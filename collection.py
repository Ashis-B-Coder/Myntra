import asyncio, uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from ..database import SessionLocal, Collection, Product, CollectionProduct
from ..models import StartCollection
from ..scraper.collector import collect, CollectionBlocked

router = APIRouter(tags=["collection"])
jobs = {}

def missing_count(p):
    keys = ["brand","product_name","product_url","mrp","selling_price","discount_percentage","rating",
            "ratings_count","reviews_count","verified_buyers","five_star_count","four_star_count",
            "three_star_count","two_star_count","one_star_count","seller"]
    return sum(p.get(k) is None or p.get(k) == "Not Available" for k in keys)

async def run_job(job_id, payload):
    def progress_sync(stage, page, count, current):
        jobs[job_id].update({"stage": stage, "progress": count, "current": current})
    async def progress(stage, page, count, current):
        progress_sync(stage, page, count, current)
    db = SessionLocal()
    c = db.scalar(select(Collection).where(Collection.job_id == job_id))
    try:
        products, duration = await collect(payload, progress)
        c.discovered = len(products)
        c.skipped = max(0, payload["limit"] - len(products))
        c.collected = len(products)
        c.missing_fields = sum(missing_count(p) for p in products)
        for p in products:
            key = p.get("product_id") or p.get("product_url")
            existing = db.scalar(select(Product).where(Product.product_id == key)) if key and key != "Not Available" else None
            if existing is None and p.get("product_url") and p["product_url"] != "Not Available":
                existing = db.scalar(select(Product).where(Product.product_url == p["product_url"]))
            if existing is None:
                existing = Product(**p)
                db.add(existing)
                db.flush()
            if not db.scalar(select(CollectionProduct).where(CollectionProduct.collection_id == c.id, CollectionProduct.product_id == existing.id)):
                db.add(CollectionProduct(collection_id=c.id, product_id=existing.id))
        c.status = "completed"
        c.completed_at = datetime.utcnow()
        c.message = f"Collection completed in {duration}s."
        db.commit()
        jobs[job_id].update({"status":"completed","progress":c.collected,"duration":duration})
    except CollectionBlocked as e:
        c.status = "blocked"; c.message = str(e); c.errors += 1; db.commit()
        jobs[job_id].update({"status":"blocked","error":str(e)})
    except Exception as e:
        c.status = "failed"; c.message = str(e); c.errors += 1; db.commit()
        jobs[job_id].update({"status":"failed","error":str(e)})
    finally:
        db.close()

@router.post("/collection/start")
async def start(payload: StartCollection):
    db = SessionLocal()
    job_id = "COL-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4].upper()
    c = Collection(job_id=job_id, category=payload.category, gender=payload.gender,
                   product_type=payload.product_type, limit=payload.limit)
    db.add(c); db.commit()
    db.close()
    jobs[job_id] = {"status":"started","progress":0,"stage":"Queued","current":""}
    asyncio.create_task(run_job(job_id, payload.model_dump()))
    return {"job_id": job_id, "status": "started"}

@router.get("/collection/{job_id}")
def status(job_id: str):
    db = SessionLocal()
    c = db.scalar(select(Collection).where(Collection.job_id == job_id))
    if not c:
        raise HTTPException(404, "Job not found")
    live = jobs.get(job_id, {})
    result = {"job_id":job_id,"status":c.status,"discovered":c.discovered,"collected":c.collected,
              "skipped":c.skipped,"missing_fields":c.missing_fields,"duplicates_removed":c.duplicates_removed,
              "errors":c.errors,"message":c.message,"started_at":c.started_at,"completed_at":c.completed_at}
    result.update(live)
    db.close()
    return result

@router.get("/collection/{job_id}/products")
def get_products(job_id: str, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    db = SessionLocal()
    c = db.scalar(select(Collection).where(Collection.job_id == job_id))
    if not c: raise HTTPException(404, "Job not found")
    q = (select(Product).join(CollectionProduct, CollectionProduct.product_id == Product.id)
         .where(CollectionProduct.collection_id == c.id).order_by(Product.id.desc())
         .offset((page-1)*page_size).limit(page_size))
    rows = db.scalars(q).all()
    total = db.scalar(select(func.count()).select_from(CollectionProduct).where(CollectionProduct.collection_id == c.id))
    out = []
    for p in rows:
        d = {k: getattr(p,k) for k in ["id","product_id","brand","product_name","product_url","mrp","selling_price",
            "discount_percentage","rating","ratings_count","reviews_count","verified_buyers","five_star_count",
            "four_star_count","three_star_count","two_star_count","one_star_count","seller","category","gender",
            "product_type","collected_at"]}
        d["collected_at"] = p.collected_at.isoformat()
        out.append(d)
    db.close()
    return {"items":out,"total":total,"page":page,"page_size":page_size}
