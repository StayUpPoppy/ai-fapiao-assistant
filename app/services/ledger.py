import json
import sqlite3
from contextlib import closing

from fastapi import HTTPException

from app.database import get_db_connection
from app.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    OrderCreate,
    OrderUpdate
)


def calculate_payment_status(
    document_type: str,
    total_amount: float,
    paid_amount: float
) -> str:
    is_sales = document_type in {"销售发票", "销售订单"}

    if paid_amount >= total_amount:
        return "已收款" if is_sales else "已付款"
    if paid_amount > 0:
        return "部分收款" if is_sales else "部分付款"
    return "未收款" if is_sales else "未付款"


def validate_payment_amounts(
    *,
    total_amount: float,
    paid_amount: float,
    prepayment_amount: float,
    total_label: str
) -> None:
    if paid_amount > total_amount:
        raise HTTPException(
            status_code=422,
            detail=f"累计收付款金额不能大于{total_label}。"
        )
    if prepayment_amount > paid_amount:
        raise HTTPException(
            status_code=422,
            detail="预付款金额不能大于累计收付款金额。"
        )


def create_invoice_record(invoice: InvoiceCreate) -> dict:
    validate_payment_amounts(
        total_amount=invoice.amount_incl_tax,
        paid_amount=invoice.paid_amount,
        prepayment_amount=invoice.prepayment_amount,
        total_label="发票价税合计"
    )
    payment_status = calculate_payment_status(
        invoice.document_type,
        invoice.amount_incl_tax,
        invoice.paid_amount
    )

    try:
        with closing(get_db_connection()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO invoices (
                    invoice_number,
                    document_type,
                    invoice_date,
                    buyer_name,
                    seller_name,
                    amount_excl_tax,
                    tax_amount,
                    amount_incl_tax,
                    items_text,
                    review_status,
                    review_notes,
                    prepayment_amount,
                    paid_amount,
                    due_date,
                    payment_status,
                    owner,
                    source_filename,
                    raw_dify_output
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice.invoice_number,
                    invoice.document_type,
                    invoice.invoice_date,
                    invoice.buyer_name,
                    invoice.seller_name,
                    invoice.amount_excl_tax,
                    invoice.tax_amount,
                    invoice.amount_incl_tax,
                    invoice.items_text,
                    invoice.review_status,
                    json.dumps(
                        invoice.review_notes,
                        ensure_ascii=False
                    ),
                    invoice.prepayment_amount,
                    invoice.paid_amount,
                    invoice.due_date,
                    payment_status,
                    invoice.owner,
                    invoice.source_filename,
                    json.dumps(
                        invoice.raw_dify_output,
                        ensure_ascii=False
                    )
                )
            )
            invoice_id = cursor.lastrowid

            for order_number in dict.fromkeys(
                invoice.order_numbers
            ):
                normalized = order_number.strip()
                if normalized:
                    connection.execute(
                        """
                        INSERT INTO invoice_order_links (
                            invoice_id,
                            order_number
                        )
                        VALUES (?, ?)
                        """,
                        (invoice_id, normalized)
                    )

            connection.commit()
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="该发票号码已存在，不能重复保存。"
        ) from error

    return {
        "id": invoice_id,
        "invoice_number": invoice.invoice_number,
        "payment_status": payment_status,
        "message": "发票已保存到台账。"
    }


def list_invoice_records() -> list[dict]:
    with closing(get_db_connection()) as connection:
        rows = connection.execute(
            """
            SELECT
                invoices.*,
                GROUP_CONCAT(
                    invoice_order_links.order_number
                ) AS order_numbers_text
            FROM invoices
            LEFT JOIN invoice_order_links
                ON invoices.id = invoice_order_links.invoice_id
            GROUP BY invoices.id
            ORDER BY invoices.created_at DESC
            """
        ).fetchall()

    items = []
    for row in rows:
        invoice = dict(row)
        order_numbers_text = invoice.pop(
            "order_numbers_text",
            None
        )
        invoice["order_numbers"] = (
            order_numbers_text.split(",")
            if order_numbers_text
            else []
        )
        invoice["review_notes"] = json.loads(
            invoice["review_notes"] or "[]"
        )
        invoice["raw_dify_output"] = json.loads(
            invoice["raw_dify_output"] or "{}"
        )
        items.append(invoice)
    return items


