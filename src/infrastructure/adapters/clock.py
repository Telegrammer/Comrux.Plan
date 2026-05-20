from datetime import UTC, datetime


class TimestampClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)
