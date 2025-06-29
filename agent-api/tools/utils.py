from datetime import datetime
from dateutil.relativedelta import relativedelta

class TimeConverter:
    @staticmethod
    def timestamp_ms_to_datetime(timestamp_ms: int) -> datetime:
        """Convert timestamp in milliseconds to datetime."""
        return datetime.fromtimestamp(timestamp_ms / 1000)

    @staticmethod
    def datetime_to_timestamp_ms(dt: datetime) -> int:
        """Convert datetime to timestamp in milliseconds."""
        return int(dt.timestamp() * 1000)

    @staticmethod
    def get_one_month_before(now: datetime = None) -> datetime:
        """
        Get the datetime of one month before the given time (or now if not provided).
        """
        if now is None:
            now = datetime.now()
        return now - relativedelta(days=1)

    @staticmethod
    def get_one_month_after(now: datetime = None) -> datetime:
        """
        Get the datetime of one month after the given time (or now if not provided).
        """
        if now is None:
            now = datetime.now()
        return now + relativedelta(days=1)
        