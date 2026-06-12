def test_list_users(client, users):
    resp = client.get("/users")
    assert resp.status_code == 200
    body = resp.json()
    assert [u["username"] for u in body] == ["user_0001", "user_0002"]


def test_get_active_user_defaults_to_first(client, users):
    resp = client.get("/users/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "user_0001"


def test_get_active_user_via_header(client, users):
    second = users[1]
    resp = client.get("/users/me", headers={"X-User-Id": str(second.id)})
    assert resp.status_code == 200
    assert resp.json()["username"] == "user_0002"


def test_get_active_user_unknown_id(client, users):
    resp = client.get("/users/me", headers={"X-User-Id": "9999"})
    assert resp.status_code == 404


def test_no_users_seeded(client):
    resp = client.get("/users/me")
    assert resp.status_code == 404
