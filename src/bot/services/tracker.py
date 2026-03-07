"""Meditation tracking service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from src.bot.db.repository import MeditationRepository
from src.bot.utils.date_ranges import day_bounds, week_bounds

Period = Literal["day", "week", "month"]
ReportScope = Literal["chat", "global"]


@dataclass(frozen=True)
class AddMinutesResult:
    user_id: int
    added_minutes: int
    today_total: int


class TrackerService:
    """Domain operations for adding entries and reading summaries."""

    def __init__(
        self,
        repository: MeditationRepository,
        timezone_name: str,
        tracked_user_ids: tuple[int, ...],
        tracked_usernames: tuple[str, ...],
        user_labels: dict[int, str],
        user_labels_by_username: dict[str, str],
        max_entry_minutes: int,
        report_scope: ReportScope,
    ) -> None:
        self._repository = repository
        self._tz = ZoneInfo(timezone_name)
        self._tracked_user_ids = tracked_user_ids
        self._tracked_usernames = tuple(self._normalize_username(v) for v in tracked_usernames)
        self._user_labels = user_labels
        self._user_labels_by_username = {
            self._normalize_username(k): v for k, v in user_labels_by_username.items()
        }
        self._max_entry_minutes = max_entry_minutes
        self._report_scope = report_scope

    def is_allowed_user(self, user_id: int, username: str | None = None) -> bool:
        """Check if user can submit entries."""
        has_id_rules = bool(self._tracked_user_ids)
        has_username_rules = bool(self._tracked_usernames)

        if not has_id_rules and not has_username_rules:
            return True

        if has_id_rules and user_id in self._tracked_user_ids:
            return True

        if has_username_rules and username:
            normalized = self._normalize_username(username)
            return normalized in self._tracked_usernames

        return False

    def resolve_user_label(
        self,
        user_id: int,
        username: str | None = None,
        fallback: str | None = None,
    ) -> str:
        """Return display name for user in reports and replies."""
        if user_id in self._user_labels:
            return self._user_labels[user_id]

        if username:
            normalized = self._normalize_username(username)
            if normalized in self._user_labels_by_username:
                return self._user_labels_by_username[normalized]
            return f"@{normalized}"

        if fallback:
            return fallback
        return f"User {user_id}"

    async def add_minutes(
        self,
        chat_id: int,
        user_id: int,
        username: str | None,
        minutes: int,
    ) -> AddMinutesResult:
        """Store entry and return fresh daily total for user."""
        if minutes == 0:
            raise ValueError("Minutes cannot be 0.")
        if abs(minutes) > self._max_entry_minutes:
            raise ValueError(f"Single entry cannot exceed {self._max_entry_minutes} minutes.")

        now_utc = datetime.now(timezone.utc)
        await self._repository.add_minutes(chat_id, user_id, username, minutes, now_utc)

        start_utc, end_utc = self.get_period_bounds_utc("day", offset=0, now_utc=now_utc)
        today_total = await self._repository.get_user_total(
            user_id=user_id,
            start_utc=start_utc,
            end_utc=end_utc,
            chat_id=self._scope_chat_id(chat_id),
        )
        return AddMinutesResult(user_id=user_id, added_minutes=minutes, today_total=today_total)

    async def get_daily_text_report(self, chat_id: int, offset_days: int = 0) -> str:
        return await self.get_period_text_report(chat_id=chat_id, period="day", offset=offset_days)

    async def get_weekly_text_report(self, chat_id: int, offset_weeks: int = 0) -> str:
        return await self.get_period_text_report(chat_id=chat_id, period="week", offset=offset_weeks)

    async def get_monthly_text_report(self, chat_id: int, offset_months: int = 0) -> str:
        return await self.get_period_text_report(chat_id=chat_id, period="month", offset=offset_months)

    async def get_period_text_report(self, chat_id: int, period: Period, offset: int = 0) -> str:
        return await self._period_text_report(chat_id=chat_id, period=period, offset=offset)

    async def get_recipient_chat_ids(self, period: Period, offset: int = 0) -> list[int]:
        """Return recipient chats for scheduled reports."""
        if self._report_scope == "global":
            known_chat_ids = await self._repository.get_known_chat_ids(
                user_ids=self._tracked_user_ids,
                usernames=self._tracked_usernames,
            )
            if known_chat_ids:
                return known_chat_ids

        now_utc = datetime.now(timezone.utc)
        start_utc, end_utc = self.get_period_bounds_utc(period, offset=offset, now_utc=now_utc)
        return await self._repository.get_chat_ids_with_activity(start_utc=start_utc, end_utc=end_utc)

    async def mark_period_report_sent_if_new(self, period: Period, offset: int = 0) -> bool:
        """Return True only if this period report was not sent before."""
        start_utc, _ = self.get_period_bounds_utc(period=period, offset=offset)
        return await self._repository.mark_period_report_sent(
            report_kind=period,
            period_start_utc=start_utc,
        )

    def get_period_bounds_utc(
        self,
        period: Period,
        offset: int,
        now_utc: datetime | None = None,
    ) -> tuple[datetime, datetime]:
        """Public period bounds helper used by reporting and scheduler."""
        base_utc = now_utc or datetime.now(timezone.utc)
        return self._period_bounds_utc(period=period, now_utc=base_utc, offset=offset)

    async def _period_text_report(self, chat_id: int, period: Period, offset: int) -> str:
        now_utc = datetime.now(timezone.utc)
        start_utc, end_utc = self._period_bounds_utc(period, now_utc, offset=offset)
        rows = await self._repository.get_summary(
            start_utc=start_utc,
            end_utc=end_utc,
            chat_id=self._scope_chat_id(chat_id),
        )

        totals = {row.user_id: row.minutes for row in rows}
        usernames_by_id = {row.user_id: row.username for row in rows}
        ordered_user_ids = self._ordered_user_ids(totals, usernames_by_id)

        if not ordered_user_ids:
            period_name = _period_title(period, offset)
            return f"Пока нет записей за {period_name}."

        lines = [f"Итоги за {_period_title(period, offset)}:"]
        for user_id in ordered_user_ids:
            label = self.resolve_user_label(user_id=user_id, username=usernames_by_id.get(user_id))
            minutes = totals.get(user_id, 0)
            lines.append(f"{label}: {format_minutes_ru(minutes)}!")

        return "\n".join(lines)

    def _ordered_user_ids(self, totals: dict[int, int], usernames_by_id: dict[int, str | None]) -> list[int]:
        if self._tracked_user_ids:
            user_ids = list(self._tracked_user_ids)
            for user_id in sorted(totals):
                if user_id not in self._tracked_user_ids:
                    user_ids.append(user_id)
            return user_ids

        return sorted(
            totals.keys(),
            key=lambda user_id: self.resolve_user_label(
                user_id=user_id,
                username=usernames_by_id.get(user_id),
                fallback=str(user_id),
            ).lower(),
        )

    def _period_bounds_utc(
        self,
        period: Period,
        now_utc: datetime,
        offset: int,
    ) -> tuple[datetime, datetime]:
        now_local = now_utc.astimezone(self._tz)

        if period == "day":
            target_local = now_local - timedelta(days=offset)
            start_local, end_local = day_bounds(target_local)
        elif period == "week":
            target_local = now_local - timedelta(weeks=offset)
            start_local, end_local = week_bounds(target_local)
        else:
            start_local, end_local = _month_bounds_with_offset(now_local, offset)

        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    def _scope_chat_id(self, chat_id: int) -> int | None:
        if self._report_scope == "chat":
            return chat_id
        return None

    @staticmethod
    def _normalize_username(value: str) -> str:
        return value.strip().lstrip("@").lower()


def _period_title(period: Period, offset: int) -> str:
    if period == "day":
        return "день" if offset == 0 else "предыдущий день"
    if period == "week":
        return "неделю" if offset == 0 else "предыдущую неделю"
    return "месяц" if offset == 0 else "предыдущий месяц"


def format_minutes_ru(total_minutes: int) -> str:
    """Format minutes as readable RU duration, e.g. 65 -> '1 ч. 5 мин.'."""
    sign = "-" if total_minutes < 0 else ""
    value = abs(total_minutes)
    hours, minutes = divmod(value, 60)

    if hours and minutes:
        return f"{sign}{hours} ч. {minutes} мин."
    if hours:
        return f"{sign}{hours} ч."
    return f"{sign}{minutes} мин."


def _month_bounds_with_offset(now_local: datetime, offset: int) -> tuple[datetime, datetime]:
    now_start = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    current_total = now_start.year * 12 + (now_start.month - 1)
    target_total = current_total - offset
    next_total = target_total + 1

    target_year = target_total // 12
    target_month = (target_total % 12) + 1

    next_year = next_total // 12
    next_month = (next_total % 12) + 1

    start = now_start.replace(year=target_year, month=target_month)
    end = now_start.replace(year=next_year, month=next_month)
    return start, end
