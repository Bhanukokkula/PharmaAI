"""Recommendations.

Route depends only on `RecommenderService` (app.services.recommender.base) —
never on a concrete implementation. Every call writes a PredictionLog row,
the raw material for the future monitoring/eval layer.

Framing matters: copy is "popular with similar shoppers" / "frequently
bought together", never clinical advice (see README scope framing).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import PredictionLog, Product, User
from app.schemas import RecommendationItem, RecommendationResponse
from app.services.recommender.base import RecommenderService, get_recommender

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("", response_model=RecommendationResponse)
def get_recommendations(
    k: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    recommender: RecommenderService = Depends(get_recommender),
) -> RecommendationResponse:
    context = {"k": k}
    recs = recommender.recommend(user_id=user.id, k=k, context=context)

    db.add(
        PredictionLog(
            user_id=user.id,
            recommended_ids=[r.product_id for r in recs],
            model_version=recommender.model_version,
            context=context,
        )
    )
    db.commit()

    items: list[RecommendationItem] = []
    for rec in recs:
        product = db.get(Product, rec.product_id)
        if product is None:
            continue
        items.append(RecommendationItem(product=product, score=rec.score, reason=rec.reason))

    return RecommendationResponse(
        user_id=user.id, model_version=recommender.model_version, items=items
    )
