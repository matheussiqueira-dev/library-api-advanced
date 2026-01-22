import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine, get_db, AsyncSessionLocal

# Fixture for the database
@pytest.fixture(scope="module")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# Tests
@pytest.mark.asyncio
async def test_create_book(client):
    response = await client.post(
        "/api/v1/books/",
        json={"title": "Test Book", "author": "Tester", "year": 2024, "isbn": "123-456"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Book"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_books(client):
    response = await client.get("/api/v1/books/")
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_read_book(client):
    # Create one first
    create_res = await client.post(
        "/api/v1/books/",
        json={"title": "Get Me", "author": "Tester", "year": 2024, "isbn": "999-999"}
    )
    book_id = create_res.json()["id"]
    
    response = await client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"

@pytest.mark.asyncio
async def test_update_book(client):
    # Create one first
    create_res = await client.post(
        "/api/v1/books/",
        json={"title": "Old Title", "author": "Tester", "year": 2024, "isbn": "888-888"}
    )
    book_id = create_res.json()["id"]
    
    response = await client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "New Title"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"

@pytest.mark.asyncio
async def test_delete_book(client):
    # Create one first
    create_res = await client.post(
        "/api/v1/books/",
        json={"title": "Delete Me", "author": "Tester", "year": 2024, "isbn": "777-777"}
    )
    book_id = create_res.json()["id"]
    
    response = await client.delete(f"/api/v1/books/{book_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_res = await client.get(f"/api/v1/books/{book_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_books_total_header(client):
    response = await client.get("/api/v1/books/")
    assert response.status_code == 200
    assert response.headers.get("X-Total-Count") is not None

@pytest.mark.asyncio
async def test_search_books(client):
    unique_title = "Search Target"
    await client.post(
        "/api/v1/books/",
        json={"title": unique_title, "author": "Finder", "year": 2022, "isbn": "555-555-555"},
    )
    response = await client.get("/api/v1/books/?q=Search")
    assert response.status_code == 200
    titles = [book["title"] for book in response.json()]
    assert unique_title in titles
