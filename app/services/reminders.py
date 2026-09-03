from contextlib import closing
from datetime import date

from app.database import get_db_connection
from app.services.dingtalk import send_dingtalk_text
from app.services.ledger import (
    list_invoice_records,
    list_order_records
)


def validate_reminder_range(days_before: int) -> None:
    if days_before < 0 or days_before > 90:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail="days_before 必须在 0 到 90 之间。"
        )


def reminder_status(
    due_date_value: date,
    days_before: int
) -> tuple[str, int] | None:
    days_to_due = (due_date_value - date.today()).days
    if days_to_due < 0:
        return "已逾期", days_to_due
    if days_to_due == 0:
        return "今日到期", days_to_due
    if days_to_due <= days_before:
        return "即将到期", days_to_due
    return None


def get_invoice_due_reminders(days_before: int) -> list[dict]:
    reminders = []

    for invoice in list_invoice_records():
        if not invoice["due_date"]:
            continue
        try:
            due_date_value = date.fromisoformat(
                invoice["due_date"]
            )
        except ValueError:
            continue

        amount_due = round(
            max(
                0,
                invoice["amount_incl_tax"]
                - invoice["paid_amount"]
            ),
            2
        )
        if amount_due <= 0.01:
            continue

        status = reminder_status(
            due_date_value,
            days_before
        )
        if status is None:
            continue
        status_name, days_to_due = status

        counterparty = (
            invoice["buyer_name"]
            if invoice["document_type"] == "销售发票"
            else invoice["seller_name"]
        )
        reminders.append({
            "source_type": "invoice",
            "invoice_id": invoice["id"],
            "invoice_number": invoice["invoice_number"],
            "document_type": invoice["document_type"],
            "order_numbers": invoice["order_numbers"],
            "counterparty": counterparty,
            "due_date": invoice["due_date"],
            "days_to_due": days_to_due,
            "amount_due": amount_due,
            "payment_status": invoice["payment_status"],
            "owner": invoice["owner"],
            "reminder_status": status_name
        })

    return sorted(
        reminders,
        key=lambda item: item["days_to_due"]
    )


def get_order_due_reminders(days_before: int) -> list[dict]:
    reminders = []

    for order in list_order_records():
        if not order["due_date"]:
            continue
        try:
            due_date_value = date.fromisoformat(order["due_date"])
        except ValueError:
            continue

        amount_due = round(
            max(
                0,
                order["order_amount"] - order["paid_amount"]
            ),
            2
        )
        if amount_due <= 0.01:
            continue

        status = reminder_status(
            due_date_value,
            days_before
        )
        if status is None:
            continue
        status_name, days_to_due = status

        reminders.append({
            "source_type": "order",
            "order_id": order["id"],
            "order_number": order["order_number"],
            "order_type": order["order_type"],
            "counterparty": order["counterparty_name"],
            "due_date": order["due_date"],
            "days_to_due": days_to_due,
            "amount_due": amount_due,
            "payment_status": order["payment_status"],
            "owner": order["owner"],
            "reminder_status": status_name
        })

    return sorted(
        reminders,
        key=lambda item: item["days_to_due"]
    )


def get_combined_due_reminders(days_before: int) -> list[dict]:
    invoice_reminders = get_invoice_due_reminders(days_before)
    order_reminders = get_order_due_reminders(days_before)
    covered_orders = set()

    for reminder in invoice_reminders:
        if reminder["document_type"] == "销售发票":
            matching_order_type = "销售订单"
        elif reminder["document_type"] == "采购发票":
            matching_order_type = "采购订单"
        else:
            continue

        for order_number in reminder.get("order_numbers", []):
            covered_orders.add(
                (matching_order_type, order_number)
            )

    filtered_orders = [
        reminder
        for reminder in order_reminders
        if (
            reminder["order_type"],
            reminder["order_number"]
        ) not in covered_orders
    ]
    return sorted(
        invoice_reminders + filtered_orders,
        key=lambda item: item["days_to_due"]
    )


def get_notification_event_key(
    reminder: dict
) -> str | None:
    days_to_due = reminder["days_to_due"]
    due_date_value = reminder["due_date"]

    if 4 <= days_to_due <= 7:
        return f"{due_date_value}:D7"
    if 1 <= days_to_due <= 3:
        return f"{due_date_value}:D3"
    if days_to_due == 0:
        return f"{due_date_value}:D0"
    if days_to_due < 0:
        return (
            f"{due_date_value}:OVERDUE:"
            f"{date.today().isoformat()}"
        )
    return None


