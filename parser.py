import json, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .validator import clean_text

PRICE_RE = re.compile(r"(?:₹|Rs\.?\s*)([\d,]+(?:\.\d+)?)")
RATING_RE = re.compile(r"\b([0-5](?:\.[0-9])?)\b")

def money(text):
    if not text:
        return None
    m = PRICE_RE.search(text.replace(",", ""))
    return float(m.group(1)) if m else None

def rating_count(text):
    if not text:
        return None
    text = text.lower().replace(",", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*([km]?)", text)
    if not m:
        return None
    n = float(m.group(1))
    if m.group(2) == "k": n *= 1000
    if m.group(2) == "m": n *= 1000000
    return int(n)

def product_links(soup, base_url):
    seen = set()
    for a in soup.select("a[href]"):
        href = urljoin(base_url, a.get("href"))
        if "myntra.com/" in href and re.search(r"/\d+/", href):
            href = href.split("?")[0]
            if href not in seen:
                seen.add(href)
                yield href

def extract_json_product_objects(soup):
    out = []
    for script in soup.find_all("script"):
        txt = script.string or script.get_text()
        if not txt or len(txt) < 20:
            continue
        if "pdpData" not in txt and "productName" not in txt and "searchResult" not in txt:
            continue
        try:
            obj = json.loads(txt)
            out.append(obj)
        except Exception:
            continue
    return out

def parse_listing(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    products = []
    # Prefer JSON-LD where available.
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.string or node.get_text())
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for x in items:
            if isinstance(x, dict) and x.get("@type") in {"Product", "ItemList"}:
                if x.get("@type") == "Product":
                    products.append({
                        "brand": (x.get("brand") or {}).get("name") if isinstance(x.get("brand"), dict) else x.get("brand"),
                        "product_name": x.get("name"),
                        "product_url": x.get("url"),
                        "mrp": ((x.get("offers") or {}).get("price")) if isinstance(x.get("offers"), dict) else None,
                        "selling_price": ((x.get("offers") or {}).get("price")) if isinstance(x.get("offers"), dict) else None,
                        "rating": ((x.get("aggregateRating") or {}).get("ratingValue")) if isinstance(x.get("aggregateRating"), dict) else None,
                        "ratings_count": ((x.get("aggregateRating") or {}).get("ratingCount")) if isinstance(x.get("aggregateRating"), dict) else None,
                    })
    # Rendered cards: selector-agnostic text extraction. Missing fields remain None.
    for a in soup.select("a[href]"):
        href = urljoin(base_url, a.get("href", ""))
        if "myntra.com/" not in href or not re.search(r"/\d+/", href):
            continue
        text = " ".join(a.stripped_strings)
        if len(text) < 8:
            continue
        brand = None
        title = None
        parts = list(a.stripped_strings)
        if len(parts) >= 2:
            brand, title = parts[0], parts[1]
        products.append({
            "brand": brand,
            "product_name": title,
            "product_url": href.split("?")[0],
            "mrp": None, "selling_price": money(text),
            "discount_percentage": None, "rating": None, "ratings_count": None,
            "reviews_count": None, "verified_buyers": None,
            "five_star_count": None, "four_star_count": None, "three_star_count": None,
            "two_star_count": None, "one_star_count": None, "seller": None
        })
    # Deduplicate URLs while preserving order.
    dedup = {}
    for p in products:
        u = p.get("product_url")
        if u and u != "Not Available":
            dedup.setdefault(u, p)
    return list(dedup.values())
