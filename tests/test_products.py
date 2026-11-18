"""Products and customers: creation, validation and duplicates."""


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_read_product(client):
    r = client.post("/products", json={"sku": "CUC-KG", "name": "Cucumbers", "unit": "kg", "price": "1.90", "stock": "40"})
    assert r.status_code == 201
    assert client.get(f"/products/{r.json()['id']}").json()["name"] == "Cucumbers"


def test_price_is_exact_decimal_not_float(client):
    r = client.post("/products", json={"sku": "APL-KG", "name": "Apples", "unit": "kg", "price": "0.10", "stock": "3"})
    assert r.json()["price"] == "0.10"


def test_rejects_negative_price_and_bad_sku(client):
    bad_price = client.post("/products", json={"sku": "X-1", "name": "Bad", "unit": "kg", "price": "-1"})
    bad_sku = client.post("/products", json={"sku": "lower case", "name": "Bad", "unit": "kg", "price": "1"})
    assert bad_price.status_code == 422
    assert bad_sku.status_code == 422


def test_duplicate_sku_is_conflict(client):
    body = {"sku": "PEP-KG", "name": "Peppers", "unit": "kg", "price": "3.20"}
    assert client.post("/products", json=body).status_code == 201
    assert client.post("/products", json=body).status_code == 409


def test_customer_vat_format_and_duplicates(client):
    assert client.post("/customers", json={"name": "Shop", "vat_number": "123"}).status_code == 422
    assert client.post("/customers", json={"name": "Shop", "vat_number": "BG111111111"}).status_code == 201
    assert client.post("/customers", json={"name": "Shop 2", "vat_number": "BG111111111"}).status_code == 409


def test_low_stock_lists_only_products_to_reorder(client, shop):
    skus = [p["sku"] for p in client.get("/products/low-stock").json()]
    assert skus == ["LEM-BOX"]


def test_unknown_product_is_404(client):
    assert client.get("/products/999").status_code == 404
