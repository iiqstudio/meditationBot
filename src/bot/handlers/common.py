"""Common command handlers (e.g., /start, /help)."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.bot.services.tracker import TrackerService


def build_common_router(tracker: TrackerService) -> Router:
    """Build router with service commands."""
    router = Router(name="common")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        help_text = (
            "Привет! Я считаю минуты медитации.\n\n"
            "Отправляй `+5`, `+15` или просто `10`.\n"
            "Команды:\n"
            "/day - итоги за день\n"
            "/week - итоги за неделю\n"
            "/month - итоги за месяц"
        )
        await message.answer(help_text)

    @router.message(Command("help"))
    async def on_help(message: Message) -> None:
        await on_start(message)

    @router.message(Command("day"))
    async def on_day(message: Message) -> None:
        if message.from_user and not tracker.is_allowed_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
        ):
            await message.answer("У тебя нет доступа к этому боту.")
            return
        report = await tracker.get_daily_text_report(chat_id=message.chat.id)
        await message.answer(report)

    @router.message(Command("week"))
    async def on_week(message: Message) -> None:
        if message.from_user and not tracker.is_allowed_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
        ):
            await message.answer("У тебя нет доступа к этому боту.")
            return
        report = await tracker.get_weekly_text_report(chat_id=message.chat.id)
        await message.answer(report)

    @router.message(Command("month"))
    async def on_month(message: Message) -> None:
        if message.from_user and not tracker.is_allowed_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
        ):
            await message.answer("У тебя нет доступа к этому боту.")
            return
        report = await tracker.get_monthly_text_report(chat_id=message.chat.id)
        await message.answer(report)

    return router
