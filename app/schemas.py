from typing import Any, Literal

from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    document_type: str
    invoice_number: str
    invoice_date: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None
    amount_excl_tax: float | None = None
    tax_amount: float | None = None
    amount_incl_tax: float
    items_text: str | None = None
    order_numbers: list[str] = Field(default_factory=list)
    review_status: str = "待人工确认"
    review_notes: list[str] = Field(default_factory=list)
    prepayment_amount: float = 0
    paid_amount: float = 0
    due_date: str | None = None
    owner: str | None = None
    source_filename: str | None = None
    raw_dify_output: dict[str, Any] = Field(
        default_factory=dict
    )


class InvoiceUpdate(BaseModel):
    prepayment_amount: float | None = Field(
        default=None,
        ge=0
    )
    paid_amount: float | None = Field(default=None, ge=0)
    due_date: str | None = None
    owner: str | None = None
    review_status: str | None = None
    review_notes: list[str] | None = None


class OrderCreate(BaseModel):
    order_type: Literal["销售订单", "采购订单"]
    order_number: str
    contract_number: str | None = None
    counterparty_name: str | None = None
    order_date: str | None = None
    delivery_date: str | None = None
    order_amount: float = Field(gt=0)
    settlement_method: str | None = None
    payment_terms: str | None = None
    prepayment_amount: float = Field(default=0, ge=0)
    paid_amount: float = Field(default=0, ge=0)
    due_date: str | None = None
    owner: str | None = None
    review_status: str = "待人工确认"
    review_notes: list[str] = Field(default_factory=list)
    source_filename: str | None = None
    raw_dify_output: dict[str, Any] = Field(
        default_factory=dict
    )


class OrderUpdate(BaseModel):
    contract_number: str | None = None
    counterparty_name: str | None = None
    order_date: str | None = None
    delivery_date: str | None = None
    order_amount: float | None = Field(default=None, gt=0)
    settlement_method: str | None = None
    payment_terms: str | None = None
    prepayment_amount: float | None = Field(
        default=None,
        ge=0
    )
    paid_amount: float | None = Field(default=None, ge=0)
    due_date: str | None = None
    owner: str | None = None
    review_status: Literal[
        "待人工确认",
        "已确认",
        "需人工复核"
    ] | None = None
    review_notes: list[str] | None = None


class LoginRequest(BaseModel):
    username: str
    password: str
class ReminderSettingsUpdate(BaseModel):
    enabled: bool
    reminder_hour: int = Field(ge=0, le=23)
    reminder_minute: int = Field(ge=0, le=59)
    days_before: int = Field(ge=0, le=365)