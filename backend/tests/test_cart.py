def _headers(user):
    return {"X-User-Id": str(user.id)}


def test_empty_cart(client, products, users):
    resp = client.get("/cart", headers=_headers(users[0]))
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}


def test_add_to_cart(client, products, users):
    pain_away = products[0]
    resp = client.post("/cart/items", json={"product_id": pain_away.id, "quantity": 2}, headers=_headers(users[0]))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["product"]["brand_name"] == "Pain Away"
    assert item["quantity"] == 2
    assert body["total"] == 10.0  # 2 x 5.00


def test_add_to_cart_existing_product_increments_quantity(client, products, users):
    pain_away = products[0]
    headers = _headers(users[0])
    client.post("/cart/items", json={"product_id": pain_away.id, "quantity": 1}, headers=headers)
    resp = client.post("/cart/items", json={"product_id": pain_away.id, "quantity": 2}, headers=headers)
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 3


def test_add_to_cart_unknown_product(client, products, users):
    resp = client.post("/cart/items", json={"product_id": 9999, "quantity": 1}, headers=_headers(users[0]))
    assert resp.status_code == 404


def test_update_cart_item_quantity(client, products, users):
    headers = _headers(users[0])
    add_resp = client.post("/cart/items", json={"product_id": products[0].id, "quantity": 1}, headers=headers)
    item_id = add_resp.json()["items"][0]["id"]

    resp = client.patch(f"/cart/items/{item_id}", json={"quantity": 5}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["quantity"] == 5


def test_update_cart_item_to_zero_removes_it(client, products, users):
    headers = _headers(users[0])
    add_resp = client.post("/cart/items", json={"product_id": products[0].id, "quantity": 1}, headers=headers)
    item_id = add_resp.json()["items"][0]["id"]

    resp = client.patch(f"/cart/items/{item_id}", json={"quantity": 0}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_remove_cart_item(client, products, users):
    headers = _headers(users[0])
    add_resp = client.post("/cart/items", json={"product_id": products[0].id, "quantity": 1}, headers=headers)
    item_id = add_resp.json()["items"][0]["id"]

    resp = client.delete(f"/cart/items/{item_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_cart_item_not_found_for_other_user(client, products, users):
    headers_a, headers_b = _headers(users[0]), _headers(users[1])
    add_resp = client.post("/cart/items", json={"product_id": products[0].id, "quantity": 1}, headers=headers_a)
    item_id = add_resp.json()["items"][0]["id"]

    resp = client.delete(f"/cart/items/{item_id}", headers=headers_b)
    assert resp.status_code == 404


def test_checkout_creates_order_and_clears_cart(client, products, users):
    headers = _headers(users[0])
    client.post("/cart/items", json={"product_id": products[0].id, "quantity": 2}, headers=headers)
    client.post("/cart/items", json={"product_id": products[1].id, "quantity": 1}, headers=headers)

    resp = client.post("/cart/checkout", headers=headers)
    assert resp.status_code == 200
    order = resp.json()
    assert order["total"] == 20.0  # 2x5.00 + 1x10.00
    assert {item["product"]["brand_name"] for item in order["items"]} == {"Pain Away", "Allergy Clear"}

    cart_resp = client.get("/cart", headers=headers)
    assert cart_resp.json() == {"items": [], "total": 0}


def test_checkout_empty_cart_fails(client, products, users):
    resp = client.post("/cart/checkout", headers=_headers(users[0]))
    assert resp.status_code == 400
