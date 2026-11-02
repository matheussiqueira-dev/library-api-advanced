from __future__ import annotations

import httpx
import pytest

from app.core.cache import TTLCache
from app.core.database import AsyncSessionLocal
from app.models.book import Book
from app.repositories.base import BaseRepository
from app.schemas.book import BookCreate, BookUpdate
from app.services.book_service import BookService
from tests.data import KNOWN_ISBN

BOOKS = "/api/v1/books/"


def titles(response: httpx.Response) -> list[str]:
    assert response.status_code == 200
    return [book["title"] for book in response.json()]


@pytest.mark.asyncio
async def test_filters_and_sorting(client, make_book):
    for title, author, year in (
        ("Alfa", "Ana", 1990),
        ("Beta", "Bruno", 2000),
        ("Gama", "Ana", 2010),
    ):
        await client.post(BOOKS, json=make_book(title=title, author=author, year=year))

    assert titles(await client.get(BOOKS, params={"author": "bru"})) == ["Beta"]
    assert titles(await client.get(BOOKS, params={"year": 2010})) == ["Gama"]
    window = {"year_min": 1995, "year_max": 2005}
    assert titles(await client.get(BOOKS, params=window)) == ["Beta"]
    ordered = {"sort": "year", "order": "asc", "author": "ana"}
    assert titles(await client.get(BOOKS, params=ordered)) == ["Alfa", "Gama"]
    ordered["order"] = "desc"
    assert titles(await client.get(BOOKS, params=ordered)) == ["Gama", "Alfa"]


@pytest.mark.asyncio
async def test_base_repository_paginates_and_reports_missing_ids(client):
    async with AsyncSessionLocal() as session:
        repo = BaseRepository(Book, session)
        for index in range(3):
            await repo.create(obj_in={"title": f"Livro {index}", "author": "A"})

        assert [book.title for book in await repo.get_multi(skip=1, limit=1)] == ["Livro 1"]
        assert await repo.count() == 3
        assert await repo.delete(id=999) is False


def service_with(session, handler) -> BookService:
    return BookService(session, http_transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_lookup_returns_nothing_on_upstream_error(client):
    async with AsyncSessionLocal() as session:
        service = service_with(session, lambda _: httpx.Response(503))
        assert await service.fetch_book_by_isbn(KNOWN_ISBN) == {}


@pytest.mark.asyncio
async def test_lookup_survives_timeout_and_malformed_body(client):
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow", request=request)

    async with AsyncSessionLocal() as session:
        assert await service_with(session, timeout).fetch_book_by_isbn(KNOWN_ISBN) == {}
        malformed = service_with(session, lambda _: httpx.Response(200, text="<html>"))
        assert await malformed.fetch_book_by_isbn(KNOWN_ISBN) == {}


@pytest.mark.asyncio
async def test_lookup_ignores_unusable_isbn_without_calling_upstream(client):
    calls: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={})

    async with AsyncSessionLocal() as session:
        assert await service_with(session, record).fetch_book_by_isbn(" - ") == {}
    assert calls == []


@pytest.mark.asyncio
async def test_invalid_external_metadata_does_not_block_creation(client):
    key = f"ISBN:{KNOWN_ISBN}"
    payload = {key: {"title": "x", "cover": {"large": "javascript:alert(1)"}}}

    async with AsyncSessionLocal() as session:
        service = service_with(session, lambda _: httpx.Response(200, json=payload))
        book = await service.create_book(BookCreate(title="Meu", author="A", isbn=KNOWN_ISBN))

    assert book.title == "Meu"
    assert book.cover_url is None


@pytest.mark.asyncio
async def test_update_of_unknown_book_returns_none(client):
    async with AsyncSessionLocal() as session:
        assert await BookService(session).update_book(999, BookUpdate(title="Novo")) is None


def test_cache_expires_entries(monkeypatch):
    clock = {"now": 100.0}
    monkeypatch.setattr("app.core.cache.time.monotonic", lambda: clock["now"])
    cache: TTLCache[str] = TTLCache(ttl_seconds=10, max_entries=2)

    cache.set("a", "1")
    assert cache.get("a") == "1"
    clock["now"] = 110.0
    assert cache.get("a") is None


def test_cache_drops_stale_entries_first_and_then_the_oldest(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr("app.core.cache.time.monotonic", lambda: clock["now"])
    cache: TTLCache[str] = TTLCache(ttl_seconds=10, max_entries=2)

    cache.set("old", "1")
    clock["now"] = 5.0
    cache.set("recent", "2")
    clock["now"] = 11.0
    cache.set("new", "3")  # "old" expired, so "recent" survives.
    assert cache.get("recent") == "2"

    cache.set("extra", "4")  # Nothing expired: the oldest insertion goes.
    assert cache.get("recent") is None
    assert cache.get("new") == "3"
