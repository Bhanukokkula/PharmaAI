"""Trains the v1 content-based recommender.

Run with `python -m ml.train` from `backend/`. Steps:

  1. Load products, users, and interactions from the DB (run `python -m
     ml.seed` first if the DB is empty).
  2. Build an item-item content similarity matrix (TF-IDF over product text
     + category one-hot, see app/services/recommender/features.py).
  3. Build an item-item co-occurrence matrix and a popularity vector from
     purchase interactions.
  4. Evaluate the resulting recommender (the exact `score_products` function
     used at serving time) against two honest, cheap signals:
       - precision@k vs. each user's *hidden* segment category affinity
         (planted by generate_synthetic.py, never seen by the recommender)
       - leave-one-out recall@k on each user's most recent purchase
  5. Save artifacts to ml/artifacts/ (loaded by ContentBasedRecommender) and
     log params/metrics/artifacts to the local MLflow file store (./mlruns).

This is intentionally simple: no train/val split tooling, no hyperparameter
search. The "model" is a handful of precomputed matrices; the honesty is in
reporting metrics against a baseline rather than claiming a number means
more than it does.
"""

from __future__ import annotations

import logging
import random
import re
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import numpy as np
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Interaction, Product, User
from app.routes.catalog import CATEGORIES
from app.services.recommender.artifacts import ARTIFACTS_DIR, SIGNAL_WEIGHTS, Artifacts, score_products
from app.services.recommender.content_based import MODEL_VERSION
from app.services.recommender import features
from ml.generate_synthetic import SEGMENTS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]
MLRUNS_DIR = BACKEND_DIR / "mlruns"
EXPERIMENT_NAME = "pharmaai-content-based"
REGISTERED_MODEL_NAME = "pharmaai-content-based"

EVAL_K = 10
EVAL_SAMPLE_SIZE = 500
EVAL_SEED = 42
TOP_AFFINITY_CATEGORIES = 2

# (product_id, interaction_type, rating_value, timestamp)
InteractionRow = tuple[int, str, float | None, datetime]


def _load_products(db) -> list[dict]:
    rows = db.execute(select(Product).order_by(Product.id)).scalars().all()
    return [
        {
            "id": p.id,
            "brand_name": p.brand_name,
            "generic_name": p.generic_name,
            "purpose": p.purpose,
            "active_ingredient": p.active_ingredient,
            "category": p.category,
        }
        for p in rows
    ]


def _load_users(db) -> dict[int, str]:
    rows = db.execute(select(User)).scalars().all()
    return {u.id: u.segment for u in rows}


def _load_interactions(db) -> tuple[dict[int, list[InteractionRow]], list[tuple[int, int]]]:
    rows = db.execute(select(Interaction)).scalars().all()
    by_user: dict[int, list[InteractionRow]] = {}
    purchases: list[tuple[int, int]] = []
    for r in rows:
        by_user.setdefault(r.user_id, []).append((r.product_id, r.interaction_type, r.rating_value, r.timestamp))
        if r.interaction_type == "purchase":
            purchases.append((r.user_id, r.product_id))
    return by_user, purchases


def _build_co_occurrence_and_popularity(
    purchases: list[tuple[int, int]],
    user_ids: list[int],
    product_index: dict[int, int],
    n_products: int,
) -> tuple[np.ndarray, np.ndarray]:
    user_index = {user_id: i for i, user_id in enumerate(user_ids)}
    purchase_matrix = np.zeros((len(user_ids), n_products))
    for user_id, product_id in purchases:
        ui = user_index.get(user_id)
        pi = product_index.get(product_id)
        if ui is not None and pi is not None:
            purchase_matrix[ui, pi] = 1.0

    co_counts = purchase_matrix.T @ purchase_matrix
    purchase_counts = np.diag(co_counts).copy()
    np.fill_diagonal(co_counts, 0.0)

    co_occurrence = np.divide(
        co_counts,
        purchase_counts[:, None],
        out=np.zeros_like(co_counts),
        where=purchase_counts[:, None] > 0,
    )

    max_count = purchase_counts.max()
    popularity = purchase_counts / max_count if max_count > 0 else purchase_counts
    return co_occurrence, popularity


