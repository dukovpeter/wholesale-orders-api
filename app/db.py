"""Database connection: one engine per process, one session per request."""
import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://orders:orders@localhost:5432/orders")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class of every ORM model."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency: opens a session for the request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
