import pytest

from app.core.config import settings
from app.core.isbn import is_valid_isbn
from app.core.rate_limit import SlidingWindowRateLimiter, lookup_limiter, write_limiter

BOOKS = "/api/v1/books/"


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ui_renders_without_inline_scripts(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "<script>" not in html
    assert 'data-api-base="/api/v1"' in html
    assert "lucide@latest" not in html
    assert 'integrity="sha384-' in html


@pytest.mark.asyncio
async def test_security_headers_on_app_routes(client):
    response = await client.get("/")
    csp = response.headers["Content-Security-Policy"]
    script_src = next(d for d in csp.split("; ") if d.startswith("script-src"))
    assert "'unsafe-inline'" not in script_src
    assert "frame-ancestors 'none'" in csp
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_docs_get_their_own_policy(client):
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "https://cdn.jsdelivr.net" in response.headers["Content-Security-Policy"]


@pytest.mark.asyncio
async def test_redoc_uses_a_pinned_bundle(client):
    response = await client.get("/redoc")
    assert response.status_code == 200
    assert "redoc@2.5.4" in response.text
    assert "redoc@next" not in response.text
    assert "https://cdn.jsdelivr.net" in response.headers["Content-Security-Policy"]


@pytest.mark.asyncio
async def test_request_id_is_echoed_only_when_well_formed(client):
    ok = await client.get("/health", headers={"X-Request-Id": "abc-123"})
    assert ok.headers["X-Request-Id"] == "abc-123"
    bad = await client.get("/health", headers={"X-Request-Id": "x" * 200})
    assert bad.headers["X-Request-Id"] != "x" * 200


@pytest.mark.asyncio
async def test_writes_over_the_limit_get_429(client, make_book, monkeypatch):
    monkeypatch.setattr(write_limiter, "max_requests", 2)
    for _ in range(2):
        assert (await client.post(BOOKS, json=make_book())).status_code == 201
    blocked = await client.post(BOOKS, json=make_book())
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    # Reads stay available while writes are throttled.
    assert (await client.get(BOOKS)).status_code == 200


@pytest.mark.asyncio
async def test_invalid_writes_still_count_towards_the_limit(client, monkeypatch):
    monkeypatch.setattr(write_limiter, "max_requests", 1)
    assert (await client.post(BOOKS, json={"title": ""})).status_code == 422
    assert (await client.post(BOOKS, json={"title": ""})).status_code == 429


@pytest.mark.asyncio
async def test_lookups_over_the_limit_get_429(client, monkeypatch):
    monkeypatch.setattr(lookup_limiter, "max_requests", 1)
    assert (await client.get(f"{BOOKS}lookup/9780306406157")).status_code == 404
    assert (await client.get(f"{BOOKS}lookup/9780306406157")).status_code == 429


@pytest.mark.asyncio
async def test_oversized_body_gets_413(client, make_book):
    body = make_book(description="x" * (settings.MAX_REQUEST_BODY_BYTES + 1))
    response = await client.post(BOOKS, json=body)
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_oversized_chunked_body_gets_413(client):
    async def chunks():
        for _ in range(settings.MAX_REQUEST_BODY_BYTES // 1024 + 2):
            yield b"x" * 1024

    response = await client.post(BOOKS, content=chunks(), headers={"Content-Type": "application/json"})
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_catalog_limit_blocks_new_books(client, make_book, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MAX_BOOKS", 1)
    assert (await client.post(BOOKS, json=make_book())).status_code == 201
    assert (await client.post(BOOKS, json=make_book())).status_code == 409


@pytest.mark.asyncio
async def test_kill_switch_disables_writes(client, make_book, monkeypatch):
    book_id = (await client.post(BOOKS, json=make_book())).json()["id"]
    monkeypatch.setattr(settings, "WRITES_ENABLED", False)
    assert (await client.post(BOOKS, json=make_book())).status_code == 503
    assert (await client.put(f"{BOOKS}{book_id}", json={"title": "x"})).status_code == 503
    assert (await client.delete(f"{BOOKS}{book_id}")).status_code == 503
    assert (await client.get(f"{BOOKS}{book_id}")).status_code == 200


def test_rate_limiter_window_slides(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.core.rate_limit.time.monotonic", lambda: now[0])
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=10)
    assert limiter.hit("a") is None
    assert limiter.hit("a") is None
    assert limiter.hit("a") == pytest.approx(10)
    assert limiter.hit("b") is None  # budgets are per client
    now[0] += 10
    assert limiter.hit("a") is None


def test_rate_limiter_bounds_tracked_clients():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, max_keys=3)
    for key in "abcdef":
        limiter.hit(key)
    assert len(limiter._hits) <= 3


@pytest.mark.parametrize(
    "isbn,expected",
    [
        ("9780306406157", True),
        ("0306406152", True),
        ("020161622X", True),
        ("9780306406158", False),
        ("0306406153", False),
        ("97803064061", False),
    ],
)
def test_isbn_checksum(isbn, expected):
    assert is_valid_isbn(isbn) is expected
