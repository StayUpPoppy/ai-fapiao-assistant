from contextlib import closing

from app.database import get_db_connection


def get_reminder_settings() -> dict:
    with closing(get_db_connection()) as connection:
        row = connection.execute(
            """
            SELECT
                enabled,
                reminder_hour,
                reminder_minute,
                days_before,
                updated_at
            FROM reminder_settings
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        raise RuntimeError("提醒设置尚未初始化。")

    return {
        "enabled": bool(row["enabled"]),
        "reminder_hour": row["reminder_hour"],
        "reminder_minute": row["reminder_minute"],
        "days_before": row["days_before"],
        "updated_at": row["updated_at"],
    }


def update_reminder_settings(
    enabled: bool,
    reminder_hour: int,
    reminder_minute: int,
    days_before: int,
) -> dict:
    if not 0 <= reminder_hour <= 23:
        raise ValueError("提醒小时必须在 0 到 23 之间。")

    if not 0 <= reminder_minute <= 59:
        raise ValueError("提醒分钟必须在 0 到 59 之间。")

    if not 0 <= days_before <= 365:
        raise ValueError("提前提醒天数必须在 0 到 365 之间。")

    with closing(get_db_connection()) as connection:
        connection.execute(
            """
            INSERT INTO reminder_settings (
                id,
                enabled,
                reminder_hour,
                reminder_minute,
                days_before,
                updated_at
            )
            VALUES (1, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                enabled = excluded.enabled,
                reminder_hour = excluded.reminder_hour,
                reminder_minute = excluded.reminder_minute,
                days_before = excluded.days_before,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                int(enabled),
                reminder_hour,
                reminder_minute,
                days_before,
            ),
        )
        connection.commit()

    return get_reminder_settings()