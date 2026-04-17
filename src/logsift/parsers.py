"""Parsers for JSON-lines and logfmt formats with auto-detection."""

from __future__ import annotations

import json
from typing import Dict, Optional


def parse_json(line: str) -> Optional[Dict]:
    """Parse a single JSON line. Returns dict or None if invalid."""
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
        if isinstance(obj, dict):
            # stringify non-dict values only if needed by caller
            return obj
        return None
    except (ValueError, json.JSONDecodeError):
        return None


def parse_logfmt(line: str) -> Optional[Dict]:
    """Parse a logfmt line: key=value key="quoted value" key=.

    Supports:
    - unquoted tokens (whitespace terminated)
    - double-quoted values with \\" and \\\\ escapes
    - empty values (key=)
    - bare tokens (no '=') skipped
    """
    line = line.rstrip("\n\r")
    if not line.strip():
        return None

    result: Dict[str, str] = {}
    i = 0
    n = len(line)
    found_any = False

    while i < n:
        # skip whitespace
        while i < n and line[i] in " \t":
            i += 1
        if i >= n:
            break

        # read key
        key_start = i
        while i < n and line[i] not in " \t=":
            i += 1
        key = line[key_start:i]
        if not key:
            i += 1
            continue

        if i >= n or line[i] != "=":
            # bare token, skip
            continue

        i += 1  # skip '='

        # read value
        if i < n and line[i] == '"':
            i += 1
            val_chars = []
            while i < n:
                c = line[i]
                if c == "\\" and i + 1 < n:
                    nxt = line[i + 1]
                    if nxt == '"':
                        val_chars.append('"')
                        i += 2
                        continue
                    if nxt == "\\":
                        val_chars.append("\\")
                        i += 2
                        continue
                    if nxt == "n":
                        val_chars.append("\n")
                        i += 2
                        continue
                    if nxt == "t":
                        val_chars.append("\t")
                        i += 2
                        continue
                    val_chars.append(c)
                    i += 1
                    continue
                if c == '"':
                    i += 1
                    break
                val_chars.append(c)
                i += 1
            value = "".join(val_chars)
        else:
            val_start = i
            while i < n and line[i] not in " \t":
                i += 1
            value = line[val_start:i]

        result[key] = value
        found_any = True

    if not found_any:
        return None
    return result


def detect_format(sample_lines) -> str:
    """Detect format from sample lines. Returns 'json', 'logfmt', or 'plain'."""
    json_hits = 0
    logfmt_hits = 0
    total = 0
    for line in sample_lines:
        line = line.strip()
        if not line:
            continue
        total += 1
        if parse_json(line) is not None:
            json_hits += 1
            continue
        p = parse_logfmt(line)
        if p and len(p) >= 1 and "=" in line:
            logfmt_hits += 1

    if total == 0:
        return "plain"
    if json_hits / total >= 0.6:
        return "json"
    if logfmt_hits / total >= 0.6:
        return "logfmt"
    return "plain"


def parse_line(line: str, fmt: str) -> Optional[Dict]:
    """Parse a line using the specified format."""
    if fmt == "json":
        return parse_json(line)
    if fmt == "logfmt":
        return parse_logfmt(line)
    # plain: return dict with raw message
    line = line.rstrip("\n\r")
    if not line.strip():
        return None
    return {"msg": line}
