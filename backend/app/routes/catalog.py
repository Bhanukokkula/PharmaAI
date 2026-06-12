"""Product browse/search/detail.

OTC / wellness products only — see README scope framing. Nothing here
returns clinical guidance; `purpose` and `warnings` are passed through
verbatim from the openFDA label for informational display only.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product
from app.schemas import ProductList, ProductOut

router = APIRouter(prefix="/catalog", tags=["catalog"])

CATEGORIES = [
    "Pain Relief",
    "Allergy",
    "Cold & Flu",
    "Digestive",
    "Vitamins & Supplements",
]


@router.get("/categories")
def list_categories() -> list[str]:
    return CATEGORIES


@router.get("/products", response_model=ProductList)
def list_products(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Search brand/generic name"),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ProductList:
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            (Product.brand_name.ilike(like)) | (Product.generic_name.ilike(like))
        )

    total = len(db.execute(stmt).scalars().all())
    items = (
        db.execute(stmt.order_by(Product.brand_name).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return ProductList(total=total, items=items)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
