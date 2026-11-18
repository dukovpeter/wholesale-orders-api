from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Unit(str, Enum):
    KG = "kg"
    BOX = "box"
    PIECE = "piece"


class OrderStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    vat_number: Mapped[str] = mapped_column(String(20), unique=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="stock_not_negative"),
        CheckConstraint("price > 0", name="price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    unit: Mapped[Unit] = mapped_column(String(10))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    min_stock: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    status: Mapped[OrderStatus] = mapped_column(String(12), default=OrderStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped[Customer] = relationship(back_populates="orders")
    lines: Mapped[list["OrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    @property
    def total(self) -> Decimal:
        return sum((line.line_total for line in self.lines), Decimal("0"))


class OrderLine(Base):
    # unit_price is a snapshot of Product.price at order time
    __tablename__ = "order_lines"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="lines")
    product: Mapped[Product] = relationship()

    @property
    def line_total(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))
