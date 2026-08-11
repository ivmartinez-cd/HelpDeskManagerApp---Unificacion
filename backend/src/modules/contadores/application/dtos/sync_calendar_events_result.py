from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class SyncCalendarEventsResult:
    operadores_count: int
    events_count: int
    range_start: str
    range_end: str
    synced_at: datetime
