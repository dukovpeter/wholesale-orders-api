from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app import services
from app.api.deps import DbSession, get_or_404
from app.config import get_settings
from app.models import Product
from app.schemas import PriceUpdate, ProductIn, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    db: DbSession,
    limit: int = Query(50, ge=1, le=get_settings().page_size_max),
    offset: int = Query(0, ge=0),
) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.id).limit(limit).offset(offset)))


@router.get("/low-stock", response_model=list[ProductOut])
def list_low_stock(db: DbSession) -> list[Product]:
    return services.low_stock(db)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: DbSession) -> Product:
    return get_or_404(db, Product, product_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductIn, db: DbSession) -> Product:
    return services.create_product(db, data)


@router.patch("/{product_id}/price", response_model=ProductOut)
def update_price(product_id: int, data: PriceUpdate, db: DbSession) -> Product:
    return services.update_price(db, product_id, data)
