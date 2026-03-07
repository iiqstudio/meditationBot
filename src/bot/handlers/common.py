"""Common command handlers (e.g., /start, /help)."""

from __future__ import annotations

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, KeyboardButton, Message, ReplyKeyboardMarkup

from src.bot.services.tracker import TrackerService


def _main_keyboard() -> ReplyKeyboardMarkup:
    """Primary reply keyboard with quick actions."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="+5"), KeyboardButton(text="+10")],
            [KeyboardButton(text="+15"), KeyboardButton(text="+30")],
            [
                KeyboardButton(text="/day"),
                KeyboardButton(text="/week"),
                KeyboardButton(text="/month"),
            ],
            [KeyboardButton(text="/year"), KeyboardButton(text="/export_year")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def build_common_router(tracker: TrackerService) -> Router:
    """Build router with service commands."""
    router = Router(name="common")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        help_text = (
            "Привет! Я считаю минуты медитации.\n\n"
            "Отправляй `+5`, `+15` или просто `10`.\n"
            "Можно пользоваться кнопками снизу.\n"
            "Команды:\n"
            "/day - итоги за день\n"
            "/week - итоги за неделю\n"
            "/month - итоги за месяц\n"
            "/year - итоги за год\n"
            "/export_year - скачать CSV за год"
        )
        await message.answer(help_text, reply_markup=_main_keyboard())

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

    @router.message(Command("year"))
    async def on_year(message: Message) -> None:
        if message.from_user and not tracker.is_allowed_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
        ):
            await message.answer("У тебя нет доступа к этому боту.")
            return
        report = await tracker.get_yearly_text_report(chat_id=message.chat.id)
        await message.answer(report)

    @router.message(Command("export_year"))
    async def on_export_year(message: Message) -> None:
        if message.from_user and not tracker.is_allowed_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
        ):
            await message.answer("У тебя нет доступа к этому боту.")
            return

        csv_bytes = await tracker.get_year_csv(chat_id=message.chat.id)
        year = datetime.now().year
        filename = f"meditation_year_{year}.csv"
        await message.answer_document(
            BufferedInputFile(csv_bytes, filename=filename),
            caption=f"Экспорт за {year} год.",
        )

    return router
