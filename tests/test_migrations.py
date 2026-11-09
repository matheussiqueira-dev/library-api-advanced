"""The Alembic history must build exactly the schema declared by the models."""

from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import settings
from app.core.database import Base

ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    # No ini file: env.py skips fileConfig, so the suite's logging setup stays untouched.
    config = Config()
    config.set_main_option("script_location", str(ROOT / "alembic"))
    return config


@pytest.fixture
def migration_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_file = tmp_path / "migrations.db"
    # env.py reads the URL from settings, so point it at a throwaway file.
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_file.as_posix()}")
    return db_file


def test_upgrade_head_matches_the_models(migration_db: Path) -> None:
    command.upgrade(_alembic_config(), "head")

    engine = create_engine(f"sqlite:///{migration_db.as_posix()}")
    try:
        with engine.connect() as connection:
            diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
            tables = inspect(connection).get_table_names()
    finally:
        engine.dispose()

    assert diff == []
    assert set(tables) == {"alembic_version", "books"}


def test_downgrade_base_removes_the_schema(migration_db: Path) -> None:
    config = _alembic_config()
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(f"sqlite:///{migration_db.as_posix()}")
    try:
        with engine.connect() as connection:
            tables = inspect(connection).get_table_names()
    finally:
        engine.dispose()

    assert tables == ["alembic_version"]
