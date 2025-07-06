from datetime import datetime
from dateutil.relativedelta import relativedelta

class TimeConverter:
    def __init__(self):
        pass
    
    # @staticmethod
    def timestamp_ms_to_datetime(self, timestamp_ms: int) -> datetime:
        """
        Convert a timestamp in milliseconds to a human-readable datetime string in 'YYYY-MM-DD HH:MM:SS' format.

        Args:
            timestamp_ms (int): Timestamp value in milliseconds.

        Returns:
            str: Datetime string in 'YYYY-MM-DD HH:MM:SS' format.
        """
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    # @staticmethod
    def datetime_to_timestamp_ms(self, dt: datetime) -> int:
        """
        Convert a datetime object to a timestamp in milliseconds.

        Args:
            dt (datetime): Datetime object to convert.

        Returns:
            int: Timestamp value in milliseconds.
        """
        return int(dt.timestamp() * 1000)

    def get_now_datetime(self) -> datetime:
        """
        Get the current time as a datetime object.

        Returns:
            datetime: Current time.
        """
        return datetime.now()
    
    # @staticmethod
    def get_other_days(self, days: int = 1) -> datetime:
        """
        Get a datetime value representing a number of days before or after the current time.

        Args:
            days (int): Number of days to add to the current time. Positive for future dates, negative for past dates.

        Returns:
            datetime: Datetime value representing the current time plus the specified number of days.
        """
        now = self.get_now_datetime()
        return now + relativedelta(days=days)
