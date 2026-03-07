"""Entry point for Telegram meditation tracker bot."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest

from src.bot.config import ReportPeriod, Settings, load_settings
from src.bot.db.repository import MeditationRepository
from src.bot.handlers.common import build_common_router
from src.bot.handlers.entries import build_entry_router
from src.bot.logging_setup import setup_logging
from src.bot.services.tracker import TrackerService

logger = logging.getLogger(__name__)


async def _auto_report_loop(
    bot: Bot,
    tracker: TrackerService,
    *,
    timezone_name: str,
    period: ReportPeriod,
    run_time_hour: int,
    run_time_minute: int,
    weekly_weekday: int,
) -> None:
    """Send periodic summary to recipient chats."""
    tz = ZoneInfo(timezone_name)
    period_offset = _scheduled_period_offset(period)

    # Catch up if the bot starts later on the exact scheduled day.
    now_local = datetime.now(tz)
    if _should_catch_up_on_start(
        now_local=now_local,
        period=period,
        run_hour=run_time_hour,
        run_minute=run_time_minute,
        weekly_weekday=weekly_weekday,
    ):
        await _send_scheduled_report(bot=bot, tracker=tracker, period=period, period_offset=period_offset)

    while True:
        now_local = datetime.now(tz)
        target_local = _next_run_datetime(
            now_local=now_local,
            period=period,
            run_hour=run_time_hour,
            run_minute=run_time_minute,
            weekly_weekday=weekly_weekday,
        )

        wait_seconds = (target_local - now_local).total_seconds()
        await asyncio.sleep(wait_seconds)

        await _send_scheduled_report(bot=bot, tracker=tracker, period=period, period_offset=period_offset)


async def _send_scheduled_report(
    bot: Bot,
    tracker: TrackerService,
    period: ReportPeriod,
    period_offset: int,
) -> None:
    """Send one scheduled report batch once per period window."""
    chat_ids = await tracker.get_recipient_chat_ids(period=period, offset=period_offset)
    if not chat_ids:
        logger.info("Auto-report skipped: no recipient chats for period=%s", period)
        return

    is_new_period = await tracker.mark_period_report_sent_if_new(period=period, offset=period_offset)
    if not is_new_period:
        logger.info(
            "Auto-report skipped: period=%s offset=%s already sent",
            period,
            period_offset,
        )
        return

    for chat_id in chat_ids:
        try:
            report = await tracker.get_period_text_report(
                chat_id=chat_id,
                period=period,
                offset=period_offset,
            )
            await bot.send_message(chat_id=chat_id, text=report)
        except TelegramBadRequest:
            logger.exception("Failed to send auto-report to chat_id=%s", chat_id)
        except Exception:
            logger.exception("Unexpected error while sending auto-report")


def _scheduled_period_offset(period: ReportPeriod) -> int:
    """For weekly/monthly schedules send closed previous period."""
    if period in {"week", "month"}:
        return 1
    return 0


def _should_catch_up_on_start(
    now_local: datetime,
    period: ReportPeriod,
    run_hour: int,
    run_minute: int,
    weekly_weekday: int,
) -> bool:
    """Catch missed schedule when service starts later on the schedule day."""
    scheduled_today = now_local.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
    if now_local < scheduled_today:
        return False

    if period == "day":
        return True
    if period == "week":
        return now_local.weekday() == weekly_weekday
    return now_local.day == 1


def _next_run_datetime(
    now_local: datetime,
    period: ReportPeriod,
    run_hour: int,
    run_minute: int,
    weekly_weekday: int,
) -> datetime:
    """Calculate next trigger timestamp in local timezone."""
    candidate = now_local.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)

    if period == "day":
        if candidate <= now_local:
            candidate += timedelta(days=1)
        return candidate

    if period == "week":
        days_ahead = (weekly_weekday - now_local.weekday()) % 7
        candidate += timedelta(days=days_ahead)
        if candidate <= now_local:
            candidate += timedelta(days=7)
        return candidate

    # month: first day of month at run time
    candidate = candidate.replace(day=1)
    if candidate <= now_local:
        year = candidate.year + (1 if candidate.month == 12 else 0)
        month = 1 if candidate.month == 12 else candidate.month + 1
        candidate = candidate.replace(year=year, month=month)
    return candidate


async def _run() -> None:
    settings = load_settings()
    setup_logging()

    repository = MeditationRepository(settings.db_path)
    await repository.init()

    tracker = TrackerService(
        repository=repository,
        timezone_name=settings.timezone,
        tracked_user_ids=settings.allowed_user_ids,
        tracked_usernames=settings.allowed_usernames,
        admin_user_ids=settings.admin_user_ids,
        admin_usernames=settings.admin_usernames,
        user_labels=settings.user_labels,
        user_labels_by_username=settings.user_labels_by_username,
        max_entry_minutes=settings.max_entry_minutes,
        report_scope=settings.report_scope,
    )

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(build_common_router(tracker))
    dp.include_router(build_entry_router(settings, tracker))

    report_tasks: list[asyncio.Task[None]] = []

    async def _startup(bot: Bot) -> None:
        nonlocal report_tasks
        logger.info(
            "Bot startup complete. Primary auto-report: period=%s, scope=%s, time=%s, weekday=%s",
            settings.report_period,
            settings.report_scope,
            settings.report_time,
            settings.report_weekday,
        )
        report_tasks.append(
            asyncio.create_task(
                _auto_report_loop(
                    bot=bot,
                    tracker=tracker,
                    timezone_name=settings.timezone,
                    period=settings.report_period,
                    run_time_hour=settings.report_time.hour,
                    run_time_minute=settings.report_time.minute,
                    weekly_weekday=settings.report_weekday,
                )
            )
        )

        if settings.monthly_report_enabled and settings.report_period != "month":
            logger.info(
                "Monthly auto-report enabled: period=month, time=%s",
                settings.monthly_report_time,
            )
            report_tasks.append(
                asyncio.create_task(
                    _auto_report_loop(
                        bot=bot,
                        tracker=tracker,
                        timezone_name=settings.timezone,
                        period="month",
                        run_time_hour=settings.monthly_report_time.hour,
                        run_time_minute=settings.monthly_report_time.minute,
                        weekly_weekday=0,
                    )
                )
            )

    async def _shutdown(bot: Bot) -> None:
        nonlocal report_tasks
        for report_task in report_tasks:
            report_task.cancel()
        for report_task in report_tasks:
            try:
                await report_task
            except asyncio.CancelledError:
                pass

    dp.startup.register(_startup)
    dp.shutdown.register(_shutdown)

    await dp.start_polling(bot)


def main() -> None:
    """Run bot application."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
