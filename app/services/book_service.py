import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTLCache
from app.core.config import settings
from app.core.isbn import normalize_isbn
from app.models.book import Book
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate, BookUpdate

logger = logging.getLogger(__name__)

OPENLIBRARY_BOOKS_URL = "https://openlibrary.org/api/books"
LOOKUP_TIMEOUT_SECONDS = 5.0
# Successful lookups (including "not found") are cached per instance for a day.
lookup_cache: TTLCache[dict[str, Any]] = TTLCache(ttl_seconds=86_400, max_entries=512)


class BookService:
    def __init__(self, db: AsyncSession, http_transport: httpx.AsyncBaseTransport | None = None):
        self.repo = BookRepository(db)
        self._http_transport = http_transport

    async def fetch_book_by_isbn(self, isbn: str) -> dict:
        """Fetch book metadata from OpenLibrary API."""
        normalized_isbn = normalize_isbn(isbn)
        if not normalized_isbn:
            return {}

        cached = lookup_cache.get(normalized_isbn)
        if cached is not None:
            return cached

        key = f"ISBN:{normalized_isbn}"
        try:
            async with httpx.AsyncClient(
                timeout=LOOKUP_TIMEOUT_SECONDS, transport=self._http_transport
            ) as client:
                response = await client.get(
                    OPENLIBRARY_BOOKS_URL,
                    params={"bibkeys": key, "format": "json", "jscmd": "data"},
                )
            if response.status_code != 200:
                logger.warning("OpenLibrary lookup returned HTTP %s", response.status_code)
                return {}
            data = response.json()
            result = self._parse_openlibrary(data[key]) if key in data else {}
        except (httpx.HTTPError, ValueError, TypeError, AttributeError, IndexError):
            logger.warning("OpenLibrary lookup failed for ISBN %s", normalized_isbn, exc_info=True)
            return {}

        lookup_cache.set(normalized_isbn, result)
        return result

    @staticmethod
    def _parse_openlibrary(book_data: dict[str, Any]) -> dict[str, Any]:
        publish_date = book_data.get("publish_date") or ""
        last_token = publish_date.split()[-1] if publish_date.split() else ""
        authors = book_data.get("authors") or []
        return {
            "title": book_data.get("title"),
            "author": authors[0].get("name") if authors else None,
            "year": int(last_token) if last_token.isdigit() else None,
            "description": book_data.get("notes") or book_data.get("subtitle"),
            "cover_url": (book_data.get("cover") or {}).get("large"),
            "page_count": book_data.get("number_of_pages"),
        }

    async def create_book(self, book_in: BookCreate) -> Book:
        if await self.repo.count() >= settings.DEMO_MAX_BOOKS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Catalog limit reached. Delete a book before adding another.",
            )

        payload = book_in.model_dump()

        if payload["isbn"]:
            existing = await self.repo.get_by_isbn(payload["isbn"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists"
                )

        # If some fields are missing and ISBN is present, try to auto-fill
        if payload["isbn"] and (not payload.get("description") or not payload.get("cover_url")):
            metadata = await self.fetch_book_by_isbn(payload["isbn"])
            merged = {**payload, **{k: v for k, v in metadata.items() if v and not payload.get(k)}}
            try:
                # External data goes through the same validation as user input.
                payload = BookCreate.model_validate(merged).model_dump()
            except ValidationError:
                logger.warning("Ignoring OpenLibrary metadata that failed validation")

        return await self.repo.create(obj_in=payload)

    async def get_book(self, book_id: int) -> Book | None:
        return await self.repo.get(book_id)

    async def get_books(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        author: str | None = None,
        year: int | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Book], int]:
        return await self.repo.search_books(
            skip=skip,
            limit=limit,
            q=q,
            author=author,
            year=year,
            year_min=year_min,
            year_max=year_max,
            sort=sort,
            order=order,
        )

    async def update_book(self, book_id: int, book_in: BookUpdate) -> Book | None:
        book = await self.repo.get(book_id)
        if not book:
            return None

        update_data = book_in.model_dump(exclude_unset=True)
        if update_data.get("isbn"):
            existing = await self.repo.get_by_isbn(update_data["isbn"])
            if existing and existing.id != book_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists"
                )

        return await self.repo.update(db_obj=book, obj_in=update_data)

    async def delete_book(self, book_id: int) -> bool:
        return await self.repo.delete(id=book_id)
