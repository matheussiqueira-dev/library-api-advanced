"""create books table

Revision ID: 0001
Revises:
Create Date: 2026-11-09

Initial schema, generated from app.models.book.Book with `alembic revision --autogenerate`
against an empty database. tests/test_migrations.py checks that `upgrade head` matches the
models, so a model change without a new revision fails the suite.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BOOK_STATUS = sa.Enum("AVAILABLE", "BORROWED", "RESERVED", "MAINTENANCE", name="bookstatus")


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("isbn", sa.String(length=20), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", BOOK_STATUS, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_books_author"), "books", ["author"], unique=False)
    op.create_index(op.f("ix_books_id"), "books", ["id"], unique=False)
    op.create_index(op.f("ix_books_isbn"), "books", ["isbn"], unique=True)
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_index(op.f("ix_books_isbn"), table_name="books")
    op.drop_index(op.f("ix_books_id"), table_name="books")
    op.drop_index(op.f("ix_books_author"), table_name="books")
    op.drop_table("books")
    # PostgreSQL keeps the enum as a separate type; other dialects ignore this.
    BOOK_STATUS.drop(op.get_bind(), checkfirst=True)
