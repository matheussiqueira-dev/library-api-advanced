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
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
