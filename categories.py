import re
import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from ..config import settings

router = APIRouter(tags=["categories"])
_cache = None

def discover():
    global _cache
    if _cache is not None:
        return _cache
    try:
        r = httpx.get(settings.myntra_base_url, headers={"User-Agent": settings.user_agent}, timeout=settings.request_timeout)
        if r.status_code in {401,403,429}:
            raise RuntimeError("Myntra limited automated access.")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        links = []
        seen = set()
        for a in soup.select("a[href]"):
            href = a.get("href","")
            text = " ".join(a.stripped_strings)
            if not text or not href.startswith("http"):
                continue
            if "myntra.com" not in href:
                continue
            if len(text) > 80:
                continue
            key = (text.lower(), href.split("?")[0])
            if key not in seen:
                seen.add(key)
                links.append({"name": text, "url": href.split("?")[0]})
        # Organize only what the live navigation actually exposes.
        categories = []
        for x in links:
            n = x["name"].lower()
            if any(k in n for k in ("men", "women", "kids", "clothing", "tshirt", "shirt", "jeans", "shoes", "accessor")):
                categories.append(x)
        _cache = categories[:250]
        return _cache
    except Exception as e:
        raise HTTPException(503, detail=f"Category discovery unavailable: {e}")

@router.get("/categories")
def categories():
    return {"source": settings.myntra_base_url, "categories": discover()}

@router.get("/categories/{category}/segments")
def segments(category: str):
    # Segment discovery is performed from public navigation links matching the selected category.
    items = discover()
    cat = category.lower()
    values = []
    for x in items:
        n = x["name"].lower()
        if cat in n or any(token in n for token in cat.split()):
            if any(g in n for g in ("men", "women", "boys", "girls", "unisex")):
                values.append(x["name"])
    return {"options": sorted(set(values))}

@router.get("/categories/{category}/segments/{segment}/products")
def products(category: str, segment: str):
    items = discover()
    terms = {x for x in (category.lower().split() + segment.lower().split()) if len(x) > 2}
    values = []
    for x in items:
        n = x["name"].lower()
        if terms.intersection(n.split()):
            values.append(x["name"])
    return {"options": sorted(set(values))}
