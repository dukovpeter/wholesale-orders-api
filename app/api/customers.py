from fastapi import APIRouter, status

from app import services
from app.api.deps import DbSession, get_or_404
from app.models import Customer, Order
from app.schemas import CustomerIn, CustomerOut, OrderOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerIn, db: DbSession) -> Customer:
    return services.create_customer(db, data)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: DbSession) -> Customer:
    return get_or_404(db, Customer, customer_id)


@router.get("/{customer_id}/orders", response_model=list[OrderOut])
def list_customer_orders(customer_id: int, db: DbSession) -> list[Order]:
    return services.customer_orders(db, customer_id)
