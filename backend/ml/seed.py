"""Phase 1 orchestrator: ingest -> generate -> load DB.

Run with `python -m ml.seed` from `backend/`. Steps:

  1. ensure ml/data/products.json exists (openFDA ingestion; cached, so a
     re-run is cheap) and merge it with ml/data/curated_supplements.json
     into the catalog (see ml.catalog).
  2. ensure ml/data/users.json and ml/data/interactions.json exist
     (synthetic users + planted-segment interactions).
  3. drop and recreate all tables, then load Product, User, and Interaction
     rows.

This is a dev seed script, not a migration tool: step 3 always wipes and
reloads the DB, so re-running is safe and idempotent.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from datetime import datetime

from sqlalchemy import insert

from app.db import Base, SessionLocal, engine
from app.models import Interaction, Product, User
from ml import generate_synthetic, ingest_openfda
from ml.catalog import PRODUCTS_PATH, load_catalog
from ml.generate_synthetic import INTERACTIONS_OUTPUT, USERS_OUTPUT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Deterministic but separate from generate_synthetic's RNG -- prices aren't
# part of the segment/affinity story, just enough variety for Phase 2 carts.
PRICE_SEED = 7
PRICE_RANGES: dict[str, tuple[float, float]] = {
    "Pain Relief": (4.99, 14.99),
    "Allergy": (8.99, 19.99),
    "Cold & Flu": (6.99, 16.99),
    "Digestive": (5.99, 15.99),
    "Vitamins & Supplements": (7.99, 24.99),
}


def _price_for(category: str, rng: random.Random) -> float:
    lo, hi = PRICE_RANGES.get(category, (4.99, 19.99))
    return round(rng.uniform(lo, hi), 2)


def ensure_products(force: bool = False) -> None:
    if PRODUCTS_PATH.exists() and not force:
        log.info("Using existing %s", PRODUCTS_PATH)
        return
    products = ingest_openfda.run()
    PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTS_PATH.write_text(json.dumps(products, indent=2))
    log.info("Wrote %d products to %s", len(products), PRODUCTS_PATH)


def ensure_synthetic(force: bool = False) -> None:
    if USERS_OUTPUT.exists() and INTERACTIONS_OUTPUT.exists() and not force:
        log.info("Using existing %s / %s", USERS_OUTPUT, INTERACTIONS_OUTPUT)
        return
    generate_synthetic.main()


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def load_db() -> dict[str, int]:
    catalog = load_catalog()
    users = json.loads(USERS_OUTPUT.read_text())
    interactions = json.loads(INTERACTIONS_OUTPUT.read_text())

    price_rng = random.Random(PRICE_SEED)

    db = SessionLocal()
    try:
        product_rows = [
            Product(
                brand_name=p["brand_name"],
                generic_name=p.get("generic_name"),
                category=p["category"],
                purpose=p.get("purpose"),
                active_ingredient=p.get("active_ingredient"),
                warnings=p.get("warnings"),
                dosage_and_administration=p.get("dosage_and_administration"),
                route=p.get("route"),
                product_ndc=p.get("product_ndc"),
                rxcui=p.get("rxcui"),
                price=_price_for(p["category"], price_rng),
            )
            for p in catalog
        ]
        db.add_all(product_rows)
        db.flush()

        user_rows = [
            User(username=u["username"], display_name=u["display_name"], segment=u["segment"])
            for u in users
        ]
        db.add_all(user_rows)
        db.flush()
        username_to_id = {u.username: u.id for u in user_rows}

        interaction_mappings = [
            {
                "user_id": username_to_id[i["username"]],
                "product_id": product_rows[i["product_index"]].id,
                "interaction_type": i["interaction_type"],
                "rating_value": i["rating_value"],
                "quantity": i["quantity"],
                "timestamp": datetime.fromisoformat(i["timestamp"]),
            }
            for i in interactions
        ]
        if interaction_mappings:
            db.execute(insert(Interaction), interaction_mappings)

        db.commit()
        return {
            "products": len(product_rows),
            "users": len(user_rows),
            "interactions": len(interaction_mappings),
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the PharmaAI database")
    parser.add_argument(
        "--force-ingest",
        action="store_true",
        help="Re-run openFDA ingestion even if ml/data/products.json exists",
    )
    parser.add_argument(
        "--force-generate",
        action="store_true",
        help="Regenerate synthetic users/interactions even if they already exist",
    )
    args = parser.parse_args()

    ensure_products(force=args.force_ingest)
    ensure_synthetic(force=args.force_generate)

    log.info("Resetting database tables")
    reset_db()

    counts = load_db()
    log.info(
        "Loaded %d products, %d users, %d interactions",
        counts["products"],
        counts["users"],
        counts["interactions"],
    )


if __name__ == "__main__":
    main()
