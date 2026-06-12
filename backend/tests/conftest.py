"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite DB — never the dev
`pharmaai.db` — via a `get_db` override on the FastAPI app. `TestClient` is
used without the `with` context manager so the app's lifespan (which would
call `init_db()` against the real engine) never runs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Product, User


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def products(db_session):
    """A handful of products spanning categories, with known prices."""
    rows = [
        Product(
            brand_name="Pain Away",
            generic_name="IBUPROFEN",
            category="Pain Relief",
            purpose="Pain reliever/fever reducer",
            active_ingredient="Ibuprofen 200 mg",
            price=5.00,
        ),
        Product(
            brand_name="Allergy Clear",
            generic_name="LORATADINE",
            category="Allergy",
            purpose="Antihistamine",
            active_ingredient="Loratadine 10 mg",
            price=10.00,
        ),
        Product(
            brand_name="Daily Multivitamin",
            generic_name="MULTIVITAMIN",
            category="Vitamins & Supplements",
            purpose="Nutritional supplement",
            active_ingredient="Multivitamin blend",
            price=15.00,
        ),
    ]
    db_session.add_all(rows)
    db_session.commit()
    for row in rows:
        db_session.refresh(row)
    return rows


@pytest.fixture()
def users(db_session):
    rows = [
        User(username="user_0001", display_name="Shopper 0001", segment="Explorer/one-off"),
        User(username="user_0002", display_name="Shopper 0002", segment="Pain management regular"),
    ]
    db_session.add_all(rows)
    db_session.commit()
    for row in rows:
        db_session.refresh(row)
    return rows