def update_invoice_record(
    invoice_id: int,
    invoice_update: InvoiceUpdate
) -> dict:
    update_data = invoice_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="请至少提交一个需要更新的字段。"
        )

    for field in {"prepayment_amount", "paid_amount"}:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} 不能设置为空。"
            )

    with closing(get_db_connection()) as connection:
        existing = connection.execute(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="未找到该发票台账。"
            )

        paid_amount = update_data.get(
            "paid_amount",
            existing["paid_amount"]
        )
        prepayment_amount = update_data.get(
            "prepayment_amount",
            existing["prepayment_amount"]
        )
        total_amount = existing["amount_incl_tax"]
        validate_payment_amounts(
            total_amount=total_amount,
            paid_amount=paid_amount,
            prepayment_amount=prepayment_amount,
            total_label="发票价税合计"
        )
        payment_status = calculate_payment_status(
            existing["document_type"],
            total_amount,
            paid_amount
        )
        update_data["payment_status"] = payment_status

        if "review_notes" in update_data:
            update_data["review_notes"] = json.dumps(
                update_data["review_notes"] or [],
                ensure_ascii=False
            )

        assignments = ", ".join(
            f"{field} = ?" for field in update_data
        )
        values = [*update_data.values(), invoice_id]
        connection.execute(
            f"""
            UPDATE invoices
            SET {assignments}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values
        )
        connection.commit()

    return {
        "id": invoice_id,
        "payment_status": payment_status,
        "message": "台账已更新。"
    }


def create_order_record(order: OrderCreate) -> dict:
    order_number = order.order_number.strip()
    if not order_number:
        raise HTTPException(
            status_code=422,
            detail="订单号不能为空。"
        )

    validate_payment_amounts(
        total_amount=order.order_amount,
        paid_amount=order.paid_amount,
        prepayment_amount=order.prepayment_amount,
        total_label="订单金额"
    )
    payment_status = calculate_payment_status(
        order.order_type,
        order.order_amount,
        order.paid_amount
    )

    try:
        with closing(get_db_connection()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO orders (
                    order_number,
                    order_type,
                    contract_number,
                    counterparty_name,
                    order_date,
                    delivery_date,
                    order_amount,
                    settlement_method,
                    payment_terms,
                    prepayment_amount,
                    paid_amount,
                    payment_status,
                    due_date,
                    owner,
                    review_status,
                    review_notes,
                    source_filename,
                    raw_dify_output
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_number,
                    order.order_type,
                    order.contract_number,
                    order.counterparty_name,
                    order.order_date,
                    order.delivery_date,
                    order.order_amount,
                    order.settlement_method,
                    order.payment_terms,
                    order.prepayment_amount,
                    order.paid_amount,
                    payment_status,
                    order.due_date,
                    order.owner,
                    order.review_status,
                    json.dumps(
                        order.review_notes,
                        ensure_ascii=False
                    ),
                    order.source_filename,
                    json.dumps(
                        order.raw_dify_output,
                        ensure_ascii=False
                    )
                )
            )
            order_id = cursor.lastrowid
            connection.commit()
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="相同类型的订单号已经存在，不能重复保存。"
        ) from error

    return {
        "id": order_id,
        "order_number": order_number,
        "payment_status": payment_status,
        "message": "订单已保存到台账。"
    }


def list_order_records() -> list[dict]:
    with closing(get_db_connection()) as connection:
        rows = connection.execute(
            """
            SELECT
                orders.*,
                GROUP_CONCAT(
                    DISTINCT invoices.invoice_number
                ) AS invoice_numbers_text
            FROM orders
            LEFT JOIN invoice_order_links
                ON invoice_order_links.order_number =
                   orders.order_number
            LEFT JOIN invoices
                ON invoices.id = invoice_order_links.invoice_id
               AND (
                    (
                        orders.order_type = '销售订单'
                        AND invoices.document_type = '销售发票'
                    )
                    OR
                    (
                        orders.order_type = '采购订单'
                        AND invoices.document_type = '采购发票'
                    )
               )
            GROUP BY orders.id
            ORDER BY orders.created_at DESC
            """
        ).fetchall()

    items = []
    for row in rows:
        order = dict(row)
        invoice_numbers_text = order.pop(
            "invoice_numbers_text",
            None
        )
        order["invoice_numbers"] = (
            invoice_numbers_text.split(",")
            if invoice_numbers_text
            else []
        )
        order["invoice_status"] = (
            "已关联发票"
            if order["invoice_numbers"]
            else "未开票"
        )
        order["review_notes"] = json.loads(
            order["review_notes"] or "[]"
        )
        order["raw_dify_output"] = json.loads(
            order["raw_dify_output"] or "{}"
        )
        items.append(order)
    return items


def update_order_record(
    order_id: int,
    order_update: OrderUpdate
) -> dict:
    update_data = order_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="请至少提交一个需要更新的字段。"
        )

    numeric_fields = {
        "order_amount",
        "prepayment_amount",
        "paid_amount"
    }
    for field in numeric_fields:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} 不能设置为空。"
            )

    with closing(get_db_connection()) as connection:
        existing = connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="未找到该订单台账。"
            )

        order_amount = update_data.get(
            "order_amount",
            existing["order_amount"]
        )
        paid_amount = update_data.get(
            "paid_amount",
            existing["paid_amount"]
        )
        prepayment_amount = update_data.get(
            "prepayment_amount",
            existing["prepayment_amount"]
        )
        validate_payment_amounts(
            total_amount=order_amount,
            paid_amount=paid_amount,
            prepayment_amount=prepayment_amount,
            total_label="订单金额"
        )
        payment_status = calculate_payment_status(
            existing["order_type"],
            order_amount,
            paid_amount
        )
        update_data["payment_status"] = payment_status

        if "review_notes" in update_data:
            update_data["review_notes"] = json.dumps(
                update_data["review_notes"] or [],
                ensure_ascii=False
            )

        assignments = ", ".join(
            f"{field} = ?" for field in update_data
        )
        values = [*update_data.values(), order_id]
        connection.execute(
            f"""
            UPDATE orders
            SET {assignments}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values
        )
        connection.commit()

    return {
        "id": order_id,
        "payment_status": payment_status,
        "message": "订单台账已更新。"
    }
