from datetime import datetime, date, time, timezone, timedelta


def now_utc():
    return datetime.now(timezone.utc)


def today_utc():
    return datetime.now(timezone.utc).date()


def to_iso_format(dt):
    return dt.isoformat()


def from_iso_format(iso_string):
    return datetime.fromisoformat(iso_string)


def format_for_filename(dt):
    return dt.strftime("%Y%m%d_%H%M%S")


def format_for_display(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def format_date_for_csv(d):
    return d.strftime("%Y-%m-%d")


def get_start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_last_n_days(n):
    today = datetime.now(timezone.utc).date()
    return [today - timedelta(days=i) for i in range(n)]


def get_time_range(period):
    end = datetime.now(timezone.utc)
    if period == "last_24_hours":
        start = end - timedelta(hours=24)
    return start, end


def to_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    else:
        return dt.astimezone(timezone.utc)


def to_local(dt):
    return dt.astimezone()


def seconds_since(dt):
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds()


def minutes_since(dt):
    return seconds_since(dt) / 60


def is_within_last_n_minutes(dt, n):
    return minutes_since(dt) <= n


def parse_schedule_time(time_str):
    try:
        hour, minute = time_str.split(":")
        return time(int(hour), int(minute))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: {time_str}")


def get_next_scheduled_time(schedule):
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
