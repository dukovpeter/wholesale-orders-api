# Wholesale Orders API

[![CI](https://github.com/dukovpeter/wholesale-orders-api/actions/workflows/ci.yml/badge.svg)](https://github.com/dukovpeter/wholesale-orders-api/actions/workflows/ci.yml)

REST API for a fruit & vegetable wholesaler: products with stock, customers, and orders that reserve stock safely
under concurrent load. All data in the repository is made up.

**Stack:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2 · Alembic · Pydantic 2 · pytest · Docker Compose ·
GitHub Actions

## What it solves

| Problem in a real warehouse | How it is handled |
|---|---|
| Two shops order the last box at the same moment | One transaction; product rows locked with `SELECT … FOR UPDATE` in id order. See [ADR 0001](docs/adr/0001-row-locks-for-stock.md). A test runs the race with two threads. |
| Prices change, old orders must not | The unit price is copied into the order line at order time. |
| Money must be exact | `NUMERIC(10,2)` in PostgreSQL, `Decimal` in Python, strings in JSON. |
| An order must not half-happen | All lines succeed or none do — `409 Conflict`, stock untouched. |
| Bad input must not reach the database | Pydantic validation (`422`) plus `CHECK` constraints in the schema. |
| The warehouse needs to know what to reorder | `GET /api/v1/products/low-stock` |

## Quick start

```bash
docker compose up --build
docker compose exec api python seed.py
```

API: http://localhost:8000 · interactive docs: http://localhost:8000/docs

```bash
curl -X POST http://localhost:8000/api/v1/orders -H "content-type: application/json" \
  -d '{"customer_id": 1, "lines": [{"product_id": 1, "quantity": "10"}]}'
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
docker compose up -d db

ruff check . && ruff format --check .   # lint + formatting
mypy app                                # strict type check
alembic check                           # migrations match the models
pytest                                  # tests + coverage, real PostgreSQL
```

Tests use a separate database (`orders_test`) built by the same Alembic migrations as production. CI runs all of these
checks on every push and pull request (`.github/workflows/ci.yml`).

## API

| Method | Path | |
|---|---|---|
| GET | `/health` | liveness |
| GET, POST | `/api/v1/products` | list (paginated), create |
| GET | `/api/v1/products/low-stock` | at or below minimum stock |
| GET | `/api/v1/products/{id}` | one product |
| PATCH | `/api/v1/products/{id}/price` | change the price (existing orders keep theirs) |
| POST · GET | `/api/v1/customers` · `/api/v1/customers/{id}` | create, read |
| GET | `/api/v1/customers/{id}/orders` | a customer's orders, newest first |
| POST | `/api/v1/orders` | place an order, reserve stock |
| GET | `/api/v1/orders/{id}` | order with lines and total |
| POST | `/api/v1/orders/{id}/cancel` | cancel, return stock |

Errors: `404` not found · `409` valid request the current state does not allow · `422` invalid input.

## Layout

```
app/
  api/          routers per resource, shared dependencies
  config.py     settings from environment
  db.py         engine and request-scoped session
  errors.py     domain errors → HTTP status, in one place
  models.py     SQLAlchemy models
  schemas.py    request / response schemas
  services.py   business rules
alembic/        migrations
docs/adr/       architecture decisions
tests/          pytest against PostgreSQL
```

## License

MIT

Built with AI-assisted development.
