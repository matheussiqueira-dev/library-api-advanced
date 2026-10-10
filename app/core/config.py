from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Library API Advanced"
    PROJECT_DESCRIPTION: str = "A senior-grade, async-first Library API with a modern UX."
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./library.db"
    DB_AUTO_CREATE: bool = True

    # Observability
    LOG_LEVEL: str = "INFO"

    # Public write protection
    WRITES_ENABLED: bool = True
    DEMO_MAX_BOOKS: int = Field(500, ge=1)
    MAX_REQUEST_BODY_BYTES: int = Field(16_384, ge=1_024)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(60, ge=1)
    RATE_LIMIT_WRITES_PER_WINDOW: int = Field(20, ge=1)
    RATE_LIMIT_LOOKUPS_PER_WINDOW: int = Field(10, ge=1)
    # Only enable behind a proxy that overwrites X-Forwarded-For (e.g. Vercel).
    TRUST_PROXY_HEADERS: bool = False

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
