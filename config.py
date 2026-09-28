import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class Settings:
    myntra_base_url: str = os.getenv("MYNTRA_BASE_URL", "https://www.myntra.com")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'data' / 'myntra.db').as_posix()}")
    request_delay: float = float(os.getenv("REQUEST_DELAY", "1.2"))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "20"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "2"))
    max_concurrency: int = int(os.getenv("MAX_CONCURRENCY", "2"))
    user_agent: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (compatible; MyntraDataCollector/1.0; +responsible-public-data-collector)",
    )
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    environment: str = os.getenv("ENVIRONMENT", "production")

settings = Settings()
