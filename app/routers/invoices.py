from fastapi import APIRouter

from app.schemas import InvoiceCreate, InvoiceUpdate
from app.services.ledger import (
    create_invoice_record,
    list_invoice_records,
    delete_invoice_record,
    update_invoice_record
)


router = APIRouter(prefix="/api/invoices", tags=["发票台账"])


@router.post("", status_code=201)
def create_invoice(invoice: InvoiceCreate):
    return create_invoice_record(invoice)


@router.get("")
def list_invoices():
    items = list_invoice_records()
    return {"total": len(items), "items": items}


@router.patch("/{invoice_id}")
def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate
):
    return update_invoice_record(
        invoice_id,
        invoice_update
    )
@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int):
    return delete_invoice_record(invoice_id)