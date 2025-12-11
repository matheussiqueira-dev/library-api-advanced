from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter()

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book_in: BookCreate, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    return await service.create_book(book_in)

@router.get("/", response_model=List[BookResponse])
async def read_books(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    return await service.get_books(skip=skip, limit=limit)

@router.get("/{book_id}", response_model=BookResponse)
async def read_book(book_id: int, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, book_in: BookUpdate, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    book = await service.update_book(book_id, book_in)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    success = await service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
