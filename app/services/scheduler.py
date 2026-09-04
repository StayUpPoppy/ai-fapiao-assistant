from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import (
    ENABLE_SCHEDULER,
    REMINDER_JOB_ID,
)
from app.services.reminder_settings import (
    get_reminder_settings,
)
from app.services.reminders import (
    run_daily_dingtalk_reminders_service,
)


def apply_reminder_settings(
    scheduler: AsyncIOScheduler,
    settings: dict,
) -> str | None:
    existing_job = scheduler.get_job(REMINDER_JOB_ID)

    if not settings["enabled"]:
        if existing_job is not None:
            scheduler.remove_job(REMINDER_JOB_ID)
        return None

    scheduler.add_job(
        run_daily_dingtalk_reminders_service,
        trigger="cron",
        hour=settings["reminder_hour"],
        minute=settings["reminder_minute"],
        id=REMINDER_JOB_ID,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    job = scheduler.get_job(REMINDER_JOB_ID)

    if job is None or job.next_run_time is None:
        return None

    return job.next_run_time.isoformat()


def start_reminder_scheduler() -> AsyncIOScheduler | None:
    # .env 中的开关作为系统级总开关
    if not ENABLE_SCHEDULER:
        return None

    scheduler = AsyncIOScheduler(
        timezone="Asia/Shanghai"
    )
    scheduler.start()

    settings = get_reminder_settings()
    apply_reminder_settings(scheduler, settings)

    return scheduler