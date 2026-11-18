# Roadmap

Next steps, in priority order. Each item names what "done" means.

1. **Authentication per customer** — API keys stored hashed; a customer only sees and creates its own orders.
   Done: a test proves customer A cannot read customer B's order (404, not 403, to avoid leaking ids).
2. **Idempotent order creation** — `Idempotency-Key` header; a retried request returns the first order instead of
   reserving stock twice. Done: two identical requests with the same key create one order.
3. **Structured logging and metrics** — JSON logs with a request id; counters for orders placed and rejected for
   stock. Done: a rejected order appears in the logs with its request id.
4. **Backups with a tested restore** — scheduled `pg_dump`, and a script that restores into a fresh database and runs
   the test suite against it. A Docker volume is not a backup.
5. **Pagination metadata** — `total` and `next` in list responses instead of a bare array.
