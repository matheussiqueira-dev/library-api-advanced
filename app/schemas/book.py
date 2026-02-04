from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models.book import BookStatus

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, json_schema_extra={"example": "The Great Gatsby"})
    author: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "F. Scott Fitzgerald"})
    description: Optional[str] = Field(None, max_length=2000)
    year: Optional[int] = Field(None, ge=1000, le=2100, json_schema_extra={"example": 1925})
    isbn: Optional[str] = Field(None, max_length=20, json_schema_extra={"example": "978-0743273565"})
    cover_url: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field(None, max_length=50)
    page_count: Optional[int] = Field(None, ge=1)
    status: BookStatus = BookStatus.AVAILABLE

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    year: Optional[int] = Field(None, ge=1000, le=2100)
    isbn: Optional[str] = Field(None, max_length=20)
    cover_url: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field(None, max_length=50)
    page_count: Optional[int] = Field(None, ge=1)
    status: Optional[BookStatus] = None

class BookResponse(BookBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
