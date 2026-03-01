"""Initialize SQLite schema for meditation tracker."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow direct execution via `python3 scripts/init_db.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bot.db.repository import MeditationRepository


async def _run() -> None:
    load_dotenv()
    db_path = os.getenv("DB_PATH", "./data/meditation.db").strip()
    if not db_path:
        raise ValueError("DB_PATH cannot be empty.")

    repository = MeditationRepository(db_path)
    await repository.init()
    print(f"Database initialized at: {db_path}")


def main() -> None:
    """Create DB tables and indices."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
