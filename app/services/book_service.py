from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate

class BookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_book(self, book_in: BookCreate) -> Book:
        new_book = Book(**book_in.model_dump())
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

    async def get_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        result = await self.db.execute(select(Book).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_book(self, book_id: int, book_in: BookUpdate) -> Optional[Book]:
        book = await self.get_book(book_id)
        if not book:
            return None
        
        update_data = book_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)
            
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def delete_book(self, book_id: int) -> bool:
        book = await self.get_book(book_id)
        if not book:
            return False
        
        await self.db.delete(book)
        await self.db.commit()
        return True
