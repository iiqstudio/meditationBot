"""Database models and schemas."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MeditationEntry:
    id: int
    chat_id: int
    user_id: int
    minutes: int
    created_at: datetime
