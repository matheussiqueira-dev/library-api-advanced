from typing import List, Optional, Tuple, Any
from sqlalchemy import select, or_, func
from app.models.book import Book
from app.repositories.base import BaseRepository

class BookRepository(BaseRepository[Book]):
    def __init__(self, db):
        super().__init__(Book, db)

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        query = select(Book).where(Book.isbn == isbn)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def search_books(
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

        # Count
        count_stmt = select(func.count()).select_from(Book)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total = await self.db.scalar(count_stmt)

        # Sort
        sort_map = {
            "title": Book.title,
            "author": Book.author,
            "year": Book.year,
            "created_at": Book.created_at,
        }
        sort_column = sort_map.get(sort, Book.created_at)
        order_by = sort_column.asc() if order == "asc" else sort_column.desc()

        # Query
        stmt = select(Book)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(order_by).offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all(), int(total or 0)
