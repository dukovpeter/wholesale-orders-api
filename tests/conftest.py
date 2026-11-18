"""Test setup: a separate PostgreSQL database, built by the real migrations, emptied before every test."""
import os

import psycopg
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

TEST_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://orders:orders@localhost:5432/orders_test")
os.environ["DATABASE_URL"] = TEST_URL  # the app and Alembic read this before they are imported

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402


def _create_database_if_missing() -> None:
    url = TEST_URL.replace("postgresql+psycopg://", "postgresql://")
    base, name = url.rsplit("/", 1)
    with psycopg.connect(base + "/postgres", autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            conn.execute(f'CREATE DATABASE "{name}"')


@pytest.fixture(scope="session")
def engine():
    _create_database_if_missing()
    command.upgrade(Config("alembic.ini"), "head")  # the tests also prove the migration works
    eng = create_engine(TEST_URL)
    yield eng
    eng.dispose()


@pytest.fixture()
def SessionTest(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE order_lines, orders, products, customers RESTART IDENTITY CASCADE"))
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def client(SessionTest):
    def override():
        db = SessionTest()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def shop(client):
    """A customer and two products with known stock — the starting point of most tests."""
    customer = client.post("/customers", json={"name": "Green Corner Ltd", "vat_number": "BG123456789"}).json()
    tomatoes = client.post("/products", json={"sku": "TOM-RED-KG", "name": "Tomatoes, red", "unit": "kg", "price": "2.40", "stock": "100", "min_stock": "20"}).json()
    lemons = client.post("/products", json={"sku": "LEM-BOX", "name": "Lemons, box 10 kg", "unit": "box", "price": "18.50", "stock": "1", "min_stock": "5"}).json()
    return {"customer": customer, "tomatoes": tomatoes, "lemons": lemons}
