import pytest

from app.core.config import EPHEMERAL_DATABASE_URL, Settings, settings
from app.core.database import AsyncSessionLocal
from app.core.rate_limit import write_limiter
from app.services.demo_seed import DEMO_BOOKS, seed_demo_books

BOOKS = "/api/v1/books/"


@pytest.fixture
def vercel_env(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    for name in ("DATABASE_URL", "DEMO_SEED", "TRUST_PROXY_HEADERS"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_vercel_defaults_to_ephemeral_seeded_database(vercel_env):
    configured = Settings(_env_file=None)
    assert configured.DATABASE_URL == EPHEMERAL_DATABASE_URL
    assert configured.ephemeral_database
    assert configured.DEMO_SEED is True
    assert configured.TRUST_PROXY_HEADERS is True


def test_explicit_env_vars_override_vercel_defaults(vercel_env):
    vercel_env.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db.example/library")
    vercel_env.setenv("TRUST_PROXY_HEADERS", "false")
    configured = Settings(_env_file=None)
    assert configured.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert not configured.ephemeral_database
    assert configured.DEMO_SEED is False
    assert configured.TRUST_PROXY_HEADERS is False


def test_local_defaults_are_unchanged(monkeypatch):
    for name in ("VERCEL", "DATABASE_URL", "DEMO_SEED", "TRUST_PROXY_HEADERS"):
        monkeypatch.delenv(name, raising=False)
    configured = Settings(_env_file=None)
    assert configured.DATABASE_URL == "sqlite+aiosqlite:///./library.db"
    assert configured.DEMO_SEED is False
    assert configured.TRUST_PROXY_HEADERS is False


@pytest.mark.asyncio
async def test_seed_fills_an_empty_catalog_once(client):
    async with AsyncSessionLocal() as session:
        assert await seed_demo_books(session) == len(DEMO_BOOKS)
        assert await seed_demo_books(session) == 0

    response = await client.get(BOOKS, params={"limit": 100})
    books = response.json()
    assert len(books) == len(DEMO_BOOKS)
    with_isbn = [b for b in books if b["isbn"]]
    assert with_isbn and all(b["cover_url"].startswith("https://covers.openlibrary.org/") for b in with_isbn)


@pytest.mark.asyncio
async def test_seed_skips_a_catalog_that_has_books(client, make_book):
    await client.post(BOOKS, json=make_book())
    async with AsyncSessionLocal() as session:
        assert await seed_demo_books(session) == 0


@pytest.mark.asyncio
async def test_ui_labels_ephemeral_demo_data(client, monkeypatch):
    assert "demo-notice" not in (await client.get("/")).text
    monkeypatch.setattr(settings, "DATABASE_URL", EPHEMERAL_DATABASE_URL)
    html = (await client.get("/")).text
    assert "demo-notice" in html
    assert "Demonstração" in html


@pytest.mark.asyncio
async def test_forwarded_ip_gets_its_own_budget_behind_a_trusted_proxy(client, make_book, monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    monkeypatch.setattr(write_limiter, "max_requests", 1)
    alice = {"X-Forwarded-For": "203.0.113.10"}
    bob = {"X-Forwarded-For": "203.0.113.20, 10.0.0.1"}
    assert (await client.post(BOOKS, json=make_book(), headers=alice)).status_code == 201
    assert (await client.post(BOOKS, json=make_book(), headers=alice)).status_code == 429
    assert (await client.post(BOOKS, json=make_book(), headers=bob)).status_code == 201
