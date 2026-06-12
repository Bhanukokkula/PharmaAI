"""List mock users and resolve the active mock session.

There is no auth in v1. The frontend's "shopping as" dropdown lists these
users and sends the chosen id as the `X-User-Id` header on subsequent
requests (see app/deps.py).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import PersonaOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.execute(select(User).order_by(User.id)).scalars().all()


@router.get("/personas", response_model=list[PersonaOut])
def list_personas(db: Session = Depends(get_db)) -> list[PersonaOut]:
    """One sample user per synthetic segment, for the "quick demo" login.

    Lets the mock sign-in page offer "shop as an allergy-season buyer" etc.
    without exposing the full 2,000-user list or the `segment` field as a
    general-purpose API attribute.
    """
    segments = db.execute(select(User.segment).distinct().order_by(User.segment)).scalars().all()
    personas = []
    for segment in segments:
        user = db.execute(
            select(User).where(User.segment == segment).order_by(User.id)
        ).scalars().first()
        if user is not None:
            personas.append(PersonaOut(id=user.id, display_name=user.display_name, segment_label=segment))
    return personas


@router.get("/me", response_model=UserOut)
def get_active_user(user: User = Depends(get_current_user)) -> User:
    return user
