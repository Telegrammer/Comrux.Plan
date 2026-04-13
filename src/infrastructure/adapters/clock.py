from datetime import datetime


class TimestampClock:
    def now(self) -> datetime:
        return datetime.now(tz=None)
