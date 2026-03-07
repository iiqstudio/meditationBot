"""Handlers for meditation minute entries like +5."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.types import Message

from src.bot.config import Settings
from src.bot.services.tracker import TrackerService, format_minutes_ru

ENTRY_RE = re.compile(r"^\s*([+-]?\d+)\s*$")


def build_entry_router(settings: Settings, tracker: TrackerService) -> Router:
    """Build router that handles numeric minute entries."""
    router = Router(name="entries")

    @router.message(F.text.regexp(ENTRY_RE))
    async def on_minutes_entry(message: Message) -> None:
        if message.from_user is None or not message.text:
            return

        user_id = message.from_user.id
        username = message.from_user.username

        if not tracker.is_allowed_user(user_id=user_id, username=username):
            await message.answer("У тебя нет доступа к этому боту.")
            return

        match = ENTRY_RE.match(message.text)
        if not match:
            return

        minutes = int(match.group(1))
        if minutes < 0 and not settings.allow_negative_entries:
            await message.answer("Отрицательные значения отключены. Используй только +N или N.")
            return

        if minutes == 0:
            await message.answer("0 минут не учитываю. Отправь число больше 0.")
            return

        if abs(minutes) > settings.max_entry_minutes:
            await message.answer(
                f"Слишком большое значение. Максимум за раз: {settings.max_entry_minutes} минут."
            )
            return

        result = await tracker.add_minutes(
            chat_id=message.chat.id,
            user_id=user_id,
            username=username,
            minutes=minutes,
        )

        label = tracker.resolve_user_label(
            user_id=user_id,
            username=username,
            fallback=message.from_user.full_name,
        )
        await message.answer(
            f"Принято: {format_minutes_ru(result.added_minutes)}.\n"
            f"{label}, сегодня: {format_minutes_ru(result.today_total)}."
        )

    return router
