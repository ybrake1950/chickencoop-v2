"""
Time utilities for the chickencoop project.

Provides consistent UTC time handling, formatting, and date calculations.
"""

from datetime import datetime, date, time, timezone, timedelta


def now_utc():
    """
    Get current UTC datetime.

    Returns:
        datetime: Current time in UTC timezone
    """
    return datetime.now(timezone.utc)


def today_utc():
    """
    Get current UTC date.

    Returns:
        date: Current date in UTC timezone
    """
    return datetime.now(timezone.utc).date()


def to_iso_format(dt):
    """
    Convert datetime to ISO format string.

    Args:
        dt: Datetime object to convert

    Returns:
        str: ISO format string representation
    """
    return dt.isoformat()


def from_iso_format(iso_string):
    """
    Parse ISO format string to datetime.

    Args:
        iso_string: ISO format datetime string

    Returns:
        datetime: Parsed datetime object
    """
    return datetime.fromisoformat(iso_string)


def format_for_filename(dt):
    """
    Format datetime for use in filenames.

    Args:
        dt: Datetime object

    Returns:
        str: Formatted string in YYYYMMDD_HHMMSS format
    """
    return dt.strftime("%Y%m%d_%H%M%S")


def format_for_display(dt):
    """
    Format datetime for human-readable display.

    Args:
        dt: Datetime object

    Returns:
        str: Formatted string with date, time, and timezone
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def format_date_for_csv(d):
    """
    Format date for CSV output.

    Args:
        d: Date object

    Returns:
        str: Formatted date string in YYYY-MM-DD format
    """
    return d.strftime("%Y-%m-%d")


def get_start_of_day(dt):
    """
    Get the start of day (00:00:00) for a given datetime.

    Args:
        dt: Datetime object

    Returns:
        datetime: Datetime set to 00:00:00.000000
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(dt):
    """
    Get the end of day (23:59:59.999999) for a given datetime.

    Args:
        dt: Datetime object

    Returns:
        datetime: Datetime set to 23:59:59.999999
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_last_n_days(n):
    """
    Get a list of the last N days including today.

    Args:
        n: Number of days to retrieve

    Returns:
        list: List of date objects for the last N days
    """
    today = datetime.now(timezone.utc).date()
    return [today - timedelta(days=i) for i in range(n)]


def get_time_range(period):
    """
    Get start and end datetime for a specified period.

    Args:
        period: Period identifier (e.g., "last_24_hours")

    Returns:
        tuple: (start_datetime, end_datetime) in UTC
    """
    end = datetime.now(timezone.utc)
    if period == "last_24_hours":
        start = end - timedelta(hours=24)
    return start, end


def to_utc(dt):
    """
    Convert datetime to UTC timezone.

    If the datetime is naive (no timezone), assumes it's already UTC.

    Args:
        dt: Datetime object

    Returns:
        datetime: Datetime in UTC timezone
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    else:
        return dt.astimezone(timezone.utc)


def to_local(dt):
    """
    Convert datetime to local system timezone.

    Args:
        dt: Datetime object

    Returns:
        datetime: Datetime in local timezone
    """
    return dt.astimezone()


def seconds_since(dt):
    """
    Calculate seconds elapsed since the given datetime.

    Args:
        dt: Datetime object to calculate from

    Returns:
        float: Number of seconds elapsed
    """
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds()


def minutes_since(dt):
    """
    Calculate minutes elapsed since the given datetime.

    Args:
        dt: Datetime object to calculate from

    Returns:
        float: Number of minutes elapsed
    """
    return seconds_since(dt) / 60


def is_within_last_n_minutes(dt, n):
    """
    Check if datetime is within the last N minutes.

    Args:
        dt: Datetime object to check
        n: Number of minutes threshold

    Returns:
        bool: True if dt is within last N minutes
    """
    return minutes_since(dt) <= n


def parse_schedule_time(time_str):
    """
    Parse a time string in HH:MM format.

    Args:
        time_str: Time string in "HH:MM" format

    Returns:
        time: Parsed time object

    Raises:
        ValueError: If time_str is not in valid format
    """
    try:
        hour, minute = time_str.split(":")
        return time(int(hour), int(minute))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: {time_str}")


def get_next_scheduled_time(schedule):
    """
    Get the next occurrence of a scheduled time.

    If the scheduled time has already passed today, returns tomorrow's occurrence.

    Args:
        schedule: Time object representing the scheduled time

    Returns:
        datetime: Next occurrence of the scheduled time in UTC
    """
    now = datetime.now(timezone.utc)
    scheduled = now.replace(
        hour=schedule.hour,
        minute=schedule.minute,
        second=0,
        microsecond=0
    )
    if scheduled <= now:
        scheduled += timedelta(days=1)
    return scheduled
