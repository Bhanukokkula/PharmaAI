"""Saved artifacts for the v1 content-based recommender, plus the scoring
function shared between training (evaluation) and serving.

Keeping `score_products` here — imported by both `ml/train.py` and
`content_based.py` — means the metric train.py reports is computed by the
exact function that serves live recommendations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.services.recommender.base import Recommendation

ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "ml" / "artifacts"

# Interaction-type weights for building a user's "engagement vector" over
# products. v1 treats every interaction as a positive signal of interest,
# just with different strengths — ratings are scaled into the same range
# rather than allowed to go negative, keeping the math (and the "why was
# this recommended" story) simple.
VIEW_WEIGHT = 1.0
PURCHASE_WEIGHT = 3.0
RATING_SCALE = 0.6  # rating_value (1-5) * RATING_SCALE -> 0.6-3.0

# Blend weights for the three recommendation signals. Each signal is
# normalized to [0, 1] (by its own max) before blending, so no signal
# dominates purely because of scale.
SIGNAL_WEIGHTS = {
    "similarity": 0.33,
    "cooccurrence": 0.33,
    "popularity": 0.34,
}


@dataclass
class Artifacts:
    product_ids: list[int]
    brand_names: list[str]
    categories: list[str]
    category_names: list[str]
    item_similarity: np.ndarray  # (n, n) cosine similarity, content-based
    co_occurrence: np.ndarray  # (n, n) row-normalized "bought i -> also bought j"
    popularity: np.ndarray  # (n,) purchase-count popularity, in [0, 1]
    meta: dict

    @property
    def index(self) -> dict[int, int]:
        return {product_id: i for i, product_id in enumerate(self.product_ids)}

    @staticmethod
    def load(directory: Path = ARTIFACTS_DIR) -> "Artifacts | None":
        meta_path = directory / "meta.json"
        if not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text())
        catalog = json.loads((directory / "catalog.json").read_text())
        return Artifacts(
            product_ids=[row["id"] for row in catalog],
            brand_names=[row["brand_name"] for row in catalog],
            categories=[row["category"] for row in catalog],
            category_names=meta["category_names"],
            item_similarity=np.load(directory / "item_similarity.npy"),
            co_occurrence=np.load(directory / "co_occurrence.npy"),
            popularity=np.load(directory / "popularity.npy"),
            meta=meta,
        )

    def save(self, directory: Path = ARTIFACTS_DIR) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        catalog = [
            {"id": product_id, "brand_name": brand_name, "category": category}
            for product_id, brand_name, category in zip(
                self.product_ids, self.brand_names, self.categories
            )
        ]
        (directory / "catalog.json").write_text(json.dumps(catalog, indent=2))
        np.save(directory / "item_similarity.npy", self.item_similarity)
        np.save(directory / "co_occurrence.npy", self.co_occurrence)
        np.save(directory / "popularity.npy", self.popularity)
        meta = {**self.meta, "category_names": self.category_names}
        (directory / "meta.json").write_text(json.dumps(meta, indent=2))


# (product_id, interaction_type, rating_value)
InteractionTuple = tuple[int, str, float | None]


def _engagement_vector(interactions: list[InteractionTuple], index: dict[int, int], n: int) -> np.ndarray:
    vec = np.zeros(n)
    for product_id, kind, rating_value in interactions:
        i = index.get(product_id)
        if i is None:
            continue
        if kind == "view":
            vec[i] += VIEW_WEIGHT
        elif kind == "purchase":
            vec[i] += PURCHASE_WEIGHT
        elif kind == "rating" and rating_value is not None:
            vec[i] += rating_value * RATING_SCALE
    return vec


def _purchase_vector(interactions: list[InteractionTuple], index: dict[int, int], n: int) -> np.ndarray:
    vec = np.zeros(n)
    for product_id, kind, _ in interactions:
        if kind != "purchase":
            continue
        i = index.get(product_id)
        if i is not None:
            vec[i] += PURCHASE_WEIGHT
    return vec


def _normalize(scores: np.ndarray) -> np.ndarray:
    peak = scores.max()
    if peak <= 0:
        return scores
    return scores / peak


def _category_affinity(engagement: np.ndarray, artifacts: Artifacts) -> dict[str, float]:
    if engagement.sum() == 0:
        uniform = 1.0 / len(artifacts.category_names)
        return dict.fromkeys(artifacts.category_names, uniform)

    totals = dict.fromkeys(artifacts.category_names, 0.0)
    for weight, category in zip(engagement, artifacts.categories):
        totals[category] += float(weight)
    total = sum(totals.values())
    return {c: v / total for c, v in totals.items()}


def _reason_for(
    i: int,
    engagement: np.ndarray,
    purchases: np.ndarray,
    similarity_score: np.ndarray,
    cooccur_score: np.ndarray,
    popularity_score: np.ndarray,
    artifacts: Artifacts,
) -> str:
    scores = {
        "cooccurrence": cooccur_score[i],
        "similarity": similarity_score[i],
        "popularity": popularity_score[i],
    }
    dominant = max(scores, key=lambda key: scores[key])
    if scores[dominant] <= 0:
        return "Popular with similar shoppers"

    if dominant == "cooccurrence":
        contributions = purchases * artifacts.co_occurrence[:, i]
        anchor = int(np.argmax(contributions))
        if contributions[anchor] > 0:
            return f"Frequently bought with {artifacts.brand_names[anchor]}"
    elif dominant == "similarity":
        contributions = engagement * artifacts.item_similarity[:, i]
        anchor = int(np.argmax(contributions))
        if contributions[anchor] > 0:
            return f"Similar to {artifacts.brand_names[anchor]}, which you've checked out"

    return "Popular with similar shoppers"


def score_products(
    interactions: list[InteractionTuple],
    artifacts: Artifacts,
    k: int,
) -> list[Recommendation]:
    """Score every product for a user and return the top-k recommendations.

    `interactions` is the user's (product_id, interaction_type, rating_value)
    history, in any order. Products the user has already purchased are
    excluded from the results.
    """
    n = len(artifacts.product_ids)
    index = artifacts.index

    engagement = _engagement_vector(interactions, index, n)
    purchases = _purchase_vector(interactions, index, n)
    purchased_mask = purchases > 0

    # Signal 1: content-similar to what the user has engaged with.
    if engagement.sum() > 0:
        similarity_raw = (engagement @ artifacts.item_similarity) / engagement.sum()
    else:
        similarity_raw = np.zeros(n)

    # Signal 2: frequently bought together with what the user has purchased.
    if purchases.sum() > 0:
        cooccur_raw = (purchases @ artifacts.co_occurrence) / purchases.sum()
    else:
        cooccur_raw = np.zeros(n)

    # Signal 3: popular within categories this user engages with.
    category_affinity = _category_affinity(engagement, artifacts)
    category_weight = np.array([category_affinity[c] for c in artifacts.categories])
    popularity_raw = category_weight * artifacts.popularity

    similarity_score = _normalize(similarity_raw)
    cooccur_score = _normalize(cooccur_raw)
    popularity_score = _normalize(popularity_raw)

    total = (
        SIGNAL_WEIGHTS["similarity"] * similarity_score
        + SIGNAL_WEIGHTS["cooccurrence"] * cooccur_score
        + SIGNAL_WEIGHTS["popularity"] * popularity_score
    )
    total[purchased_mask] = -np.inf

    order = np.argsort(total)[::-1]
    recommendations: list[Recommendation] = []
    for i in order:
        if len(recommendations) >= k or total[i] == -np.inf:
            break
        reason = _reason_for(
            int(i), engagement, purchases, similarity_score, cooccur_score, popularity_score, artifacts
        )
        recommendations.append(
            Recommendation(product_id=artifacts.product_ids[i], score=round(float(total[i]), 4), reason=reason)
        )
    return recommendations