def get_unsent_dingtalk_reminders(
    reminders: list[dict]
) -> list[dict]:
    unsent = []
    with closing(get_db_connection()) as connection:
        for reminder in reminders:
            event_key = get_notification_event_key(reminder)
            if event_key is None:
                continue

            if reminder["source_type"] == "invoice":
                existing = connection.execute(
                    """
                    SELECT id FROM notification_logs
                    WHERE invoice_id = ?
                      AND channel = ?
                      AND event_key = ?
                    """,
                    (
                        reminder["invoice_id"],
                        "dingtalk",
                        event_key
                    )
                ).fetchone()
            elif reminder["source_type"] == "order":
                existing = connection.execute(
                    """
                    SELECT id FROM order_notification_logs
                    WHERE order_id = ?
                      AND channel = ?
                      AND event_key = ?
                    """,
                    (
                        reminder["order_id"],
                        "dingtalk",
                        event_key
                    )
                ).fetchone()
            else:
                continue

            if existing is None:
                item = dict(reminder)
                item["event_key"] = event_key
                unsent.append(item)
    return unsent


def record_dingtalk_notifications(
    reminders: list[dict]
) -> None:
    with closing(get_db_connection()) as connection:
        for reminder in reminders:
            if reminder["source_type"] == "invoice":
                connection.execute(
                    """
                    INSERT OR IGNORE INTO notification_logs (
                        invoice_id,
                        channel,
                        event_key,
                        reminder_status,
                        due_date
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        reminder["invoice_id"],
                        "dingtalk",
                        reminder["event_key"],
                        reminder["reminder_status"],
                        reminder["due_date"]
                    )
                )
            elif reminder["source_type"] == "order":
                connection.execute(
                    """
                    INSERT OR IGNORE INTO order_notification_logs (
                        order_id,
                        channel,
                        event_key,
                        reminder_status,
                        due_date
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        reminder["order_id"],
                        "dingtalk",
                        reminder["event_key"],
                        reminder["reminder_status"],
                        reminder["due_date"]
                    )
                )
        connection.commit()


def build_due_reminder_message(reminders: list[dict]) -> str:
    lines = [
        "【供应链账期提醒】",
        f"统计日期：{date.today().isoformat()}",
        f"待跟进单据：{len(reminders)} 笔",
        ""
    ]

    for index, item in enumerate(reminders, start=1):
        days_to_due = item["days_to_due"]
        if days_to_due < 0:
            time_description = f"已逾期 {abs(days_to_due)} 天"
        elif days_to_due == 0:
            time_description = "今日到期"
        else:
            time_description = f"剩余 {days_to_due} 天"

        if item["source_type"] == "invoice":
            document_type = item["document_type"]
            number_label = "发票号码"
            document_number = item["invoice_number"]
            order_numbers = item.get("order_numbers", [])
        else:
            document_type = item["order_type"]
            number_label = "订单号码"
            document_number = item["order_number"]
            order_numbers = []

        amount_label = (
            "待收款"
            if document_type in {"销售发票", "销售订单"}
            else "待付款"
        )
        lines.extend([
            (
                f"{index}. {item['reminder_status']}｜"
                f"{document_type}"
            ),
            f"往来单位：{item['counterparty'] or '待确认'}",
            f"{number_label}：{document_number}",
            (
                f"到期日期：{item['due_date']}"
                f"（{time_description}）"
            ),
            f"{amount_label}：¥{item['amount_due']:,.2f}",
            f"负责人：{item['owner'] or '待分配'}"
        ])
        if order_numbers:
            lines.append("关联订单：" + "、".join(order_numbers))
        lines.append("")

    lines.append("请相关负责人及时跟进并更新台账。")
    return "\n".join(lines)


async def run_daily_dingtalk_reminders_service() -> dict:
    reminders = get_combined_due_reminders(days_before=7)
    unsent = get_unsent_dingtalk_reminders(reminders)
    if not unsent:
        return {
            "status": "skipped",
            "sent_count": 0,
            "message": "今天没有新的账期提醒需要发送。"
        }

    content = build_due_reminder_message(unsent)
    dingtalk_result = await send_dingtalk_text(content)
    record_dingtalk_notifications(unsent)
    return {
        "status": "sent",
        "sent_count": len(unsent),
        "message": "今日账期提醒已发送。",
        "dingtalk_response": dingtalk_result
    }
