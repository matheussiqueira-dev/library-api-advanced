from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Vercel's filesystem is read-only except /tmp, which is per instance and wiped on
# cold starts. Until a managed Postgres is attached, the demo runs on this file.
EPHEMERAL_DATABASE_URL = "sqlite+aiosqlite:////tmp/library.db"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Library Studio"
    PROJECT_DESCRIPTION: str = "An async-first Library API with a modern UX."
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./library.db"
    DB_AUTO_CREATE: bool = True
    # Insert a curated set of books on startup when the catalog is empty.
    DEMO_SEED: bool = False

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

    # Set to "1" by the Vercel build and runtime.
    VERCEL: bool = False

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    @model_validator(mode="after")
    def apply_vercel_defaults(self) -> "Settings":
        # Explicit env vars always win; these only fill in what was left unset.
        if self.VERCEL:
            explicit = self.model_fields_set
            if "DATABASE_URL" not in explicit:
                self.DATABASE_URL = EPHEMERAL_DATABASE_URL
                if "DEMO_SEED" not in explicit:
                    self.DEMO_SEED = True
            if "TRUST_PROXY_HEADERS" not in explicit:
                # Vercel overwrites X-Forwarded-For with the real client IP.
                self.TRUST_PROXY_HEADERS = True
        return self

    @property
    def ephemeral_database(self) -> bool:
        return self.DATABASE_URL == EPHEMERAL_DATABASE_URL

settings = Settings()