def delete_invoice_record(invoice_id: int) -> dict:
    with closing(get_db_connection()) as connection:
        existing = connection.execute(
            """
            SELECT invoice_number
            FROM invoices
            WHERE id = ?
            """,
            (invoice_id,)
        ).fetchone()

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="未找到该发票台账。"
            )

        try:
            # 先删除该发票的通知去重记录
            connection.execute(
                """
                DELETE FROM notification_logs
                WHERE invoice_id = ?
                """,
                (invoice_id,)
            )

            # 再删除发票与订单的关联
            connection.execute(
                """
                DELETE FROM invoice_order_links
                WHERE invoice_id = ?
                """,
                (invoice_id,)
            )

            # 最后删除发票主记录
            connection.execute(
                """
                DELETE FROM invoices
                WHERE id = ?
                """,
                (invoice_id,)
            )

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "id": invoice_id,
        "invoice_number": existing["invoice_number"],
        "message": "发票及其关联记录已彻底删除。"
    }


def delete_order_record(order_id: int) -> dict:
    with closing(get_db_connection()) as connection:
        existing = connection.execute(
            """
            SELECT order_number, order_type
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="未找到该订单台账。"
            )

        invoice_document_type = (
            "销售发票"
            if existing["order_type"] == "销售订单"
            else "采购发票"
        )

        try:
            # 删除该订单的通知去重记录
            connection.execute(
                """
                DELETE FROM order_notification_logs
                WHERE order_id = ?
                """,
                (order_id,)
            )

            # 删除同一业务方向下的发票关联
            connection.execute(
                """
                DELETE FROM invoice_order_links
                WHERE order_number = ?
                  AND invoice_id IN (
                      SELECT id
                      FROM invoices
                      WHERE document_type = ?
                  )
                """,
                (
                    existing["order_number"],
                    invoice_document_type
                )
            )

            # 删除订单主记录
            connection.execute(
                """
                DELETE FROM orders
                WHERE id = ?
                """,
                (order_id,)
            )

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "id": order_id,
        "order_number": existing["order_number"],
        "message": "订单及其关联记录已彻底删除。"
    }