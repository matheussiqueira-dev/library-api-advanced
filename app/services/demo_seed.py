from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookStatus
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate

_COVER_URL = "https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false"

AVAILABLE, BORROWED, RESERVED, MAINTENANCE = (
    BookStatus.AVAILABLE,
    BookStatus.BORROWED,
    BookStatus.RESERVED,
    BookStatus.MAINTENANCE,
)

# Real books with their published ISBNs, shown in the UI under a "demo data" notice.
# (title, author, year, isbn, language, status)
DEMO_BOOKS: List[Tuple[str, str, int, Optional[str], str, BookStatus]] = [
    ("Clean Code", "Robert C. Martin", 2008, "9780132350884", "en", AVAILABLE),
    ("The Pragmatic Programmer", "Andrew Hunt e David Thomas", 1999, "9780201616224", "en", BORROWED),
    ("Refactoring", "Martin Fowler", 1999, "0201485672", "en", AVAILABLE),
    (
        "Design Patterns",
        "Erich Gamma, Richard Helm, Ralph Johnson e John Vlissides",
        1994,
        "0201633612",
        "en",
        RESERVED,
    ),
    ("Domain-Driven Design", "Eric Evans", 2003, "0321125215", "en", AVAILABLE),
    ("The Mythical Man-Month", "Frederick P. Brooks Jr.", 1995, "0201835959", "en", AVAILABLE),
    ("Code Complete", "Steve McConnell", 2004, "0735619670", "en", MAINTENANCE),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", 2017, "9781449373320", "en", AVAILABLE),
    ("Clean Architecture", "Robert C. Martin", 2017, "9780134494166", "en", BORROWED),
    (
        "Introduction to Algorithms",
        "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest e Clifford Stein",
        2009,
        "9780262033848",
        "en",
        AVAILABLE,
    ),
    ("Dom Casmurro", "Machado de Assis", 1899, None, "pt-BR", AVAILABLE),
    ("Memórias Póstumas de Brás Cubas", "Machado de Assis", 1881, None, "pt-BR", AVAILABLE),
    ("O Cortiço", "Aluísio Azevedo", 1890, None, "pt-BR", RESERVED),
    ("Vidas Secas", "Graciliano Ramos", 1938, None, "pt-BR", AVAILABLE),
]


async def seed_demo_books(db: AsyncSession) -> int:
    """Insert DEMO_BOOKS when the catalog is empty. Returns how many were added."""
    if await BookRepository(db).count() > 0:
        return 0
    for title, author, year, isbn, language, status in DEMO_BOOKS:
        book = BookCreate.model_validate(
            {
                "title": title,
                "author": author,
                "year": year,
                "isbn": isbn,
                "language": language,
                "status": status,
                "cover_url": _COVER_URL.format(isbn=isbn) if isbn else None,
            }
        )
        db.add(Book(**book.model_dump()))
    await db.commit()
    return len(DEMO_BOOKS)
