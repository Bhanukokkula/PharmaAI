"""Item feature vectors for the v1 content-based recommender.

Used only by ml/train.py: combines a TF-IDF representation of each
product's text fields with a one-hot category vector, then L2-normalizes
each row so cosine similarity is a plain dot product. The resulting
item-item similarity matrix is precomputed and saved as an artifact —
serving never re-runs this.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# Relative weight of "same category" vs. text similarity when building item
# vectors. Higher = category match matters more than ingredient/purpose
# wording.
CATEGORY_WEIGHT = 2.0

TFIDF_MAX_FEATURES = 300


def _text_for(product: dict) -> str:
    return " ".join(
        [
            product.get("generic_name") or "",
            product.get("purpose") or "",
            product.get("active_ingredient") or "",
        ]
    )


def build_item_similarity(products: list[dict], categories: list[str]) -> np.ndarray:
    """Returns an (n, n) cosine-similarity matrix over product feature vectors.

    `products` is a list of dicts with `generic_name`, `purpose`,
    `active_ingredient`, and `category`, in the row order the rest of the
    artifacts use. `categories` is the fixed list of known category names,
    used to build the one-hot block.
    """
    texts = [_text_for(p) for p in products]
    tfidf = TfidfVectorizer(max_features=TFIDF_MAX_FEATURES, stop_words="english")
    text_features = tfidf.fit_transform(texts).toarray()

    category_index = {c: i for i, c in enumerate(categories)}
    category_features = np.zeros((len(products), len(categories)))
    for row, product in enumerate(products):
        col = category_index.get(product["category"])
        if col is not None:
            category_features[row, col] = CATEGORY_WEIGHT

    features = np.hstack([text_features, category_features])
    features = normalize(features)
    similarity = features @ features.T

    # Every product is trivially "identical to itself" (cosine similarity 1.0,
    # the maximum possible). Zeroing the diagonal keeps self-similarity from
    # ever winning a candidate's similarity score or being picked as its own
    # "similar to ..." anchor in score_products().
    np.fill_diagonal(similarity, 0.0)
    return similarity
