"""SQLAlchemy engine/session setup.

Locked to SQLite for v1, but only via this module's DATABASE_URL — every
other module talks to the DB through the ORM, so swapping to Postgres later
is a one-line change to DATABASE_URL plus a driver install.
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SQLITE_PATH = os.path.join(BACKEND_DIR, "pharmaai.db")

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Used at startup and by the seed script."""
    # Importing models here (rather than at module load) avoids circular
    # imports while still registering all ORM classes on Base.metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
