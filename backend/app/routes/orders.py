"""Read-only order history for the active mock user.

Additive endpoint for the account page — orders themselves are created via
POST /cart/checkout (see app/routes/cart.py).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Order, User
from app.schemas import OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Order]:
    return (
        db.execute(
            select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
        )
        .scalars()
        .all()
    )
