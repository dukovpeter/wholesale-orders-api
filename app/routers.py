"""HTTP endpoints. Thin layer: validate input, call a service, map errors to status codes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.models import Customer, Order, Product
from app.schemas import CustomerIn, CustomerOut, OrderIn, OrderOut, ProductIn, ProductOut

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: int):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__.lower()} {obj_id} not found")
    return obj


# ── products ──
@router.get("/products", response_model=list[ProductOut], tags=["products"])
def list_products(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return db.scalars(select(Product).order_by(Product.id).limit(limit).offset(offset)).all()


@router.get("/products/low-stock", response_model=list[ProductOut], tags=["products"])
def list_low_stock(db: Session = Depends(get_db)):
    return services.low_stock(db)


@router.get("/products/{product_id}", response_model=ProductOut, tags=["products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Product, product_id)


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED, tags=["products"])
def create_product(data: ProductIn, db: Session = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"sku {data.sku} already exists")
    db.refresh(product)
    return product


# ── customers ──
@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, tags=["customers"])
def create_customer(data: CustomerIn, db: Session = Depends(get_db)):
    customer = Customer(**data.model_dump())
    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"vat number {data.vat_number} already exists")
    db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerOut, tags=["customers"])
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Customer, customer_id)


# ── orders ──
@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED, tags=["orders"])
def create_order(data: OrderIn, db: Session = Depends(get_db)):
    try:
        return services.place_order(db, data)
    except services.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except services.Conflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@router.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Order, order_id)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut, tags=["orders"])
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    try:
        return services.cancel_order(db, order_id)
    except services.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except services.Conflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
