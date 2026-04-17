"""Where-clause parser and evaluator."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Tuple

OPERATORS = ["!=", ">=", "<=", "~=", "=", ">", "<"]


def _is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _coerce(a: Any, b: str) -> Tuple[Any, Any]:
    """Coerce two values for comparison: numeric if both numeric-like, else string."""
    sa = "" if a is None else str(a)
    if _is_numeric(sa) and _is_numeric(b):
        return float(sa), float(b)
    return sa, b


def parse_where(clause: str) -> Tuple[str, str, str]:
    """Tokenize a where clause into (field, op, value).

    Recognizes operators: !=, >=, <=, ~=, =, >, <
    Also recognizes ' in ' (space-delimited) for list membership.
    """
    clause = clause.strip()

    # check ' in ' operator
    m = re.match(r"^(\S+)\s+in\s+(.+)$", clause)
    if m:
        return m.group(1).strip(), "in", m.group(2).strip()

    for op in OPERATORS:
        idx = clause.find(op)
        if idx > 0:
            field = clause[:idx].strip()
            value = clause[idx + len(op):].strip()
            # strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            return field, op, value

    raise ValueError(f"Invalid where clause: {clause!r}")


def make_predicate(clause: str) -> Callable[[Dict], bool]:
    """Build a predicate function from a where clause."""
    field, op, value = parse_where(clause)

    def pred(record: Dict) -> bool:
        actual = record.get(field)
        if actual is None:
            # missing field: only != and not-in can be true
            if op == "!=":
                return True
            return False

        if op == "=":
            la, lb = _coerce(actual, value)
            return la == lb
        if op == "!=":
            la, lb = _coerce(actual, value)
            return la != lb
        if op == ">":
            la, lb = _coerce(actual, value)
            try:
                return la > lb
            except TypeError:
                return False
        if op == ">=":
            la, lb = _coerce(actual, value)
            try:
                return la >= lb
            except TypeError:
                return False
        if op == "<":
            la, lb = _coerce(actual, value)
            try:
                return la < lb
            except TypeError:
                return False
        if op == "<=":
            la, lb = _coerce(actual, value)
            try:
                return la <= lb
            except TypeError:
                return False
        if op == "~=":
            try:
                return re.search(value, str(actual)) is not None
            except re.error:
                return False
        if op == "in":
            items = [v.strip() for v in value.split(",")]
            sa = str(actual)
            if _is_numeric(sa):
                try:
                    fa = float(sa)
                    for it in items:
                        if _is_numeric(it) and float(it) == fa:
                            return True
                except ValueError:
                    pass
            return sa in items
        return False

    return pred


def make_predicates(clauses: List[str]) -> Callable[[Dict], bool]:
    """Combine multiple where clauses with AND."""
    preds = [make_predicate(c) for c in clauses]

    def combined(record: Dict) -> bool:
        return all(p(record) for p in preds)

    return combined
