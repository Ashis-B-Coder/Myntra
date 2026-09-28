from pathlib import Path
from sqlalchemy import create_engine, String, Float, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship
from datetime import datetime
from .config import settings

Path("data").mkdir(exist_ok=True)
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
elif db_url.startswith("postgresql://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]

engine_kwargs = {"pool_pre_ping": True}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class Collection(Base):
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(200))
    gender: Mapped[str] = mapped_column(String(100))
    product_type: Mapped[str] = mapped_column(String(200))
    limit: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="started")
    discovered: Mapped[int] = mapped_column(Integer, default=0)
    collected: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    missing_fields: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_removed: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
    brand: Mapped[str] = mapped_column(String(500), default="Not Available")
    product_name: Mapped[str] = mapped_column(String(1000), default="Not Available")
    product_url: Mapped[str] = mapped_column(Text, default="Not Available")
    mrp: Mapped[float | None] = mapped_column(Float, nullable=True)
    selling_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    discount_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    ratings_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified_buyers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    five_star_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    four_star_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    three_star_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    two_star_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    one_star_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seller: Mapped[str] = mapped_column(String(500), default="Not Available")
    category: Mapped[str] = mapped_column(String(200), default="Not Available")
    gender: Mapped[str] = mapped_column(String(100), default="Not Available")
    product_type: Mapped[str] = mapped_column(String(200), default="Not Available")
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CollectionProduct(Base):
    __tablename__ = "collection_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)

Index("ix_collection_product_unique", CollectionProduct.collection_id, CollectionProduct.product_id, unique=True)

def init_db():
    Base.metadata.create_all(engine)
