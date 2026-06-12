def test_list_categories(client):
    resp = client.get("/catalog/categories")
    assert resp.status_code == 200
    categories = resp.json()
    assert "Pain Relief" in categories
    assert "Vitamins & Supplements" in categories


def test_list_products(client, products):
    resp = client.get("/catalog/products")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert {p["brand_name"] for p in body["items"]} == {"Pain Away", "Allergy Clear", "Daily Multivitamin"}


def test_list_products_filters_by_category(client, products):
    resp = client.get("/catalog/products", params={"category": "Allergy"})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["brand_name"] == "Allergy Clear"


def test_list_products_search(client, products):
    resp = client.get("/catalog/products", params={"q": "multivitamin"})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["brand_name"] == "Daily Multivitamin"


def test_list_products_pagination(client, products):
    first = client.get("/catalog/products", params={"limit": 2, "offset": 0}).json()
    second = client.get("/catalog/products", params={"limit": 2, "offset": 2}).json()
    assert first["total"] == 3
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert {p["id"] for p in first["items"]} != {p["id"] for p in second["items"]}


def test_get_product(client, products):
    target = products[0]
    resp = client.get(f"/catalog/products/{target.id}")
    assert resp.status_code == 200
    assert resp.json()["brand_name"] == "Pain Away"


def test_get_product_not_found(client, products):
    resp = client.get("/catalog/products/9999")
    assert resp.status_code == 404
