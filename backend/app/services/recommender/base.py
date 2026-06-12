"""The recommender boundary.

This is the most important interface in the project: routes depend ONLY on
`RecommenderService`, never on a concrete implementation. Swapping in a
future RAG/chatbot assistant (Fork A) or a drift-prone forecasting model
(Fork B) is a one-line change in `get_recommender()` below — no route or
frontend changes required.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Recommendation:
    product_id: int
    score: float
    reason: str


class RecommenderService(ABC):
    """Abstract interface for all recommenders, v1 and future forks."""

    #: Identifies which model/version produced recommendations. Written to
    #: every PredictionLog row so future monitoring can slice by version.
    model_version: str = "unversioned"

    @abstractmethod
    def recommend(
        self, user_id: int, k: int = 10, context: dict | None = None
    ) -> list[Recommendation]:
        """Return up to `k` recommendations for `user_id`.

        `context` is an open-ended dict (e.g. {"page": "cart"}) that
        implementations may use or ignore. It is logged as-is to
        PredictionLog for future analysis.
        """
        raise NotImplementedError


_recommender: RecommenderService | None = None


def get_recommender() -> RecommenderService:
    """Returns the active recommender singleton.

    This is the single wiring point referenced in the build brief: to swap
    the v1 content-based recommender for a future fork, change the
    construction below and nothing else in the codebase needs to know.
    """
    global _recommender
    if _recommender is None:
        from app.services.recommender.content_based import ContentBasedRecommender

        _recommender = ContentBasedRecommender()
    return _recommender
