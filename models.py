from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class StartCollection(BaseModel):
    category: str = Field(min_length=1, max_length=200)
    gender: str = Field(min_length=1, max_length=100)
    product_type: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=100, ge=1, le=5000)
    use_cache: bool = True

class ProductOut(BaseModel):
    id: int
    product_id: Optional[str]
    brand: str
    product_name: str
    product_url: str
    mrp: Optional[float]
    selling_price: Optional[float]
    discount_percentage: Optional[float]
    rating: Optional[float]
    ratings_count: Optional[int]
    reviews_count: Optional[int]
    verified_buyers: Optional[int]
    five_star_count: Optional[int]
    four_star_count: Optional[int]
    three_star_count: Optional[int]
    two_star_count: Optional[int]
    one_star_count: Optional[int]
    seller: str
    category: str
    gender: str
    product_type: str
    collected_at: str
