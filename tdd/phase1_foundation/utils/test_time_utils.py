"""
TDD Tests: Time Utilities

These tests define the expected behavior for timestamp handling.
Implement src/utils/time_utils.py to make these tests pass.

Run: pytest tdd/phase1_foundation/utils/test_time_utils.py -v
"""

import pytest
from datetime import datetime, date, timezone, timedelta


# =============================================================================
# Test: UTC Timestamp Generation
# =============================================================================

class TestUTCTimestamp:
    """Tests for generating UTC timestamps."""

    def test_now_utc_returns_datetime(self):
        """Should return a datetime object."""
        from src.utils.time_utils import now_utc

        result = now_utc()

        assert isinstance(result, datetime)

    def test_now_utc_is_timezone_aware(self):
        """Returned datetime should be timezone-aware."""
        from src.utils.time_utils import now_utc

        result = now_utc()

        assert result.tzinfo is not None

    def test_now_utc_is_utc_timezone(self):
        """Returned datetime should be in UTC timezone."""
        from src.utils.time_utils import now_utc

        result = now_utc()

        assert result.tzinfo == timezone.utc

    def test_today_utc_returns_date(self):
        """Should return current date in UTC."""
        from src.utils.time_utils import today_utc

        result = today_utc()

        assert isinstance(result, date)


# =============================================================================
# Test: ISO Format Conversion
# =============================================================================

class TestISOFormatConversion:
    """Tests for ISO 8601 format conversion."""

    def test_to_iso_format_returns_string(self):
        """Should return an ISO format string."""
        from src.utils.time_utils import to_iso_format

        dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        result = to_iso_format(dt)

        assert isinstance(result, str)

    def test_to_iso_format_includes_timezone(self):
        """ISO string should include timezone info."""
        from src.utils.time_utils import to_iso_format

        dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        result = to_iso_format(dt)

        assert "+" in result or "Z" in result

    def test_from_iso_format_returns_datetime(self):
        """Should parse ISO string to datetime."""
        from src.utils.time_utils import from_iso_format

        iso_string = "2025-01-25T14:30:00+00:00"
        result = from_iso_format(iso_string)

        assert isinstance(result, datetime)

    def test_from_iso_format_preserves_values(self):
        """Parsed datetime should have correct values."""
        from src.utils.time_utils import from_iso_format

        iso_string = "2025-01-25T14:30:00+00:00"
        result = from_iso_format(iso_string)

        assert result.year == 2025
        assert result.month == 1
        assert result.day == 25
        assert result.hour == 14
        assert result.minute == 30

    def test_roundtrip_iso_format(self):
        """Converting to ISO and back should preserve datetime."""
        from src.utils.time_utils import to_iso_format, from_iso_format

        original = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        iso_string = to_iso_format(original)
        result = from_iso_format(iso_string)

        assert result == original


# =============================================================================
# Test: Timestamp Formatting
# =============================================================================

class TestTimestampFormatting:
    """Tests for formatting timestamps for display."""

    def test_format_timestamp_for_filename(self):
        """Should format timestamp for safe filenames."""
        from src.utils.time_utils import format_for_filename

        dt = datetime(2025, 1, 25, 14, 30, 45, tzinfo=timezone.utc)
        result = format_for_filename(dt)

        assert "2025" in result
        assert "01" in result
        assert "25" in result
        # Should not contain characters invalid for filenames
        assert ":" not in result
        assert "/" not in result

    def test_format_timestamp_for_display(self):
        """Should format timestamp for human display."""
        from src.utils.time_utils import format_for_display

        dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        result = format_for_display(dt)

        assert isinstance(result, str)
        # Should be human readable
        assert len(result) > 10

    def test_format_date_for_csv(self):
        """Should format date for CSV filenames."""
        from src.utils.time_utils import format_date_for_csv

        d = date(2025, 1, 25)
        result = format_date_for_csv(d)

        assert "2025" in result
        assert "01" in result
        assert "25" in result


# =============================================================================
# Test: Time Range Calculations
# =============================================================================

