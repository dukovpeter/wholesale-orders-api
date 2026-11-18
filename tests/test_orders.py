"""Orders: the business rules that protect money and stock."""

import threading
from decimal import Decimal

from app import services
from app.errors import ConflictError
from app.models import Product
from app.schemas import OrderIn


def order(client, shop, *lines):
    return client.post(
        "/api/v1/orders",
        json={"customer_id": shop["customer"]["id"], "lines": [{"product_id": p, "quantity": q} for p, q in lines]},
    )


def test_order_reserves_stock_and_computes_total(client, shop):
    r = order(client, shop, (shop["tomatoes"]["id"], "12.5"))
    assert r.status_code == 201
    assert r.json()["total"] == "30.00"  # 12.5 kg × 2.40
    assert client.get(f"/api/v1/products/{shop['tomatoes']['id']}").json()["stock"] == "87.50"


def test_not_enough_stock_is_conflict_and_changes_nothing(client, shop):
    r = order(client, shop, (shop["tomatoes"]["id"], "5"), (shop["lemons"]["id"], "3"))
    assert r.status_code == 409
    assert client.get(f"/api/v1/products/{shop['tomatoes']['id']}").json()["stock"] == "100.00"  # all or nothing


def test_price_is_frozen_in_the_order(client, shop, session_factory):
    created = order(client, shop, (shop["tomatoes"]["id"], "1")).json()
    with session_factory() as db:
        db.get(Product, shop["tomatoes"]["id"]).price = Decimal("9.99")
        db.commit()
    assert client.get(f"/api/v1/orders/{created['id']}").json()["lines"][0]["unit_price"] == "2.40"


def test_cancel_returns_stock_and_cannot_cancel_twice(client, shop):
    created = order(client, shop, (shop["lemons"]["id"], "1")).json()
    assert client.post(f"/api/v1/orders/{created['id']}/cancel").json()["status"] == "cancelled"
    assert client.get(f"/api/v1/products/{shop['lemons']['id']}").json()["stock"] == "1.00"
    assert client.post(f"/api/v1/orders/{created['id']}/cancel").status_code == 409


def test_unknown_customer_or_product_is_404(client, shop):
    assert (
        client.post(
            "/api/v1/orders",
            json={"customer_id": 999, "lines": [{"product_id": shop["tomatoes"]["id"], "quantity": "1"}]},
        ).status_code
        == 404
    )
    assert order(client, shop, (999, "1")).status_code == 404


def test_same_product_twice_in_one_order_is_rejected(client, shop):
    assert order(client, shop, (shop["tomatoes"]["id"], "1"), (shop["tomatoes"]["id"], "2")).status_code == 422


def test_two_customers_cannot_both_buy_the_last_box(client, shop, session_factory):
    """The race that row locks prevent: two orders for the last box of lemons at the same moment."""
    data = OrderIn(customer_id=shop["customer"]["id"], lines=[{"product_id": shop["lemons"]["id"], "quantity": "1"}])
    results, start = [], threading.Barrier(2)

    def buy():
        with session_factory() as db:
            start.wait()
            try:
                services.place_order(db, data)
                results.append("ok")
            except ConflictError:
                results.append("conflict")

    threads = [threading.Thread(target=buy) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == ["conflict", "ok"]
    with session_factory() as db:
        assert db.get(Product, shop["lemons"]["id"]).stock == Decimal("0")


def test_customer_orders_newest_first(client, shop):
    first = order(client, shop, (shop["tomatoes"]["id"], "1")).json()
    second = order(client, shop, (shop["tomatoes"]["id"], "2")).json()
    listed = client.get(f"/api/v1/customers/{shop['customer']['id']}/orders").json()
    assert [o["id"] for o in listed] == [second["id"], first["id"]]


def test_orders_of_unknown_customer_is_404(client):
    assert client.get("/api/v1/customers/999/orders").status_code == 404
