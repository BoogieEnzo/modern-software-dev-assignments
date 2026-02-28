"""Test configuration and fixtures."""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set papers directory for tests
TEST_PAPERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "papers")


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database."""
    # Create temp database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    DATABASE_URL = f"sqlite:///{db_file.name}"

    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Import and create tables
    from app.models import Base

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        os.unlink(db_file.name)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with overridden database."""
    from app.database import get_db
    from app.main import app

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
