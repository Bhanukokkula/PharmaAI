"""Pydantic schemas for request/response bodies."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand_name: str
    generic_name: str | None = None
    category: str
    purpose: str | None = None
    active_ingredient: str | None = None
    warnings: str | None = None
    dosage_and_administration: str | None = None
    route: str | None = None
    product_ndc: str | None = None
    rxcui: str | None = None
    price: float


class ProductList(BaseModel):
    total: int
    items: list[ProductOut]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str


class PersonaOut(BaseModel):
    """A seeded user offered as a one-click "shop as" demo persona.

    `segment_label` surfaces the synthetic segment (e.g. "Allergy-season
    buyer") so the demo login can say what kind of shopper this is — it's
    informational framing for the demo, not exposed anywhere else.
    """

    id: int
    display_name: str
    segment_label: str


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductOut
    quantity: int


class CartOut(BaseModel):
    items: list[CartItemOut]
    total: float


class CartAddRequest(BaseModel):
    product_id: int
    quantity: int = 1


class CartUpdateRequest(BaseModel):
    quantity: int


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product: ProductOut
    quantity: int
    unit_price: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total: float
    created_at: datetime
    items: list[OrderItemOut]


class RecommendationItem(BaseModel):
    product: ProductOut
    score: float
    reason: str


class RecommendationResponse(BaseModel):
    user_id: int
    model_version: str
    items: list[RecommendationItem]
