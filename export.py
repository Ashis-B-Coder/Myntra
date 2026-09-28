from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from ..database import SessionLocal, Collection, Product, CollectionProduct
from ..exporters.excel import build_excel
from ..exporters.pdf import build_pdf

router=APIRouter(tags=["export"])
EXPORT_DIR=Path("exports"); EXPORT_DIR.mkdir(exist_ok=True)

def get_data(job_id):
    db=SessionLocal()
    c=db.scalar(select(Collection).where(Collection.job_id==job_id))
    if not c:
        db.close(); raise HTTPException(404,"Job not found")
    products=db.scalars(select(Product).join(CollectionProduct, CollectionProduct.product_id==Product.id)
        .where(CollectionProduct.collection_id==c.id).order_by(Product.id)).all()
    db.close()
    return c,products

@router.post("/collection/{job_id}/export/excel")
def excel(job_id):
    c,p=get_data(job_id)
    path=EXPORT_DIR/f"{job_id}.xlsx"; build_excel(p,c,path)
    return {"status":"ready","download":f"/api/collection/{job_id}/export/excel/download"}

@router.get("/collection/{job_id}/export/excel/download")
def excel_download(job_id):
    path=EXPORT_DIR/f"{job_id}.xlsx"
    if not path.exists(): raise HTTPException(404,"Generate the Excel file first")
    return FileResponse(path,filename=path.name,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.post("/collection/{job_id}/export/pdf")
def pdf(job_id):
    c,p=get_data(job_id)
    path=EXPORT_DIR/f"{job_id}.pdf"; build_pdf(p,c,path)
    return {"status":"ready","download":f"/api/collection/{job_id}/export/pdf/download"}

@router.get("/collection/{job_id}/export/pdf/download")
def pdf_download(job_id):
    path=EXPORT_DIR/f"{job_id}.pdf"
    if not path.exists(): raise HTTPException(404,"Generate the PDF first")
    return FileResponse(path,filename=path.name,media_type="application/pdf")
