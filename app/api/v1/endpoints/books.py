from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter()

async def get_book_service(db: AsyncSession = Depends(get_db)) -> BookService:
    return BookService(db)

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_in: BookCreate,
    service: BookService = Depends(get_book_service)
):
    return await service.create_book(book_in)

@router.get("/", response_model=List[BookResponse])
async def read_books(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in title/author"),
    author: Optional[str] = Query(None, min_length=1, max_length=100),
    year: Optional[int] = Query(None, ge=1000, le=2100),
    year_min: Optional[int] = Query(None, ge=1000, le=2100),
    year_max: Optional[int] = Query(None, ge=1000, le=2100),
    sort: Literal["title", "author", "year", "created_at"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    service: BookService = Depends(get_book_service),
):
    if year_min is not None and year_max is not None and year_min > year_max:
        raise HTTPException(status_code=400, detail="year_min cannot be greater than year_max")
    books, total = await service.get_books(
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
    response.headers["X-Total-Count"] = str(total)
    return books

@router.get("/lookup/{isbn}", response_model=dict)
async def lookup_isbn(isbn: str, service: BookService = Depends(get_book_service)):
    """Lookup book metadata by ISBN from external API."""
    data = await service.fetch_book_by_isbn(isbn)
    if not data:
        raise HTTPException(status_code=404, detail="ISBN not found in external registry")
    return data

@router.get("/{book_id}", response_model=BookResponse)
async def read_book(book_id: int, service: BookService = Depends(get_book_service)):
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_in: BookUpdate,
    service: BookService = Depends(get_book_service)
):
    book = await service.update_book(book_id, book_in)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, service: BookService = Depends(get_book_service)):
    success = await service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
