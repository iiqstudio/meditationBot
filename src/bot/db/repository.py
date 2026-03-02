"""Repository API for persistence and aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite


@dataclass(frozen=True)
class UserSummary:
    user_id: int
    minutes: int
    username: str | None


class MeditationRepository:
    """Async SQLite repository for meditation data."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def init(self) -> None:
        """Create tables and indexes if they do not exist."""
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS meditation_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    minutes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            await self._ensure_username_column(db)
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_entries_chat_created
                ON meditation_entries(chat_id, created_at)
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_entries_user_created
                ON meditation_entries(user_id, created_at)
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_kind TEXT NOT NULL,
                    period_start_utc TEXT NOT NULL,
                    sent_at_utc TEXT NOT NULL,
                    UNIQUE(report_kind, period_start_utc)
                )
                """
            )
            await db.commit()

    async def _ensure_username_column(self, db: aiosqlite.Connection) -> None:
        cursor = await db.execute("PRAGMA table_info(meditation_entries)")
        rows = await cursor.fetchall()
        columns = {str(row[1]) for row in rows}
        if "username" not in columns:
            await db.execute("ALTER TABLE meditation_entries ADD COLUMN username TEXT")

    async def add_minutes(
        self,
        chat_id: int,
        user_id: int,
        username: str | None,
        minutes: int,
        created_at_utc: datetime,
    ) -> None:
        """Insert a meditation entry."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO meditation_entries(chat_id, user_id, username, minutes, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, username, minutes, _to_utc_iso(created_at_utc)),
            )
            await db.commit()

    async def get_summary(
        self,
        start_utc: datetime,
        end_utc: datetime,
        chat_id: int | None = None,
    ) -> list[UserSummary]:
        """Return minutes grouped by user for the given [start, end) range."""
        where = ["created_at >= ?", "created_at < ?"]
        params: list[object] = [_to_utc_iso(start_utc), _to_utc_iso(end_utc)]

        if chat_id is not None:
            where.append("chat_id = ?")
            params.append(chat_id)

        query = f"""
            SELECT
                user_id,
                SUM(minutes) AS total_minutes,
                NULLIF(MAX(COALESCE(username, '')), '') AS username
            FROM meditation_entries
            WHERE {' AND '.join(where)}
            GROUP BY user_id
            ORDER BY user_id
        """

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()

        return [UserSummary(user_id=row[0], minutes=row[1], username=row[2]) for row in rows]

    async def get_user_total(
        self,
        user_id: int,
        start_utc: datetime,
        end_utc: datetime,
        chat_id: int | None = None,
    ) -> int:
        """Return aggregate minutes for a single user and [start, end) range."""
        where = ["user_id = ?", "created_at >= ?", "created_at < ?"]
        params: list[object] = [user_id, _to_utc_iso(start_utc), _to_utc_iso(end_utc)]

        if chat_id is not None:
            where.append("chat_id = ?")
            params.append(chat_id)

        query = f"""
            SELECT COALESCE(SUM(minutes), 0)
            FROM meditation_entries
            WHERE {' AND '.join(where)}
        """

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(query, tuple(params))
            row = await cursor.fetchone()

        return int(row[0]) if row else 0

    async def get_chat_ids_with_activity(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[int]:
        """Return chat ids that have at least one entry in [start, end)."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                """
                SELECT DISTINCT chat_id
                FROM meditation_entries
                WHERE created_at >= ?
                  AND created_at < ?
                ORDER BY chat_id
                """,
                (_to_utc_iso(start_utc), _to_utc_iso(end_utc)),
            )
            rows = await cursor.fetchall()

        return [int(row[0]) for row in rows]

    async def get_known_chat_ids(
        self,
        user_ids: tuple[int, ...],
        usernames: tuple[str, ...],
    ) -> list[int]:
        """Return chat ids where tracked users ever interacted with the bot."""
        where_clauses: list[str] = []
        params: list[object] = []

        if user_ids:
            placeholders = ",".join(["?"] * len(user_ids))
            where_clauses.append(f"user_id IN ({placeholders})")
            params.extend(user_ids)

        normalized_usernames = tuple(v.strip().lower() for v in usernames if v.strip())
        if normalized_usernames:
            placeholders = ",".join(["?"] * len(normalized_usernames))
            where_clauses.append(f"LOWER(COALESCE(username, '')) IN ({placeholders})")
            params.extend(normalized_usernames)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " OR ".join(where_clauses)

        query = f"""
            SELECT DISTINCT chat_id
            FROM meditation_entries
            {where_sql}
            ORDER BY chat_id
        """

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()

        return [int(row[0]) for row in rows]

    async def mark_period_report_sent(
        self,
        report_kind: str,
        period_start_utc: datetime,
    ) -> bool:
        """Mark scheduled report as sent; returns True only for first successful mark."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                """
                INSERT OR IGNORE INTO sent_reports(report_kind, period_start_utc, sent_at_utc)
                VALUES (?, ?, ?)
                """,
                (
                    report_kind,
                    _to_utc_iso(period_start_utc),
                    _to_utc_iso(datetime.now(timezone.utc)),
                ),
            )
            await db.commit()

        return cursor.rowcount > 0


def _to_utc_iso(value: datetime) -> str:
    """Normalize datetime to UTC ISO-8601 string."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()
