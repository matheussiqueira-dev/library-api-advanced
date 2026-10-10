import pytest

from app.repositories.book_repository import BookRepository
from tests.data import KNOWN_ISBN

BOOKS = "/api/v1/books/"


@pytest.mark.asyncio
async def test_create_book(client, make_book):
    response = await client.post(BOOKS, json=make_book(isbn="978-0-306-40615-7"))
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["isbn"] == "9780306406157"
    assert "id" in data


@pytest.mark.asyncio
async def test_read_books(client, make_book):
    await client.post(BOOKS, json=make_book())
    response = await client.get(BOOKS)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.headers.get("X-Total-Count") == "1"


@pytest.mark.asyncio
async def test_read_book(client, make_book):
    create_res = await client.post(BOOKS, json=make_book(title="Get Me"))
    book_id = create_res.json()["id"]

    response = await client.get(f"{BOOKS}{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_update_book(client, make_book):
    create_res = await client.post(BOOKS, json=make_book(title="Old Title"))
    book_id = create_res.json()["id"]

    response = await client.put(f"{BOOKS}{book_id}", json={"title": "New Title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_book(client, make_book):
    create_res = await client.post(BOOKS, json=make_book(title="Delete Me"))
    book_id = create_res.json()["id"]

    response = await client.delete(f"{BOOKS}{book_id}")
    assert response.status_code == 204

    get_res = await client.get(f"{BOOKS}{book_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_search_books(client, make_book):
    await client.post(BOOKS, json=make_book(title="Search Target", author="Finder"))
    await client.post(BOOKS, json=make_book(title="Other", author="Someone"))
    response = await client.get(BOOKS, params={"q": "Search"})
    assert response.status_code == 200
    assert [book["title"] for book in response.json()] == ["Search Target"]


@pytest.mark.asyncio
async def test_year_range_must_be_ordered(client):
    response = await client.get(BOOKS, params={"year_min": 2000, "year_max": 1990})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_html_in_title_is_stored_verbatim(client, make_book):
    # The UI renders with textContent; the API must return the raw string untouched.
    payload = "<img src=x onerror=alert(1)>"
    create_res = await client.post(BOOKS, json=make_book(title=payload, author=payload))
    assert create_res.status_code == 201
    book = (await client.get(f"{BOOKS}{create_res.json()['id']}")).json()
    assert book["title"] == payload
    assert book["author"] == payload


@pytest.mark.asyncio
async def test_duplicate_isbn_returns_conflict(client, make_book):
    first = await client.post(BOOKS, json=make_book(isbn="0306406152"))
    assert first.status_code == 201
    duplicate = await client.post(BOOKS, json=make_book(isbn="0-306-40615-2"))
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_unique_constraint_race_returns_conflict(client, make_book, monkeypatch):
    # Simulate two concurrent creates: the pre-check misses the row, the DB constraint catches it.
    await client.post(BOOKS, json=make_book(isbn="9780306406157"))

    async def no_existing_book(self, isbn):
        return None

    monkeypatch.setattr(BookRepository, "get_by_isbn", no_existing_book)
    response = await client.post(BOOKS, json=make_book(isbn="9780306406157"))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_to_existing_isbn_returns_conflict(client, make_book):
    await client.post(BOOKS, json=make_book(isbn="020161622X"))
    other = await client.post(BOOKS, json=make_book(isbn="9780743273565"))
    response = await client.put(f"{BOOKS}{other.json()['id']}", json={"isbn": "020161622x"})
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["title", "author", "status"])
async def test_update_rejects_null_for_required_fields(client, make_book, field):
    book_id = (await client.post(BOOKS, json=make_book())).json()["id"]
    response = await client.put(f"{BOOKS}{book_id}", json={field: None})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("isbn", ["123-456", "9780306406158", "030640615X"])
async def test_create_rejects_invalid_isbn(client, make_book, isbn):
    response = await client.post(BOOKS, json=make_book(isbn=isbn))
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,hi", "//evil.example/x.png"])
async def test_create_rejects_non_http_cover_url(client, make_book, url):
    response = await client.post(BOOKS, json=make_book(cover_url=url))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_empty_optional_strings_from_form_are_accepted(client, make_book):
    response = await client.post(BOOKS, json=make_book(isbn="", cover_url=""))
    assert response.status_code == 201
    assert response.json()["isbn"] is None


@pytest.mark.asyncio
async def test_create_autofills_metadata_from_lookup(client, make_book, openlibrary):
    response = await client.post(BOOKS, json=make_book(isbn=KNOWN_ISBN))
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "A Handbook of Agile Software Craftsmanship"
    assert data["cover_url"].startswith("https://covers.openlibrary.org/")
    assert len(openlibrary.requests) == 1


@pytest.mark.asyncio
async def test_lookup_returns_metadata_and_is_cached(client, openlibrary):
    first = await client.get(f"{BOOKS}lookup/978-0-13-235088-4")
    second = await client.get(f"{BOOKS}lookup/{KNOWN_ISBN}")
    assert first.status_code == second.status_code == 200
    assert first.json()["title"] == "Clean Code"
    assert first.json()["year"] == 2008
    assert len(openlibrary.requests) == 1


@pytest.mark.asyncio
async def test_lookup_unknown_isbn_returns_404(client):
    response = await client.get(f"{BOOKS}lookup/9780306406157")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("isbn", ["9780306406158", "abcdefghij", "12345"])
async def test_lookup_rejects_invalid_isbn(client, openlibrary, isbn):
    response = await client.get(f"{BOOKS}lookup/{isbn}")
    assert response.status_code == 422
    assert openlibrary.requests == []
