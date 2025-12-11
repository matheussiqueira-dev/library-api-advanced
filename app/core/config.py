from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Library API Advanced"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./library.db"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
