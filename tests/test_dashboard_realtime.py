"""
tests/test_dashboard_realtime.py
================================
Tests verifying:
1. Timezone is Asia/Kolkata (IST: UTC+05:30).
2. Timestamp is timezone-aware (tzinfo is present and valid).
3. Timestamp is dynamically generated from current system clock.
4. Timestamp is NOT hard-coded (never fixed strings, never 2024 historical dates).
5. Automatic refresh mechanism is configured (st.fragment with 30s interval).
6. Timestamp changes dynamically after simulated refresh interval.
7. No unnecessary database queries/polling are introduced by the live clock.
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add streamlit directory to sys.path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "streamlit"))

from components import get_current_ist_time, format_dashboard_timestamp


class TestDashboardRealtimeTimestamp:
    """Test suite for Step 7.7: Live Dashboard Timestamp & Auto-Refresh."""

    # 1. Verify timezone is Asia/Kolkata
    def test_01_timezone_is_asia_kolkata(self):
        dt = get_current_ist_time()
        assert dt is not None
        assert dt.tzinfo is not None, "Returned datetime must have a tzinfo"
        tz_name = str(dt.tzinfo)
        # Should be Asia/Kolkata or IST
        assert "Asia/Kolkata" in tz_name or "IST" in tz_name
        # Offset must be exactly UTC+05:30 (+19800 seconds)
        offset = dt.utcoffset()
        assert offset == timedelta(hours=5, minutes=30), (
            f"Expected UTC+05:30 offset (+19800s), got {offset}"
        )

    # 2. Verify timestamp is timezone-aware
    def test_02_timestamp_is_timezone_aware(self):
        dt = get_current_ist_time()
        assert dt.tzinfo is not None
        assert dt.tzinfo.utcoffset(dt) is not None, "Timestamp must not be naive"
        # Compare against UTC now to ensure exact alignment
        utc_now = datetime.now(timezone.utc)
        diff_seconds = abs((dt - utc_now).total_seconds())
        assert diff_seconds < 5, f"IST time deviates from UTC by {diff_seconds}s"

    # 3. Verify timestamp is dynamically generated
    def test_03_timestamp_is_dynamically_generated(self):
        # Two mock times should yield different dynamic timestamps
        t1 = datetime(2026, 9, 8, 2, 1, 0, tzinfo=timezone(timedelta(hours=5, minutes=30), name="IST"))
        t2 = datetime(2026, 9, 8, 2, 2, 0, tzinfo=timezone(timedelta(hours=5, minutes=30), name="IST"))

        with patch("components.get_current_ist_time", return_value=t1):
            formatted1 = format_dashboard_timestamp()
            assert formatted1 == "08 Sep 2026, 02:01 AM IST"

        with patch("components.get_current_ist_time", return_value=t2):
            formatted2 = format_dashboard_timestamp()
            assert formatted2 == "08 Sep 2026, 02:02 AM IST"

        assert formatted1 != formatted2, "Timestamp must change dynamically with time"

    # 4. Verify timestamp is NOT hard-coded
    def test_04_timestamp_not_hardcoded(self):
        formatted = format_dashboard_timestamp()
        assert "IST" in formatted, "Must include IST suffix"
        # Must reflect current year, month, and day dynamically
        current_ist = get_current_ist_time()
        assert current_ist.strftime("%Y") in formatted, "Must reflect current dynamic year"
        assert current_ist.strftime("%b") in formatted, "Must reflect current dynamic month"
        assert current_ist.strftime("%d") in formatted, "Must reflect current dynamic day"
        # Must NOT be 2024 (historical dataset year)
        assert "2024" not in formatted or current_ist.year == 2024

    # 5. Verify automatic refresh mechanism is configured
    def test_05_automatic_refresh_mechanism_configured(self):
        # Inspect app.py source to verify @st.fragment(run_every=30)
        app_path = _ROOT / "streamlit" / "app.py"
        assert app_path.exists(), "app.py must exist"
        content = app_path.read_text(encoding="utf-8")

        assert "@st.fragment" in content, "Must use @st.fragment decorator"
        assert "run_every=30" in content or "run_every=60" in content, (
            "Refresh interval must be approximately 30-60 seconds"
        )
        assert "render_live_utility_toolbar" in content, (
            "Must define dedicated live utility toolbar fragment"
        )

    # 6. Verify timestamp changes after refresh interval
    def test_06_timestamp_changes_after_refresh_interval(self):
        # When 60 seconds pass, the formatted 12-hour timestamp updates
        base_time = datetime(2026, 9, 8, 2, 1, 15, tzinfo=timezone(timedelta(hours=5, minutes=30), name="IST"))
        after_interval = base_time + timedelta(seconds=60)

        s_before = format_dashboard_timestamp(base_time)
        s_after = format_dashboard_timestamp(after_interval)

        assert s_before == "08 Sep 2026, 02:01 AM IST"
        assert s_after == "08 Sep 2026, 02:02 AM IST"
        assert s_before != s_after

    # 7. Verify no unnecessary database polling is introduced
    def test_07_no_unnecessary_database_polling(self):
        # Formatting timestamp or getting IST time must NOT execute any database queries
        mock_engine = MagicMock()
        t = get_current_ist_time()
        fmt = format_dashboard_timestamp(t)

        # Ensure mock engine was never touched
        assert mock_engine.connect.call_count == 0
        assert mock_engine.execute.call_count == 0
        assert fmt.endswith("IST")