def _segment_top_categories(segments: dict, top_n: int) -> dict[str, set[str]]:
    result = {}
    for segment, cfg in segments.items():
        ranked = sorted(cfg["affinity"].items(), key=lambda kv: kv[1], reverse=True)
        result[segment] = {category for category, _ in ranked[:top_n]}
    return result


def _category_share(categories: list[str], wanted: set[str], n: int) -> float:
    return sum(1 for c in categories if c in wanted) / n


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _evaluate(
    by_user: dict[int, list[InteractionRow]],
    user_segments: dict[int, str],
    artifacts: Artifacts,
    eval_user_ids: list[int],
    segment_top_categories: dict[str, set[str]],
) -> dict:
    n = len(artifacts.product_ids)

    precision_hits: list[float] = []
    precision_by_segment: dict[str, list[float]] = {}
    baseline_hits: list[float] = []

    item_recall_hits: list[float] = []
    category_recall_hits: list[float] = []
    coverage_set: set[int] = set()
    baseline_by_segment_cache: dict[str, float] = {}

    for user_id in eval_user_ids:
        segment = user_segments.get(user_id)
        if segment is None:
            continue
        rows = by_user.get(user_id, [])
        interactions = [(pid, kind, rating) for pid, kind, rating, _ts in rows]

        recs = score_products(interactions, artifacts, k=EVAL_K)
        rec_categories = [artifacts.categories[artifacts.index[r.product_id]] for r in recs]
        coverage_set.update(r.product_id for r in recs)

        top_cats = segment_top_categories[segment]
        precision = _category_share(rec_categories, top_cats, len(recs)) if recs else 0.0
        precision_hits.append(precision)
        precision_by_segment.setdefault(segment, []).append(precision)

        baseline = baseline_by_segment_cache.setdefault(
            segment, _category_share(artifacts.categories, top_cats, n)
        )
        baseline_hits.append(baseline)

        # Leave-one-out: hold out the most recently purchased item, re-score
        # with the rest of the history, and see if it (or its category)
        # comes back in the top-k.
        purchase_rows = [row for row in rows if row[1] == "purchase"]
        if purchase_rows:
            held_out = max(purchase_rows, key=lambda row: row[3])
            remaining = [(pid, kind, rating) for pid, kind, rating, _ts in rows if (pid, kind, rating, _ts) != held_out]
            loo_recs = score_products(remaining, artifacts, k=EVAL_K)
            loo_product_ids = {r.product_id for r in loo_recs}
            loo_categories = {artifacts.categories[artifacts.index[r.product_id]] for r in loo_recs}

            held_out_product_id = held_out[0]
            held_out_category = artifacts.categories[artifacts.index[held_out_product_id]]
            item_recall_hits.append(1.0 if held_out_product_id in loo_product_ids else 0.0)
            category_recall_hits.append(1.0 if held_out_category in loo_categories else 0.0)

    return {
        "precision_at_k": _mean(precision_hits),
        "precision_at_k_baseline": _mean(baseline_hits),
        "precision_at_k_by_segment": {seg: _mean(vals) for seg, vals in precision_by_segment.items()},
        "category_recall_at_k": _mean(category_recall_hits),
        "item_recall_at_k": _mean(item_recall_hits),
        "coverage_at_k": len(coverage_set) / n,
        "n_loo_users": len(item_recall_hits),
    }


