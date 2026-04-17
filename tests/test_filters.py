import pytest

from logsift.filters import make_predicate, parse_where


def test_parse_where_eq():
    assert parse_where("level=error") == ("level", "=", "error")


def test_parse_where_neq():
    assert parse_where("level!=info") == ("level", "!=", "info")


def test_parse_where_gte():
    assert parse_where("status>=500") == ("status", ">=", "500")


def test_parse_where_in():
    f, op, v = parse_where("level in error,fatal")
    assert f == "level" and op == "in" and v == "error,fatal"


def test_parse_where_invalid():
    with pytest.raises(ValueError):
        parse_where("nope")


def test_pred_eq():
    p = make_predicate("level=error")
    assert p({"level": "error"})
    assert not p({"level": "info"})


def test_pred_numeric_gt():
    p = make_predicate("status>=500")
    assert p({"status": 500})
    assert p({"status": "503"})
    assert not p({"status": 200})


def test_pred_regex():
    p = make_predicate("msg~=failed.*connect")
    assert p({"msg": "failed to connect to db"})
    assert not p({"msg": "success"})


def test_pred_in():
    p = make_predicate("level in warn,error,fatal")
    assert p({"level": "error"})
    assert not p({"level": "info"})


def test_pred_in_numeric():
    p = make_predicate("code in 200,201,204")
    assert p({"code": 200})
    assert p({"code": "201"})
    assert not p({"code": 500})


def test_pred_missing_field():
    p = make_predicate("level=error")
    assert not p({})
    p2 = make_predicate("level!=info")
    assert p2({})


def test_pred_lt():
    p = make_predicate("n<10")
    assert p({"n": 5})
    assert not p({"n": 15})
