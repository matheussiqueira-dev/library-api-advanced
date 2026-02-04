from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
import enum
from sqlalchemy.sql import func
from app.core.database import Base


class BookStatus(str, enum.Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    isbn = Column(String(20), unique=True, index=True, nullable=True)
    cover_url = Column(String(500), nullable=True)
    language = Column(String(50), nullable=True)
    page_count = Column(Integer, nullable=True)
    status = Column(SQLEnum(BookStatus), default=BookStatus.AVAILABLE, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
