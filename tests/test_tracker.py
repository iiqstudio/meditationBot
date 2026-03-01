"""Tests for tracker utility date ranges."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.bot.utils.date_ranges import day_bounds, month_bounds, week_bounds


def test_day_bounds() -> None:
    now = datetime(2026, 3, 1, 15, 42, tzinfo=ZoneInfo("Europe/Moscow"))
    start, end = day_bounds(now)
    assert start.hour == 0
    assert start.minute == 0
    assert (end - start).days == 1


def test_week_bounds_starts_on_monday() -> None:
    now = datetime(2026, 3, 1, 15, 42, tzinfo=ZoneInfo("Europe/Moscow"))  # Sunday
    start, end = week_bounds(now)
    assert start.weekday() == 0
    assert (end - start).days == 7


def test_month_bounds() -> None:
    now = datetime(2026, 12, 31, 23, 59, tzinfo=ZoneInfo("Europe/Moscow"))
    start, end = month_bounds(now)
    assert start.day == 1
    assert start.month == 12
    assert end.month == 1
    assert end.year == 2027
