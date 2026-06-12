"""Shared catalog loading.

Combines the openFDA-derived catalog (ml/data/products.json) with the
hand-curated supplements (ml/data/curated_supplements.json) into a single
ordered list. Both generate_synthetic.py (which references products by list
index in interactions.json) and seed.py (which inserts Products into the DB
in this same order, so row 0 -> Product.id 1, etc.) must build the catalog
via this function so the indices line up.
"""

from __future__ import annotations

import json
from pathlib import Path

from ml.ingest_openfda import CATEGORIES

__all__ = ["CATEGORIES", "load_catalog"]

DATA_DIR = Path(__file__).resolve().parent / "data"
PRODUCTS_PATH = DATA_DIR / "products.json"
CURATED_SUPPLEMENTS_PATH = DATA_DIR / "curated_supplements.json"


def load_catalog() -> list[dict]:
    products = json.loads(PRODUCTS_PATH.read_text())
    curated = json.loads(CURATED_SUPPLEMENTS_PATH.read_text())
    return products + curated
