import re
import httpx
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate, BookUpdate

class BookService:
    def __init__(self, db: AsyncSession):
        self.repo = BookRepository(db)
        self._isbn_pattern = re.compile(r"[\s-]")

    def _normalize_isbn(self, isbn: Optional[str]) -> Optional[str]:
        if not isbn:
            return None
        cleaned = self._isbn_pattern.sub("", isbn).upper()
        return cleaned or None

    async def fetch_book_by_isbn(self, isbn: str) -> dict:
        """Fetch book metadata from OpenLibrary API."""
        normalized_isbn = self._normalize_isbn(isbn)
        if not normalized_isbn:
            return {}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://openlibrary.org/api/books?bibkeys=ISBN:{normalized_isbn}&format=json&jscmd=data",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    key = f"ISBN:{normalized_isbn}"
                    if key in data:
                        book_data = data[key]
                        return {
                            "title": book_data.get("title"),
                            "author": book_data.get("authors", [{}])[0].get("name") if book_data.get("authors") else None,
                            "year": int(book_data.get("publish_date", "").split()[-1]) if book_data.get("publish_date") and book_data.get("publish_date").split()[-1].isdigit() else None,
                            "description": book_data.get("notes") or book_data.get("subtitle"),
                            "cover_url": book_data.get("cover", {}).get("large"),
                            "page_count": book_data.get("number_of_pages"),
                        }
            except Exception:
                pass
        return {}

    async def create_book(self, book_in: BookCreate) -> Book:
        payload = book_in.model_dump()
        payload["isbn"] = self._normalize_isbn(payload.get("isbn"))
        
        if payload["isbn"]:
            existing = await self.repo.get_by_isbn(payload["isbn"])
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists")
        
        # If some fields are missing and ISBN is present, try to auto-fill
        if payload["isbn"] and (not payload.get("description") or not payload.get("cover_url")):
            metadata = await self.fetch_book_by_isbn(payload["isbn"])
            for key, value in metadata.items():
                if not payload.get(key) and value:
                    payload[key] = value

        return await self.repo.create(obj_in=payload)

    async def get_book(self, book_id: int) -> Optional[Book]:
        return await self.repo.get(book_id)

    async def get_books(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        q: Optional[str] = None,
        author: Optional[str] = None,
        year: Optional[int] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> Tuple[List[Book], int]:
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

    async def update_book(self, book_id: int, book_in: BookUpdate) -> Optional[Book]:
        book = await self.repo.get(book_id)
        if not book:
            return None
        
        update_data = book_in.model_dump(exclude_unset=True)
        if "isbn" in update_data:
            update_data["isbn"] = self._normalize_isbn(update_data.get("isbn"))
            if update_data["isbn"]:
                existing = await self.repo.get_by_isbn(update_data["isbn"])
                if existing and existing.id != book_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists")
        
        return await self.repo.update(db_obj=book, obj_in=update_data)

    async def delete_book(self, book_id: int) -> bool:
        return await self.repo.delete(id=book_id)
