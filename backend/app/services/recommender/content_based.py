"""v1 recommender: category affinity + product attribute similarity.

Blends three signals computed offline by ml/train.py and loaded from
ml/artifacts/ at startup (see app/services/recommender/artifacts.py):

  - content similarity to products the user has viewed/purchased/rated
  - "frequently bought together" co-occurrence with purchased products
  - popularity within categories the user engages with

If artifacts haven't been trained yet, `recommend()` returns an empty list
— kept import-safe so the API can boot before `python -m ml.train` has run.
"""

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Interaction
from app.services.recommender.artifacts import Artifacts, score_products
from app.services.recommender.base import Recommendation, RecommenderService

MODEL_VERSION = "content-based-v1"


class ContentBasedRecommender(RecommenderService):
    model_version = MODEL_VERSION

    def __init__(self) -> None:
        self.artifacts = Artifacts.load()

    def recommend(
        self, user_id: int, k: int = 10, context: dict | None = None
    ) -> list[Recommendation]:
        if self.artifacts is None:
            return []

        db = SessionLocal()
        try:
            rows = db.execute(
                select(Interaction.product_id, Interaction.interaction_type, Interaction.rating_value).where(
                    Interaction.user_id == user_id
                )
            ).all()
        finally:
            db.close()

        interactions = [(row.product_id, row.interaction_type, row.rating_value) for row in rows]
        return score_products(interactions, self.artifacts, k=k)
