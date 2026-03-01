"""Date range helpers for day/week/month windows."""

from __future__ import annotations

from datetime import datetime, timedelta


def day_bounds(now: datetime) -> tuple[datetime, datetime]:
    """Return [start, end) bounds for the current day in `now` timezone."""
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def week_bounds(now: datetime) -> tuple[datetime, datetime]:
    """Return [start, end) bounds for the current week (Monday-based)."""
    day_start, _ = day_bounds(now)
    start = day_start - timedelta(days=day_start.weekday())
    end = start + timedelta(days=7)
    return start, end


def month_bounds(now: datetime) -> tuple[datetime, datetime]:
    """Return [start, end) bounds for the current month."""
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end
