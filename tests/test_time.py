from datetime import datetime, timedelta, timezone

from logsift.time_utils import extract_record_time, parse_between, parse_relative, parse_time


def test_parse_relative_minutes():
    assert parse_relative("15m") == timedelta(minutes=15)


def test_parse_relative_hours():
    assert parse_relative("2h") == timedelta(hours=2)


def test_parse_relative_days():
    assert parse_relative("3d") == timedelta(days=3)


def test_parse_relative_invalid():
    assert parse_relative("nope") is None


def test_parse_time_relative():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt = parse_time("15m", now=now)
    assert dt == now - timedelta(minutes=15)


def test_parse_time_absolute():
    dt = parse_time("2024-01-01T10:00:00Z")
    assert dt is not None
    assert dt.year == 2024 and dt.hour == 10


def test_parse_between():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    rng = parse_between("1h..30m", now=now)
    assert rng is not None
    start, end = rng
    assert start < end


def test_extract_record_time_iso():
    dt = extract_record_time({"time": "2024-01-01T10:00:00Z"})
    assert dt is not None and dt.hour == 10


def test_extract_record_time_epoch():
    dt = extract_record_time({"ts": 1704106800})
    assert dt is not None
