"""Time parsing utilities."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from dateutil import parser as du_parser

DEFAULT_TIME_FIELDS = ("time", "timestamp", "ts", "@timestamp")

_RELATIVE_RE = re.compile(r"^(\d+)\s*([smhdw])$", re.IGNORECASE)


def parse_relative(s: str) -> Optional[timedelta]:
    """Parse a relative time like '15m', '2h', '1d'. Returns timedelta or None."""
    m = _RELATIVE_RE.match(s.strip())
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "s":
        return timedelta(seconds=n)
    if unit == "m":
        return timedelta(minutes=n)
    if unit == "h":
        return timedelta(hours=n)
    if unit == "d":
        return timedelta(days=n)
    if unit == "w":
        return timedelta(weeks=n)
    return None


def parse_time(s: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """Parse a time string: relative ('15m'), absolute ('2024-01-01T10:00:00'),
    or clock time ('10:00').
    Returns timezone-aware datetime (UTC if naive)."""
    if now is None:
        now = datetime.now(timezone.utc)
    s = s.strip()
    if not s:
        return None

    rel = parse_relative(s)
    if rel is not None:
        return now - rel

    # clock time HH:MM or HH:MM:SS on today
    if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", s):
        try:
            t = du_parser.parse(s)
            dt = now.replace(
                hour=t.hour, minute=t.minute, second=t.second, microsecond=0
            )
            return dt
        except (ValueError, du_parser.ParserError):
            return None

    try:
        dt = du_parser.parse(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, du_parser.ParserError, OverflowError):
        return None


def parse_between(s: str, now: Optional[datetime] = None) -> Optional[Tuple[datetime, datetime]]:
    """Parse 'A..B' range. Returns (start, end) or None."""
    if ".." not in s:
        return None
    a, b = s.split("..", 1)
    start = parse_time(a, now=now)
    end = parse_time(b, now=now)
    if start is None or end is None:
        return None
    return start, end


def extract_record_time(record: dict, field: Optional[str] = None) -> Optional[datetime]:
    """Extract a timestamp from a record, trying known fields."""
    candidates = (field,) if field else DEFAULT_TIME_FIELDS
    for f in candidates:
        if f and f in record:
            val = record[f]
            if val is None:
                continue
            if isinstance(val, (int, float)):
                try:
                    # seconds or milliseconds
                    n = float(val)
                    if n > 1e12:
                        n = n / 1000.0
                    return datetime.fromtimestamp(n, tz=timezone.utc)
                except (ValueError, OSError):
                    continue
            try:
                dt = du_parser.parse(str(val))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, du_parser.ParserError, OverflowError):
                continue
    return None
