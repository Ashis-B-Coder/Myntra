import asyncio, re, time
from datetime import datetime
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup
from .parser import parse_listing
from .validator import validate_product
from .rate_limiter import RateLimiter
from ..config import settings

class CollectionBlocked(Exception):
    pass

def listing_url(category, gender, product_type, page=1):
    # Public Myntra search URL. The query is intentionally user-selected.
    q = " ".join(x for x in (gender, product_type) if x)
    return f"{settings.myntra_base_url}/search/{quote_plus(q)}?p={page}"

async def fetch(client, url, limiter):
    await limiter.wait()
    last = None
    for attempt in range(settings.max_retries + 1):
        try:
            r = await client.get(url, timeout=settings.request_timeout, follow_redirects=True)
            if r.status_code in {401, 403, 429}:
                raise CollectionBlocked(f"Myntra returned HTTP {r.status_code}. Automated collection is unavailable.")
            r.raise_for_status()
            return r.text
        except CollectionBlocked:
            raise
        except Exception as e:
            last = e
            if attempt < settings.max_retries:
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError(str(last))

async def collect(selection, progress):
    limiter = RateLimiter(settings.request_delay)
    headers = {"User-Agent": settings.user_agent, "Accept-Language": "en-IN,en;q=0.9"}
    products, seen = [], set()
    pages_without_new = 0
    started = time.monotonic()

    async with httpx.AsyncClient(headers=headers) as client:
        page = 1
        while len(products) < selection["limit"] and page <= 100:
            url = listing_url(selection["category"], selection["gender"], selection["product_type"], page)
            await progress("Fetching", page, len(products), url)
            html = await fetch(client, url, limiter)
            parsed = parse_listing(html, settings.myntra_base_url)
            new_count = 0
            for raw in parsed:
                raw.update({
                    "category": selection["category"],
                    "gender": selection["gender"],
                    "product_type": selection["product_type"],
                    "collected_at": datetime.utcnow()
                })
                p = validate_product(raw)
                key = p.get("product_id") or p.get("product_url")
                if not key:
                    key = f"{p.get('brand')}|{p.get('product_name')}".lower()
                if key in seen:
                    continue
                seen.add(key)
                products.append(p)
                new_count += 1
                if len(products) >= selection["limit"]:
                    break
            pages_without_new = pages_without_new + 1 if new_count == 0 else 0
            if pages_without_new >= 2:
                break
            page += 1
            await progress("Parsing", page, len(products), url)

    return products, round(time.monotonic() - started, 2)