class TestTimeRangeCalculations:
    """Tests for calculating time ranges."""

    def test_get_start_of_day_utc(self):
        """Should return start of day in UTC."""
        from src.utils.time_utils import get_start_of_day

        dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        result = get_start_of_day(dt)

        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.day == 25

    def test_get_end_of_day_utc(self):
        """Should return end of day in UTC."""
        from src.utils.time_utils import get_end_of_day

        dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        result = get_end_of_day(dt)

        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        assert result.day == 25

    def test_get_last_n_days(self):
        """Should return list of last N days."""
        from src.utils.time_utils import get_last_n_days

        result = get_last_n_days(7)

        assert len(result) == 7
        assert all(isinstance(d, date) for d in result)
        # Should be in reverse chronological order
        assert result[0] >= result[-1]

    def test_get_time_range_for_period(self):
        """Should return start and end for a named period."""
        from src.utils.time_utils import get_time_range

        start, end = get_time_range("last_24_hours")

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert end > start
        assert (end - start) <= timedelta(hours=25)


# =============================================================================
# Test: Timezone Conversion
# =============================================================================

class TestTimezoneConversion:
    """Tests for timezone conversion."""

    def test_to_utc_from_naive(self):
        """Should convert naive datetime assuming local time."""
        from src.utils.time_utils import to_utc

        naive_dt = datetime(2025, 1, 25, 14, 30, 0)
        result = to_utc(naive_dt)

        assert result.tzinfo == timezone.utc

    def test_to_utc_from_aware(self):
        """Should convert aware datetime to UTC."""
        from src.utils.time_utils import to_utc

        # EST is UTC-5
        est = timezone(timedelta(hours=-5))
        aware_dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=est)
        result = to_utc(aware_dt)

        assert result.tzinfo == timezone.utc
        assert result.hour == 19  # 14:30 EST = 19:30 UTC

    def test_to_local_from_utc(self):
        """Should convert UTC to local timezone."""
        from src.utils.time_utils import to_local

        utc_dt = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        result = to_local(utc_dt)

        assert isinstance(result, datetime)
        # Should still represent the same instant
        assert result.utctimetuple()[:6] == utc_dt.utctimetuple()[:6]


# =============================================================================
# Test: Time Difference Calculations
# =============================================================================

class TestTimeDifferenceCalculations:
    """Tests for calculating time differences."""

    def test_seconds_since_returns_float(self):
        """Should return seconds as float."""
        from src.utils.time_utils import seconds_since

        past = datetime.now(timezone.utc) - timedelta(seconds=60)
        result = seconds_since(past)

        assert isinstance(result, (int, float))
        assert result >= 59  # Allow for small timing differences

    def test_minutes_since_returns_float(self):
        """Should return minutes as float."""
        from src.utils.time_utils import minutes_since

        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = minutes_since(past)

        assert isinstance(result, (int, float))
        assert result >= 4.9

    def test_is_within_last_n_minutes_true(self):
        """Should return True for recent timestamps."""
        from src.utils.time_utils import is_within_last_n_minutes

        recent = datetime.now(timezone.utc) - timedelta(minutes=2)
        result = is_within_last_n_minutes(recent, 5)

        assert result is True

    def test_is_within_last_n_minutes_false(self):
        """Should return False for old timestamps."""
        from src.utils.time_utils import is_within_last_n_minutes

        old = datetime.now(timezone.utc) - timedelta(minutes=10)
        result = is_within_last_n_minutes(old, 5)

        assert result is False


# =============================================================================
# Test: Scheduled Time Parsing
# =============================================================================

class TestScheduledTimeParsing:
    """Tests for parsing scheduled times."""

    def test_parse_schedule_time_returns_time(self):
        """Should parse HH:MM format to time."""
        from src.utils.time_utils import parse_schedule_time
        from datetime import time

        result = parse_schedule_time("19:00")

        assert isinstance(result, time)
        assert result.hour == 19
        assert result.minute == 0

    def test_parse_schedule_time_handles_leading_zeros(self):
        """Should handle times with leading zeros."""
        from src.utils.time_utils import parse_schedule_time

        result = parse_schedule_time("07:30")

        assert result.hour == 7
        assert result.minute == 30

    def test_parse_schedule_time_invalid_format_raises(self):
        """Should raise error for invalid format."""
        from src.utils.time_utils import parse_schedule_time

        with pytest.raises(ValueError):
            parse_schedule_time("invalid")

    def test_get_next_scheduled_time(self):
        """Should calculate next occurrence of scheduled time."""
        from src.utils.time_utils import get_next_scheduled_time
        from datetime import time

        schedule = time(19, 0)  # 7 PM
        result = get_next_scheduled_time(schedule)

        assert isinstance(result, datetime)
        assert result.hour == 19
        assert result.minute == 0
        assert result > datetime.now(timezone.utc)
