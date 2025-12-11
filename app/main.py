from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from contextlib import asynccontextmanager
from app.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist (for simplicity without migrations run)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to the Advanced Library API", "docs": "/docs"}