def main() -> None:
    db = SessionLocal()
    try:
        products = _load_products(db)
        user_segments = _load_users(db)
        by_user, purchases = _load_interactions(db)
    finally:
        db.close()

    if not products:
        raise SystemExit("No products in the DB. Run `python -m ml.seed` first.")

    n_products = len(products)
    product_index = {p["id"]: i for i, p in enumerate(products)}
    user_ids = list(user_segments.keys())

    log.info("Building item content similarity for %d products...", n_products)
    item_similarity = features.build_item_similarity(products, CATEGORIES)

    log.info("Building co-occurrence + popularity from %d purchase interactions...", len(purchases))
    co_occurrence, popularity = _build_co_occurrence_and_popularity(purchases, user_ids, product_index, n_products)

    artifacts = Artifacts(
        product_ids=[p["id"] for p in products],
        brand_names=[p["brand_name"] for p in products],
        categories=[p["category"] for p in products],
        category_names=CATEGORIES,
        item_similarity=item_similarity,
        co_occurrence=co_occurrence,
        popularity=popularity,
        meta={},
    )

    rng = random.Random(EVAL_SEED)
    eval_user_ids = rng.sample(user_ids, min(EVAL_SAMPLE_SIZE, len(user_ids)))
    segment_top_categories = _segment_top_categories(SEGMENTS, TOP_AFFINITY_CATEGORIES)

    log.info("Evaluating on %d sampled users...", len(eval_user_ids))
    metrics = _evaluate(by_user, user_segments, artifacts, eval_user_ids, segment_top_categories)

    log.info("precision@%d vs. segment affinity: %.3f (random baseline: %.3f)",
             EVAL_K, metrics["precision_at_k"], metrics["precision_at_k_baseline"])
    log.info("leave-one-out category recall@%d: %.3f (item recall@%d: %.3f, n=%d)",
             EVAL_K, metrics["category_recall_at_k"], EVAL_K, metrics["item_recall_at_k"], metrics["n_loo_users"])
    log.info("catalog coverage@%d: %.3f", EVAL_K, metrics["coverage_at_k"])

    trained_at = datetime.now(timezone.utc).isoformat()
    artifacts.meta = {
        "model_version": MODEL_VERSION,
        "trained_at": trained_at,
        "n_products": n_products,
        "n_users": len(user_ids),
        "n_interactions": sum(len(v) for v in by_user.values()),
        "signal_weights": SIGNAL_WEIGHTS,
        "tfidf_max_features": features.TFIDF_MAX_FEATURES,
        "category_weight": features.CATEGORY_WEIGHT,
        "eval": {k: v for k, v in metrics.items() if k != "precision_at_k_by_segment"},
        "eval_k": EVAL_K,
        "eval_sample_size": len(eval_user_ids),
    }
    artifacts.save()
    log.info("Saved artifacts to %s", ARTIFACTS_DIR)

    mlflow.set_tracking_uri(f"file:{MLRUNS_DIR}")
    mlflow.set_experiment(EXPERIMENT_NAME)

    run_name = f"{MODEL_VERSION}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tag("model_version", MODEL_VERSION)

        mlflow.log_param("n_products", n_products)
        mlflow.log_param("n_users", len(user_ids))
        mlflow.log_param("n_interactions", artifacts.meta["n_interactions"])
        mlflow.log_param("n_purchase_interactions", len(purchases))
        mlflow.log_param("eval_k", EVAL_K)
        mlflow.log_param("eval_sample_size", len(eval_user_ids))
        mlflow.log_param("top_affinity_categories", TOP_AFFINITY_CATEGORIES)
        mlflow.log_param("tfidf_max_features", features.TFIDF_MAX_FEATURES)
        mlflow.log_param("category_weight", features.CATEGORY_WEIGHT)
        for name, weight in SIGNAL_WEIGHTS.items():
            mlflow.log_param(f"signal_weight_{name}", weight)

        mlflow.log_metric("precision_at_k_segment_affinity", metrics["precision_at_k"])
        mlflow.log_metric("precision_at_k_random_baseline", metrics["precision_at_k_baseline"])
        mlflow.log_metric("category_recall_at_k", metrics["category_recall_at_k"])
        mlflow.log_metric("item_recall_at_k", metrics["item_recall_at_k"])
        mlflow.log_metric("coverage_at_k", metrics["coverage_at_k"])
        for segment, value in metrics["precision_at_k_by_segment"].items():
            mlflow.log_metric(f"precision_at_k_segment_{_slug(segment)}", value)

        mlflow.log_artifacts(str(ARTIFACTS_DIR), artifact_path="model")

        try:
            mlflow.register_model(model_uri=f"runs:/{run.info.run_id}/model", name=REGISTERED_MODEL_NAME)
        except Exception as exc:  # pragma: no cover - registry is a nice-to-have, not load-bearing
            log.warning("Skipping model registry update: %s", exc)

        log.info("Logged MLflow run %s in experiment %r", run.info.run_id, EXPERIMENT_NAME)


if __name__ == "__main__":
    main()
