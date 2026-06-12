"""Shared FastAPI dependencies."""

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User


def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the mock "active user" from the X-User-Id header.

    There is no auth in v1 — the frontend's user switcher sets this header.
    Falls back to the first seeded user so the API is usable without it.
    """
    if x_user_id is not None:
        user = db.get(User, x_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User {x_user_id} not found")
        return user

    user = db.execute(select(User).order_by(User.id)).scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="No users seeded yet")
    return user
