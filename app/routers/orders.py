from fastapi import APIRouter

from app.schemas import OrderCreate, OrderUpdate
from app.services.ledger import (
    create_order_record,
    list_order_records,
    update_order_record
)


router = APIRouter(prefix="/api/orders", tags=["订单台账"])


@router.post("", status_code=201)
def create_order(order: OrderCreate):
    return create_order_record(order)


@router.get("")
def list_orders():
    items = list_order_records()
    return {"total": len(items), "items": items}


@router.patch("/{order_id}")
def update_order(
    order_id: int,
    order_update: OrderUpdate
):
    return update_order_record(order_id, order_update)
