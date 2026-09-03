from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import (
    ENABLE_SCHEDULER,
    REMINDER_HOUR,
    REMINDER_JOB_ID,
    REMINDER_MINUTE
)
from app.services.reminders import (
    run_daily_dingtalk_reminders_service
)


def start_reminder_scheduler() -> AsyncIOScheduler | None:
    if not ENABLE_SCHEDULER:
        return None

    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        run_daily_dingtalk_reminders_service,
        trigger="cron",
        hour=REMINDER_HOUR,
        minute=REMINDER_MINUTE,
        id=REMINDER_JOB_ID,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600
    )
    scheduler.start()
    return scheduler
