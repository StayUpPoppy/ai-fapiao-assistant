from datetime import date

from fastapi import APIRouter, Request

from app.config import REMINDER_JOB_ID
from app.services.dingtalk import send_dingtalk_text
from app.services.reminders import (
    build_due_reminder_message,
    get_combined_due_reminders,
    get_invoice_due_reminders,
    get_order_due_reminders,
    run_daily_dingtalk_reminders_service,
    validate_reminder_range
)


router = APIRouter(tags=["账期提醒"])


@router.get("/api/reminders/all/due")
def list_all_due_reminders(days_before: int = 7):
    validate_reminder_range(days_before)
    invoice_reminders = get_invoice_due_reminders(days_before)
    order_reminders = get_order_due_reminders(days_before)
    combined = get_combined_due_reminders(days_before)
    return {
        "today": date.today().isoformat(),
        "days_before": days_before,
        "invoice_total_before_dedup": len(invoice_reminders),
        "order_total_before_dedup": len(order_reminders),
        "suppressed_duplicate_total": (
            len(invoice_reminders)
            + len(order_reminders)
            - len(combined)
        ),
        "total": len(combined),
        "items": combined
    }


@router.get("/api/reminders/due")
def list_due_reminders(days_before: int = 7):
    validate_reminder_range(days_before)
    reminders = get_invoice_due_reminders(days_before)
    return {
        "today": date.today().isoformat(),
        "days_before": days_before,
        "total": len(reminders),
        "items": reminders
    }


@router.get("/api/reminders/orders/due")
def list_order_due_reminders(days_before: int = 7):
    validate_reminder_range(days_before)
    reminders = get_order_due_reminders(days_before)
    return {
        "today": date.today().isoformat(),
        "days_before": days_before,
        "total": len(reminders),
        "items": reminders
    }


@router.post("/api/notifications/dingtalk/test")
async def test_dingtalk_notification():
    content = (
        "【供应链台账助手】钉钉通知测试\n"
        f"测试日期：{date.today().isoformat()}\n"
        "状态：Webhook 与加签配置正常。"
    )
    result = await send_dingtalk_text(content)
    return {
        "status": "sent",
        "message": "钉钉测试消息已发送。",
        "dingtalk_response": result
    }


@router.post("/api/notifications/dingtalk/reminders")
async def send_due_reminder_notification(
    days_before: int = 7
):
    validate_reminder_range(days_before)
    reminders = get_combined_due_reminders(days_before)
    if not reminders:
        return {
            "status": "skipped",
            "sent_count": 0,
            "message": "当前范围内没有需要提醒的未结清单据。"
        }

    content = build_due_reminder_message(reminders)
    result = await send_dingtalk_text(content)
    return {
        "status": "sent",
        "sent_count": len(reminders),
        "message": "账期提醒已发送到钉钉群。",
        "dingtalk_response": result
    }


@router.post("/api/notifications/dingtalk/run-daily")
async def run_daily_dingtalk_reminders():
    return await run_daily_dingtalk_reminders_service()


@router.get("/api/scheduler/status")
def get_scheduler_status(request: Request):
    scheduler = getattr(
        request.app.state,
        "reminder_scheduler",
        None
    )
    if scheduler is None:
        return {
            "running": False,
            "message": "提醒调度器尚未启动。"
        }

    job = scheduler.get_job(REMINDER_JOB_ID)
    return {
        "running": scheduler.running,
        "job_id": REMINDER_JOB_ID,
        "next_run_time": (
            job.next_run_time.isoformat()
            if job and job.next_run_time
            else None
        )
    }
