from urllib.parse import urlparse

NOT_AVAILABLE = "Not Available"

def clean_text(value):
    if value is None:
        return NOT_AVAILABLE
    value = " ".join(str(value).split()).strip()
    return value or NOT_AVAILABLE

def valid_url(value):
    if not value or value == NOT_AVAILABLE:
        return False
    p = urlparse(value)
    return p.scheme in {"http", "https"} and bool(p.netloc)

def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def validate_product(p):
    p["brand"] = clean_text(p.get("brand"))
    p["product_name"] = clean_text(p.get("product_name"))
    p["seller"] = clean_text(p.get("seller"))
    p["product_url"] = p.get("product_url") if valid_url(p.get("product_url")) else NOT_AVAILABLE
    for k in ("mrp", "selling_price", "discount_percentage", "rating"):
        p[k] = num(p.get(k))
    for k in ("ratings_count", "reviews_count", "verified_buyers", "five_star_count",
              "four_star_count", "three_star_count", "two_star_count", "one_star_count"):
        p[k] = integer(p.get(k))
    if p["rating"] is not None and not 0 <= p["rating"] <= 5:
        p["rating"] = None
    if p["discount_percentage"] is not None and not 0 <= p["discount_percentage"] <= 100:
        p["discount_percentage"] = None
    return p
