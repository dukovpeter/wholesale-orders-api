# ADR 0001 — Row locks for stock reservation

**Status:** accepted · **Date:** 2026-11-18

## Context
Several shops order at the same time, and a few products (lemons, tomatoes in season) are "hot". If two orders read
the same stock and both pass the check, we sell stock we do not have. Orders are short: a handful of lines, one
transaction, milliseconds.

## Options
1. **Pessimistic locking** — `SELECT … FOR UPDATE` on the ordered products inside the order transaction.
2. **Optimistic locking** — a `version` column; the update fails if someone changed the row, and the client retries.
3. **Atomic conditional update** — `UPDATE products SET stock = stock - :q WHERE id = :id AND stock >= :q`, check the
   row count.

## Decision
Option 1. Lock the product rows **in id order** (prevents deadlocks), check every line, then write — all or nothing.

## Why not the others
- Optimistic locking moves the retry to the client and makes failures more likely exactly on hot products.
- The conditional update is fast for one product, but an order has many lines; making it all-or-nothing needs the same
  transaction plus per-line rollback logic, which is harder to read and test.

## Consequences
- Orders for the same product queue for a few milliseconds — acceptable at our volume.
- The rule is proven by `tests/test_orders.py::test_two_customers_cannot_both_buy_the_last_box`; removing
  `with_for_update()` makes it fail.
- Revisit if orders become long-running (e.g. calls to a payment provider inside the transaction).
