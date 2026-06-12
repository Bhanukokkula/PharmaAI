from app.main import app
from app.models import PredictionLog
from app.services.recommender.base import Recommendation, RecommenderService, get_recommender


class StubRecommender(RecommenderService):
    model_version = "stub-v1"

    def recommend(self, user_id, k=10, context=None):
        return [Recommendation(product_id=999, score=0.5, reason="stub reason")]


def test_recommend_returns_recommender_output_and_logs_prediction(client, products, users, db_session):
    def override():
        return StubRecommender()

    app.dependency_overrides[get_recommender] = override
    try:
        resp = client.get("/recommend", params={"k": 3}, headers={"X-User-Id": str(users[0].id)})
    finally:
        del app.dependency_overrides[get_recommender]

    assert resp.status_code == 200
    body = resp.json()
    assert body["model_version"] == "stub-v1"
    assert body["user_id"] == users[0].id

    # StubRecommender always returns product_id=999, which doesn't exist in
    # the seeded `products` fixture, so the route should skip it.
    assert body["items"] == []

    logs = db_session.query(PredictionLog).all()
    assert len(logs) == 1
    assert logs[0].user_id == users[0].id
    assert logs[0].model_version == "stub-v1"
    assert logs[0].recommended_ids == [999]
    assert logs[0].context == {"k": 3}


def test_recommend_includes_product_details_for_known_ids(client, products, users, db_session):
    target = products[0]

    class KnownIdRecommender(RecommenderService):
        model_version = "stub-v2"

        def recommend(self, user_id, k=10, context=None):
            return [Recommendation(product_id=target.id, score=0.9, reason="because reasons")]

    app.dependency_overrides[get_recommender] = lambda: KnownIdRecommender()
    try:
        resp = client.get("/recommend", headers={"X-User-Id": str(users[0].id)})
    finally:
        del app.dependency_overrides[get_recommender]

    body = resp.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["product"]["brand_name"] == target.brand_name
    assert item["reason"] == "because reasons"
    assert item["score"] == 0.9
