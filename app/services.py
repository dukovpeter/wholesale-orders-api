"""Business rules. Kept out of the HTTP layer so they can be tested and reused."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Order, OrderLine, OrderStatus, Product
from app.schemas import OrderIn


class NotFound(Exception):
    """A referenced customer, product or order does not exist."""


class Conflict(Exception):
    """The request is valid but cannot be done in the current state (e.g. not enough stock)."""


def place_order(db: Session, data: OrderIn) -> Order:
    """Create an order and reserve its stock in ONE transaction.

    The product rows are locked (SELECT ... FOR UPDATE) in id order, so two orders for the last
    box cannot both succeed, and two orders never wait on each other in opposite order (deadlock).
    The unit price is copied into the line: later price changes do not rewrite old orders.
    """
    if db.get(Customer, data.customer_id) is None:
        raise NotFound(f"customer {data.customer_id} not found")

    wanted = {line.product_id: line.quantity for line in data.lines}
    products = db.scalars(
        select(Product).where(Product.id.in_(wanted)).order_by(Product.id).with_for_update()
    ).all()
    found = {p.id: p for p in products}
    missing = sorted(set(wanted) - set(found))
    if missing:
        db.rollback()
        raise NotFound(f"products not found: {missing}")

    short = [f"{p.sku} (have {p.stock}, need {wanted[p.id]})" for p in products if p.stock < wanted[p.id]]
    if short:
        db.rollback()
        raise Conflict("not enough stock: " + ", ".join(short))

    order = Order(customer_id=data.customer_id, status=OrderStatus.NEW)
    for product in products:
        qty = wanted[product.id]
        product.stock -= qty
        order.lines.append(OrderLine(product_id=product.id, quantity=qty, unit_price=product.price))
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order_id: int) -> Order:
    """Cancel an order and return its stock. Cancelling twice is a conflict, not a silent no-op."""
    order = db.scalars(select(Order).where(Order.id == order_id).with_for_update()).first()
    if order is None:
        raise NotFound(f"order {order_id} not found")
    if order.status == OrderStatus.CANCELLED:
        db.rollback()
        raise Conflict(f"order {order_id} is already cancelled")
    ids = sorted(line.product_id for line in order.lines)
    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update())}
    for line in order.lines:
        products[line.product_id].stock += line.quantity
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


def low_stock(db: Session) -> list[Product]:
    """Products at or below their minimum stock: what the warehouse must reorder."""
    return list(db.scalars(select(Product).where(Product.stock <= Product.min_stock).order_by(Product.stock - Product.min_stock, Product.id)))
