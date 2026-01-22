import re
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate

class BookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._isbn_pattern = re.compile(r"[\s-]")

    def _normalize_isbn(self, isbn: Optional[str]) -> Optional[str]:
        if not isbn:
            return None
        cleaned = self._isbn_pattern.sub("", isbn).upper()
        return cleaned or None

    async def _isbn_exists(self, isbn: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(Book.id).where(Book.isbn == isbn)
        if exclude_id is not None:
            stmt = stmt.where(Book.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_book(self, book_in: BookCreate) -> Book:
        payload = book_in.model_dump()
        payload["isbn"] = self._normalize_isbn(payload.get("isbn"))
        if payload["isbn"] and await self._isbn_exists(payload["isbn"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists")
        new_book = Book(**payload)
        self.db.add(new_book)
        try:
            await self.db.commit()
            await self.db.refresh(new_book)
            return new_book
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists")

    async def get_book(self, book_id: int) -> Optional[Book]:
        result = await self.db.execute(select(Book).where(Book.id == book_id))
        return result.scalars().first()

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
        conditions = []
        if q:
            search = f"%{q.strip()}%"
            conditions.append(or_(Book.title.ilike(search), Book.author.ilike(search)))
        if author:
            conditions.append(Book.author.ilike(f"%{author.strip()}%"))
        if year is not None:
            conditions.append(Book.year == year)
        if year_min is not None:
            conditions.append(Book.year >= year_min)
        if year_max is not None:
            conditions.append(Book.year <= year_max)

        count_stmt = select(func.count()).select_from(Book)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total = await self.db.scalar(count_stmt)

        sort_map = {
            "title": Book.title,
            "author": Book.author,
            "year": Book.year,
            "created_at": Book.created_at,
        }
        sort_column = sort_map.get(sort, Book.created_at)
        order_by = sort_column.asc() if order == "asc" else sort_column.desc()

        stmt = select(Book)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(order_by).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all(), int(total or 0)

    async def update_book(self, book_id: int, book_in: BookUpdate) -> Optional[Book]:
        book = await self.get_book(book_id)
        if not book:
            return None
        
        update_data = book_in.model_dump(exclude_unset=True)
        if "isbn" in update_data:
            update_data["isbn"] = self._normalize_isbn(update_data.get("isbn"))
            if update_data["isbn"] and await self._isbn_exists(update_data["isbn"], exclude_id=book_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists")
        for field, value in update_data.items():
            setattr(book, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(book)
            return book
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists")

    async def delete_book(self, book_id: int) -> bool:
        book = await self.get_book(book_id)
        if not book:
            return False
        
        await self.db.delete(book)
        await self.db.commit()
        return True
