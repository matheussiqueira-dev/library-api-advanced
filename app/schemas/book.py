from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, example="The Great Gatsby")
    author: str = Field(..., min_length=1, max_length=100, example="F. Scott Fitzgerald")
    year: Optional[int] = Field(None, ge=1000, le=2100, example=1925)
    isbn: Optional[str] = Field(None, max_length=20, example="978-0743273565")

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1000, le=2100)
    isbn: Optional[str] = Field(None, max_length=20)

class BookResponse(BookBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
