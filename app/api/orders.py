from fastapi import APIRouter, status

from app import services
from app.api.deps import DbSession, get_or_404
from app.models import Order
from app.schemas import OrderIn, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Unknown customer or product"}, 409: {"description": "Not enough stock"}},
)
def create_order(data: OrderIn, db: DbSession) -> Order:
    return services.place_order(db, data)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: DbSession) -> Order:
    return get_or_404(db, Order, order_id)


@router.post("/{order_id}/cancel", response_model=OrderOut, responses={409: {"description": "Already cancelled"}})
def cancel_order(order_id: int, db: DbSession) -> Order:
    return services.cancel_order(db, order_id)
