"""
Pytest configuration and shared fixtures.
"""
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.database import Base


@pytest.fixture
def temp_db() -> Generator[Session, None, None]:
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        Path(db_path).unlink()


@pytest.fixture
def temp_cache_db() -> Generator[str, None, None]:
    """Create a temporary cache database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        yield db_path
    finally:
        if Path(db_path).exists():
            Path(db_path).unlink()
