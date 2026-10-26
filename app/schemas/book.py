from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.isbn import is_valid_isbn, normalize_isbn
from app.models.book import BookStatus


def _validate_isbn(value: str | None) -> str | None:
    normalized = normalize_isbn(value)
    if normalized is None:
        return None
    if not is_valid_isbn(normalized):
        raise ValueError("isbn must be a valid ISBN-10 or ISBN-13")
    return normalized


def _validate_cover_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("cover_url must be an http(s) URL")
    return value


class BookBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, json_schema_extra={"example": "The Great Gatsby"}
    )
    author: str = Field(
        ..., min_length=1, max_length=100, json_schema_extra={"example": "F. Scott Fitzgerald"}
    )
    description: str | None = Field(None, max_length=2000)
    year: int | None = Field(None, ge=1000, le=2100, json_schema_extra={"example": 1925})
    isbn: str | None = Field(None, max_length=20, json_schema_extra={"example": "978-0743273565"})
    cover_url: str | None = Field(None, max_length=500)
    language: str | None = Field(None, max_length=50)
    page_count: int | None = Field(None, ge=1)
    status: BookStatus = BookStatus.AVAILABLE


class BookCreate(BookBase):
    @field_validator("isbn")
    @classmethod
    def check_isbn(cls, value: str | None) -> str | None:
        return _validate_isbn(value)

    @field_validator("cover_url")
    @classmethod
    def check_cover_url(cls, value: str | None) -> str | None:
        return _validate_cover_url(value)


class BookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    author: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    year: int | None = Field(None, ge=1000, le=2100)
    isbn: str | None = Field(None, max_length=20)
    cover_url: str | None = Field(None, max_length=500)
    language: str | None = Field(None, max_length=50)
    page_count: int | None = Field(None, ge=1)
    status: BookStatus | None = None

    @field_validator("title", "author", "status")
    @classmethod
    def reject_explicit_null(cls, value):
        # Omitting a field keeps it unchanged; sending null for a NOT NULL column is invalid.
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("isbn")
    @classmethod
    def check_isbn(cls, value: str | None) -> str | None:
        return _validate_isbn(value)

    @field_validator("cover_url")
    @classmethod
    def check_cover_url(cls, value: str | None) -> str | None:
        return _validate_cover_url(value)


class BookResponse(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
