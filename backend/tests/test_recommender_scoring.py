"""Unit tests for the v1 recommender's scoring logic.

These build a small, hand-written `Artifacts` bundle (4 products) instead of
relying on `ml/artifacts/` (gitignored, produced by `python -m ml.train`),
so they run against any checkout without a trained model.
"""

import numpy as np

from app.services.recommender.artifacts import Artifacts, score_products
from app.services.recommender.features import build_item_similarity


def _build_artifacts() -> Artifacts:
    # product_ids: 10="Pain A", 20="Pain B", 30="Allergy C", 40="Vitamin D"
    item_similarity = np.array(
        [
            [0.00, 0.80, 0.20, 0.10],
            [0.80, 0.00, 0.05, 0.05],
            [0.20, 0.05, 0.00, 0.05],
            [0.10, 0.05, 0.05, 0.00],
        ]
    )
    co_occurrence = np.array(
        [
            [0.0, 0.9, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ]
    )
    popularity = np.array([0.5, 1.0, 0.3, 0.2])

    return Artifacts(
        product_ids=[10, 20, 30, 40],
        brand_names=["Pain A", "Pain B", "Allergy C", "Vitamin D"],
        categories=["Pain Relief", "Pain Relief", "Allergy", "Vitamins & Supplements"],
        category_names=["Pain Relief", "Allergy", "Vitamins & Supplements"],
        item_similarity=item_similarity,
        co_occurrence=co_occurrence,
        popularity=popularity,
        meta={},
    )


def test_cold_start_recommends_by_popularity_with_uniform_category_affinity():
    artifacts = _build_artifacts()
    recs = score_products([], artifacts, k=4)

    assert [r.product_id for r in recs] == [20, 10, 30, 40]
    assert all(r.reason == "Popular with similar shoppers" for r in recs)


def test_purchase_drives_frequently_bought_together_and_excludes_purchased_item():
    artifacts = _build_artifacts()
    recs = score_products([(10, "purchase", None)], artifacts, k=4)

    product_ids = [r.product_id for r in recs]
    assert 10 not in product_ids  # already purchased -> not re-recommended
    assert product_ids == [20, 30, 40]
    assert recs[0].reason == "Frequently bought with Pain A"
    assert recs[1].reason.startswith("Similar to Pain A")
    assert recs[2].reason.startswith("Similar to Pain A")


def test_viewing_an_item_does_not_recommend_it_back_via_self_similarity():
    artifacts = _build_artifacts()
    recs = score_products([(10, "view", None)], artifacts, k=4)

    product_ids = [r.product_id for r in recs]
    # Pain A (10) was viewed but not purchased, so it's still a valid
    # candidate -- but with self-similarity zeroed out it shouldn't win #1
    # purely for being "similar to itself". Pain B (20) -- genuinely similar
    # to Pain A *and* popular -- should rank first instead.
    assert product_ids[0] == 20

    # Pain A may still appear (e.g. on its own popularity), but never with a
    # self-referential "similar to Pain A" reason.
    for rec in recs:
        if rec.product_id == 10:
            assert "Pain A" not in rec.reason


def test_k_limits_results():
    artifacts = _build_artifacts()
    assert len(score_products([], artifacts, k=2)) == 2


def test_build_item_similarity_zeroes_diagonal():
    products = [
        {"generic_name": "A", "purpose": "pain relief", "active_ingredient": "ibuprofen", "category": "Pain Relief"},
        {"generic_name": "B", "purpose": "allergy relief", "active_ingredient": "loratadine", "category": "Allergy"},
    ]
    similarity = build_item_similarity(products, ["Pain Relief", "Allergy"])
    assert similarity[0, 0] == 0
    assert similarity[1, 1] == 0
