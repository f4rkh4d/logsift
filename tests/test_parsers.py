from logsift.parsers import detect_format, parse_json, parse_line, parse_logfmt


def test_parse_json_basic():
    assert parse_json('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_parse_json_invalid():
    assert parse_json("not json") is None
    assert parse_json("") is None
    assert parse_json("[1,2]") is None  # array, not object


def test_parse_logfmt_basic():
    assert parse_logfmt("level=info msg=hello") == {"level": "info", "msg": "hello"}


def test_parse_logfmt_quoted():
    r = parse_logfmt('level=error msg="hello world" key=val')
    assert r == {"level": "error", "msg": "hello world", "key": "val"}


def test_parse_logfmt_empty_value():
    r = parse_logfmt("a= b=2")
    assert r == {"a": "", "b": "2"}


def test_parse_logfmt_escapes():
    r = parse_logfmt('msg="he said \\"hi\\"" n=1')
    assert r == {"msg": 'he said "hi"', "n": "1"}


def test_parse_logfmt_nonempty_returns_none():
    assert parse_logfmt("") is None
    assert parse_logfmt("   ") is None


def test_detect_format_json():
    lines = ['{"a":1}', '{"b":2}', '{"c":3}']
    assert detect_format(lines) == "json"


def test_detect_format_logfmt():
    lines = ["a=1 b=2", "a=3 b=4", "x=y z=w"]
    assert detect_format(lines) == "logfmt"


def test_detect_format_plain():
    lines = ["just some text", "more text here", "no structure"]
    assert detect_format(lines) == "plain"


def test_parse_line_plain():
    assert parse_line("hello world", "plain") == {"msg": "hello world"}
