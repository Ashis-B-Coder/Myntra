from pathlib import Path
from dotenv import load_dotenv

# Load .env before importing modules that read environment configuration.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .api.categories import router as categories_router
from .api.collection import router as collection_router
from .api.export import router as export_router

app = FastAPI(
    title="Myntra Data Collector & Report Builder",
    version="1.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

Path("data").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)
init_db()

app.include_router(categories_router, prefix="/api")
app.include_router(collection_router, prefix="/api")
app.include_router(export_router, prefix="/api")

frontend = Path(__file__).resolve().parent.parent / "frontend"
if frontend.exists():
    app.mount("/static", StaticFiles(directory=frontend), name="static")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(frontend / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "myntra-data-collector", "environment": settings.environment}
