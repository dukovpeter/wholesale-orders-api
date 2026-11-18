from fastapi import APIRouter, status

from app import services
from app.api.deps import DbSession, get_or_404
from app.models import Customer
from app.schemas import CustomerIn, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerIn, db: DbSession) -> Customer:
    return services.create_customer(db, data)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: DbSession) -> Customer:
    return get_or_404(db, Customer, customer_id)
