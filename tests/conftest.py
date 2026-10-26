import atexit
import os
import shutil
import tempfile
from pathlib import Path

# Point the app at a throwaway database before anything imports app.core.database,
# so tests never touch ./library.db or a developer's .env database.
_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="library-api-tests-"))
atexit.register(shutil.rmtree, _TEST_DB_DIR, ignore_errors=True)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TEST_DB_DIR / 'test.db').as_posix()}"
os.environ["DB_AUTO_CREATE"] = "false"

from collections.abc import AsyncIterator, Callable  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi import Depends  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.api.v1.endpoints.books import get_book_service  # noqa: E402
from app.core.database import Base, engine, get_db  # noqa: E402
from app.core.rate_limit import lookup_limiter, write_limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.services.book_service import BookService, lookup_cache  # noqa: E402
from tests.data import OPENLIBRARY_FIXTURE  # noqa: E402


class FakeOpenLibrary:
    """Stands in for openlibrary.org so tests never reach the network."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        key = request.url.params.get("bibkeys", "")
        payload = {key: OPENLIBRARY_FIXTURE[key]} if key in OPENLIBRARY_FIXTURE else {}
        return httpx.Response(200, json=payload)


@pytest.fixture
def openlibrary() -> FakeOpenLibrary:
    return FakeOpenLibrary()


@pytest_asyncio.fixture
async def client(openlibrary: FakeOpenLibrary) -> AsyncIterator[AsyncClient]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    write_limiter.reset()
    lookup_limiter.reset()
    lookup_cache.clear()

    transport = httpx.MockTransport(openlibrary.handler)

    async def service_with_fake_openlibrary(db: AsyncSession = Depends(get_db)) -> BookService:
        return BookService(db, http_transport=transport)

    app.dependency_overrides[get_book_service] = service_with_fake_openlibrary
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        # Each test runs on its own event loop; don't reuse pooled connections across loops.
        await engine.dispose()


@pytest.fixture
def make_book() -> Callable[..., dict]:
    def _make(**overrides: object) -> dict:
        book = {"title": "Test Book", "author": "Tester", "year": 2024}
        book.update(overrides)
        return book

    return _make
