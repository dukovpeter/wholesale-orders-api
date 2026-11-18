from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ConflictError, NotFoundError
from app.models import Customer, Order, OrderLine, OrderStatus, Product
from app.schemas import CustomerIn, OrderIn, PriceUpdate, ProductIn


def create_product(db: Session, data: ProductIn) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"sku {data.sku} already exists") from exc
    db.refresh(product)
    return product


def update_price(db: Session, product_id: int, data: PriceUpdate) -> Product:
    # Lock the row so a concurrent order reads either the old or the new price, never a half-written state.
    product = db.scalars(select(Product).where(Product.id == product_id).with_for_update()).first()
    if product is None:
        raise NotFoundError(f"product {product_id} not found")
    product.price = data.price
    db.commit()
    db.refresh(product)
    return product


def create_customer(db: Session, data: CustomerIn) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"vat number {data.vat_number} already exists") from exc
    db.refresh(customer)
    return customer


def _lock_products(db: Session, ids: list[int]) -> dict[int, Product]:
    # Lock in a fixed order (by id) so two orders never wait on each other in reverse — no deadlocks.
    stmt = select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update()
    return {p.id: p for p in db.scalars(stmt)}


def place_order(db: Session, data: OrderIn) -> Order:
    if db.get(Customer, data.customer_id) is None:
        raise NotFoundError(f"customer {data.customer_id} not found")

    wanted = {line.product_id: line.quantity for line in data.lines}
    products = _lock_products(db, sorted(wanted))

    missing = sorted(set(wanted) - set(products))
    if missing:
        db.rollback()
        raise NotFoundError(f"products not found: {missing}")

    short = [f"{p.sku} (have {p.stock}, need {wanted[p.id]})" for p in products.values() if p.stock < wanted[p.id]]
    if short:
        db.rollback()
        raise ConflictError("not enough stock: " + ", ".join(short))

    order = Order(customer_id=data.customer_id, status=OrderStatus.NEW)
    for product in products.values():
        product.stock -= wanted[product.id]
        # The price is copied, so a later price change never rewrites an existing order.
        order.lines.append(OrderLine(product_id=product.id, quantity=wanted[product.id], unit_price=product.price))
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order_id: int) -> Order:
    order = db.scalars(select(Order).where(Order.id == order_id).with_for_update()).first()
    if order is None:
        raise NotFoundError(f"order {order_id} not found")
    if order.status == OrderStatus.CANCELLED:
        db.rollback()
        raise ConflictError(f"order {order_id} is already cancelled")

    products = _lock_products(db, sorted(line.product_id for line in order.lines))
    for line in order.lines:
        products[line.product_id].stock += line.quantity
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


def low_stock(db: Session) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.stock <= Product.min_stock)
        .order_by(Product.stock - Product.min_stock, Product.id)
    )
    return list(db.scalars(stmt))


def customer_orders(db: Session, customer_id: int) -> list[Order]:
    if db.get(Customer, customer_id) is None:
        raise NotFoundError(f"customer {customer_id} not found")
    stmt = (
        select(Order)
        .where(Order.customer_id == customer_id)
        # Load all lines in one extra query instead of one query per order (N+1).
        .options(selectinload(Order.lines))
        # id breaks ties between orders created in the same instant.
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return list(db.scalars(stmt))
