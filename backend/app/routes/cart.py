"""Cart + order flow.

Order flow ends at a confirmation screen — no payment processing (see
README "What NOT to build").
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import CartItem, Order, OrderItem, Product, User
from app.schemas import (
    CartAddRequest,
    CartItemOut,
    CartOut,
    CartUpdateRequest,
    OrderOut,
)

router = APIRouter(prefix="/cart", tags=["cart"])


def _cart_out(db: Session, user: User) -> CartOut:
    items = (
        db.execute(select(CartItem).where(CartItem.user_id == user.id))
        .scalars()
        .all()
    )
    total = sum(item.product.price * item.quantity for item in items)
    return CartOut(items=items, total=round(total, 2))


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    return _cart_out(db, user)


@router.post("/items", response_model=CartOut)
def add_to_cart(
    body: CartAddRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    product = db.get(Product, body.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if body.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be >= 1")

    existing = db.execute(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.product_id == body.product_id
        )
    ).scalar_one_or_none()

    if existing:
        existing.quantity += body.quantity
    else:
        db.add(CartItem(user_id=user.id, product_id=body.product_id, quantity=body.quantity))

    db.commit()
    return _cart_out(db, user)


@router.patch("/items/{item_id}", response_model=CartOut)
def update_cart_item(
    item_id: int,
    body: CartUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    item = db.get(CartItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if body.quantity < 1:
        db.delete(item)
    else:
        item.quantity = body.quantity

    db.commit()
    return _cart_out(db, user)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    item = db.get(CartItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()
    return _cart_out(db, user)


@router.post("/checkout", response_model=OrderOut)
def checkout(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Order:
    items = (
        db.execute(select(CartItem).where(CartItem.user_id == user.id))
        .scalars()
        .all()
    )
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = round(sum(item.product.price * item.quantity for item in items), 2)
    order = Order(user_id=user.id, total=total)
    db.add(order)
    db.flush()

    for item in items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
        )
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order
