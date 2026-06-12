"""SQLAlchemy ORM models.

Core entities: Product (real OTC catalog from openFDA), User (mock identities
with a hidden ground-truth `segment` used to evaluate the recommender),
Interaction (view/purchase/rating events), and PredictionLog (every
recommend() call, for the future monitoring/eval layer).

CartItem/Order/OrderItem support the e-commerce flow in Phase 2.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    brand_name: Mapped[str] = mapped_column(String(255), index=True)
    generic_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(64), index=True)

    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_ingredient: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    dosage_and_administration: Mapped[str | None] = mapped_column(Text, nullable=True)

    route: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product_ndc: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rxcui: Mapped[str | None] = mapped_column(String(64), nullable=True)

    price: Mapped[float] = mapped_column(Float, default=9.99)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="product")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))

    # Hidden ground-truth segment label planted by generate_synthetic.py.
    # Used to evaluate the recommender (precision@k vs. segment affinity),
    # not exposed as a "real" attribute in the product UI.
    segment: Mapped[str] = mapped_column(String(64), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="user")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)

    # "view" | "purchase" | "rating"
    interaction_type: Mapped[str] = mapped_column(String(32), index=True)

    rating_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    user: Mapped["User"] = relationship(back_populates="interactions")
    product: Mapped["Product"] = relationship(back_populates="interactions")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recommended_ids: Mapped[list] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64))
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    total: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
