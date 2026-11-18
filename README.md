# Wholesale Orders API

A small, production-minded REST API for a fruit & vegetable wholesaler: products with stock, customers, and orders
that **reserve stock safely**. All data in the project is made up.

**Stack:** FastAPI · PostgreSQL 16 · SQLAlchemy 2 (ORM) · Alembic · Pydantic 2 · pytest · Docker Compose

## What it shows

| Problem in a real warehouse | How the code handles it |
|---|---|
| Two shops order the **last box** at the same moment | One transaction, product rows locked with `SELECT … FOR UPDATE` (in id order, no deadlocks). A test runs the race with two threads and expects exactly one success. |
| Prices change, but old orders must not | The unit price is **copied into the order line** at order time. |
| Money must be exact | `NUMERIC(10,2)` in the database, `Decimal` in Python, strings in JSON — never `float`. |
| An order with one missing item must not half-happen | All lines succeed or none do (`409 Conflict`, stock untouched). |
| Bad input should never reach the database | Pydantic schemas (`422`) + database `CHECK` constraints (stock ≥ 0, price > 0, quantity > 0). |
| The warehouse needs to know what to reorder | `GET /products/low-stock`. |

## Run it

```bash
docker compose up --build        # API on http://localhost:8000, docs on /docs
docker compose exec api python seed.py
```

Try an order:

```bash
curl -X POST http://localhost:8000/orders -H "content-type: application/json" \
  -d '{"customer_id": 1, "lines": [{"product_id": 1, "quantity": "10"}]}'
```

## Tests

The tests run against a real PostgreSQL database (`orders_test`), built by the same Alembic migrations as production.

```bash
docker compose up -d db
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows; use .venv/bin on macOS/Linux
.venv/Scripts/python -m pytest
```

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | liveness check |
| GET / POST | `/products` | list (paginated) / create |
| GET | `/products/low-stock` | products at or below minimum stock |
| GET | `/products/{id}` | one product |
| POST | `/customers` · GET `/customers/{id}` | create / read a customer |
| POST | `/orders` | place an order and reserve stock |
| GET | `/orders/{id}` | order with lines and total |
| POST | `/orders/{id}/cancel` | cancel and return the stock |

## Structure

```
app/
  db.py         engine, session per request
  models.py     tables as Python classes (SQLAlchemy ORM)
  schemas.py    what the API accepts and returns (Pydantic)
  services.py   business rules: place_order, cancel_order, low_stock
  routers.py    HTTP endpoints, error → status code
  main.py       FastAPI app
alembic/        migrations (schema history)
tests/          pytest, real PostgreSQL
```

## Design decisions

- **Business rules live in `services.py`, not in the endpoints**: they can be tested and reused (CLI, background jobs).
- **Row locks instead of optimistic retries**: orders are short and contention is on a few hot products, so a short lock is simpler and correct.
- **Migrations, not `create_all()`**: every schema change is versioned and reviewable.

Built with AI-assisted development.
