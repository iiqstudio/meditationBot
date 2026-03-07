"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from typing import Literal

from dotenv import load_dotenv


ReportPeriod = Literal["day", "week", "month"]
ReportScope = Literal["chat", "global"]


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment."""

    bot_token: str
    allowed_user_ids: tuple[int, ...]
    allowed_usernames: tuple[str, ...]
    admin_user_ids: tuple[int, ...]
    admin_usernames: tuple[str, ...]
    user_labels: dict[int, str]
    user_labels_by_username: dict[str, str]
    timezone: str
    db_path: str
    report_time: time
    report_period: ReportPeriod
    report_scope: ReportScope
    report_weekday: int
    monthly_report_enabled: bool
    monthly_report_time: time
    allow_negative_entries: bool
    max_entry_minutes: int


def _normalize_username(value: str) -> str:
    return value.strip().lstrip("@").lower()


def _parse_int_list(raw: str) -> tuple[int, ...]:
    if not raw.strip():
        return ()

    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part))
    return tuple(values)


def _parse_username_list(raw: str) -> tuple[str, ...]:
    if not raw.strip():
        return ()

    values: list[str] = []
    for part in raw.split(","):
        normalized = _normalize_username(part)
        if normalized:
            values.append(normalized)
    return tuple(values)


def _parse_user_labels(raw: str) -> dict[int, str]:
    labels: dict[int, str] = {}
    if not raw.strip():
        return labels

    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if ":" not in pair:
            raise ValueError("USER_LABELS format is invalid. Use '123:Илья,456:Настя'.")
        user_id_text, label_text = pair.split(":", 1)
        user_id = int(user_id_text.strip())
        label = label_text.strip()
        if not label:
            raise ValueError("USER_LABELS contains empty name.")
        labels[user_id] = label

    return labels


def _parse_user_labels_by_username(raw: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    if not raw.strip():
        return labels

    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if ":" not in pair:
            raise ValueError(
                "USER_LABELS_BY_USERNAME format is invalid. Use 'ilayarr:Илья,anastasiya:Настя'."
            )
        username_text, label_text = pair.split(":", 1)
        username = _normalize_username(username_text)
        label = label_text.strip()
        if not username:
            raise ValueError("USER_LABELS_BY_USERNAME contains empty username.")
        if not label:
            raise ValueError("USER_LABELS_BY_USERNAME contains empty name.")
        labels[username] = label

    return labels


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Cannot parse boolean value: {value!r}")


def _parse_time_hhmm(value: str) -> time:
    chunks = value.strip().split(":")
    if len(chunks) != 2:
        raise ValueError("AUTO_REPORT_TIME must be in HH:MM format.")
    hour = int(chunks[0])
    minute = int(chunks[1])
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("AUTO_REPORT_TIME has out-of-range values.")
    return time(hour=hour, minute=minute)


def _parse_report_period(value: str) -> ReportPeriod:
    normalized = value.strip().lower()
    if normalized not in {"day", "week", "month"}:
        raise ValueError("AUTO_REPORT_PERIOD must be one of: day, week, month.")
    return normalized  # type: ignore[return-value]


def _parse_report_scope(value: str) -> ReportScope:
    normalized = value.strip().lower()
    if normalized not in {"chat", "global"}:
        raise ValueError("REPORT_SCOPE must be one of: chat, global.")
    return normalized  # type: ignore[return-value]


def load_settings() -> Settings:
    """Load and validate settings from environment."""
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required.")

    allowed_user_ids = _parse_int_list(os.getenv("ALLOWED_USER_IDS", ""))
    allowed_usernames = _parse_username_list(os.getenv("ALLOWED_USERNAMES", ""))
    admin_user_ids = _parse_int_list(os.getenv("ADMIN_USER_IDS", ""))
    admin_usernames = _parse_username_list(os.getenv("ADMIN_USERNAMES", ""))
    user_labels = _parse_user_labels(os.getenv("USER_LABELS", ""))
    user_labels_by_username = _parse_user_labels_by_username(
        os.getenv("USER_LABELS_BY_USERNAME", "")
    )

    timezone = os.getenv("TIMEZONE", "Europe/Moscow").strip()
    db_path = os.getenv("DB_PATH", "./data/meditation.db").strip()
    if not timezone:
        raise ValueError("TIMEZONE cannot be empty.")
    if not db_path:
        raise ValueError("DB_PATH cannot be empty.")

    report_time_raw = os.getenv("AUTO_REPORT_TIME", os.getenv("DAILY_REPORT_TIME", "22:00"))
    report_time = _parse_time_hhmm(report_time_raw)

    report_period = _parse_report_period(os.getenv("AUTO_REPORT_PERIOD", "day"))
    report_scope = _parse_report_scope(os.getenv("REPORT_SCOPE", "global"))

    report_weekday_raw = os.getenv("AUTO_REPORT_WEEKDAY", "0")
    report_weekday = int(report_weekday_raw)
    if report_weekday < 0 or report_weekday > 6:
        raise ValueError("AUTO_REPORT_WEEKDAY must be between 0 (Mon) and 6 (Sun).")

    monthly_report_enabled = _parse_bool(
        os.getenv("AUTO_REPORT_MONTHLY_ENABLED", "false"),
        default=False,
    )
    monthly_report_time_raw = os.getenv("AUTO_REPORT_MONTHLY_TIME", report_time_raw)
    monthly_report_time = _parse_time_hhmm(monthly_report_time_raw)

    allow_negative_entries = _parse_bool(os.getenv("ALLOW_NEGATIVE_ENTRIES", "false"), default=False)

    max_entry_minutes_raw = os.getenv("MAX_ENTRY_MINUTES", "180")
    max_entry_minutes = int(max_entry_minutes_raw)
    if max_entry_minutes <= 0:
        raise ValueError("MAX_ENTRY_MINUTES must be > 0.")

    return Settings(
        bot_token=bot_token,
        allowed_user_ids=allowed_user_ids,
        allowed_usernames=allowed_usernames,
        admin_user_ids=admin_user_ids,
        admin_usernames=admin_usernames,
        user_labels=user_labels,
        user_labels_by_username=user_labels_by_username,
        timezone=timezone,
        db_path=db_path,
        report_time=report_time,
        report_period=report_period,
        report_scope=report_scope,
        report_weekday=report_weekday,
        monthly_report_enabled=monthly_report_enabled,
        monthly_report_time=monthly_report_time,
        allow_negative_entries=allow_negative_entries,
        max_entry_minutes=max_entry_minutes,
    )
