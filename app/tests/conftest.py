import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use SQLite in-memory for tests — no MySQL needed
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")

import db as db_module
from db import Base, get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Patch engine so check_db_connection uses test engine
    db_module.engine = test_engine
    Base.metadata.create_all(bind=test_engine)

    # Insert a couple of seed rows
    with test_engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO users (name, email, status, country, created_at) VALUES "
                "('Test Alice', 'alice@test.com', 'active', 'UK', '2025-01-01 00:00:00'), "
                "('Test Bob', 'bob@test.com', 'inactive', 'US', '2025-06-01 00:00:00')"
            )
        )
        conn.commit()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
