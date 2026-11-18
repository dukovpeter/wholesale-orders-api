from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import OrderStatus, Unit

Money = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Quantity = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Amount = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class ProductIn(BaseModel):
    sku: str = Field(pattern=r"^[A-Z0-9-]{3,32}$", examples=["TOM-RED-KG"])
    name: str = Field(min_length=2, max_length=120)
    unit: Unit
    price: Money
    stock: Amount = Decimal("0")
    min_stock: Amount = Decimal("0")


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    vat_number: str = Field(pattern=r"^BG\d{9,10}$", examples=["BG123456789"])


class CustomerOut(CustomerIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderLineIn(BaseModel):
    product_id: int
    quantity: Quantity


class OrderIn(BaseModel):
    customer_id: int
    lines: list[OrderLineIn] = Field(min_length=1, max_length=100)

    @field_validator("lines")
    @classmethod
    def one_line_per_product(cls, lines: list[OrderLineIn]) -> list[OrderLineIn]:
        ids = [line.product_id for line in lines]
        if len(ids) != len(set(ids)):
            raise ValueError("each product may appear only once in an order")
        return lines


class OrderLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    status: OrderStatus
    created_at: datetime
    lines: list[OrderLineOut]
    total: Decimal
