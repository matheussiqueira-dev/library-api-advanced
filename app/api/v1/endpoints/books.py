from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.isbn import is_valid_isbn, normalize_isbn
from app.core.rate_limit import lookup_limiter, rate_limited, write_limiter
from app.core.security import ensure_writes_enabled
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter()

# Public demo: every mutation goes through the kill switch and a per-IP budget.
WRITE_GUARDS = [Depends(ensure_writes_enabled), Depends(rate_limited(write_limiter))]


async def get_book_service(db: AsyncSession = Depends(get_db)) -> BookService:
    return BookService(db)


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_GUARDS,
)
async def create_book(book_in: BookCreate, service: BookService = Depends(get_book_service)):
    return await service.create_book(book_in)


@router.get("/", response_model=list[BookResponse])
async def read_books(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, min_length=1, max_length=100, description="Search in title/author"),
    author: str | None = Query(None, min_length=1, max_length=100),
    year: int | None = Query(None, ge=1000, le=2100),
    year_min: int | None = Query(None, ge=1000, le=2100),
    year_max: int | None = Query(None, ge=1000, le=2100),
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


@router.get(
    "/lookup/{isbn}",
    response_model=dict,
    dependencies=[Depends(rate_limited(lookup_limiter))],
)
async def lookup_isbn(
    isbn: str = Path(..., min_length=10, max_length=20),
    service: BookService = Depends(get_book_service),
):
    """Lookup book metadata by ISBN from external API."""
    normalized = normalize_isbn(isbn)
    if not normalized or not is_valid_isbn(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="isbn must be a valid ISBN-10 or ISBN-13",
        )
    data = await service.fetch_book_by_isbn(normalized)
    if not data:
        raise HTTPException(status_code=404, detail="ISBN not found in external registry")
    return data


@router.get("/{book_id}", response_model=BookResponse)
async def read_book(book_id: int, service: BookService = Depends(get_book_service)):
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/{book_id}", response_model=BookResponse, dependencies=WRITE_GUARDS)
async def update_book(
    book_id: int, book_in: BookUpdate, service: BookService = Depends(get_book_service)
):
    book = await service.update_book(book_id, book_in)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=WRITE_GUARDS)
async def delete_book(book_id: int, service: BookService = Depends(get_book_service)):
    success = await service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
