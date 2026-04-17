"""Output renderers: table, json, raw."""

from __future__ import annotations

import json
import sys
from typing import Dict, Iterable, List, Optional

from rich.console import Console
from rich.table import Table

_LEVEL_STYLES = {
    "debug": "dim cyan",
    "info": "green",
    "warn": "yellow",
    "warning": "yellow",
    "error": "bold red",
    "err": "bold red",
    "fatal": "bold red reverse",
    "critical": "bold red reverse",
}


def _level_style(level: str) -> str:
    return _LEVEL_STYLES.get(str(level).lower(), "")


def render_table(
    records: Iterable[Dict],
    fields: Optional[List[str]] = None,
    console: Optional[Console] = None,
) -> None:
    console = console or Console()
    records = list(records)
    if not records:
        return

    if fields is None:
        # use union of keys, with common ordering
        seen = []
        for r in records:
            for k in r.keys():
                if k not in seen:
                    seen.append(k)
        priority = ["time", "timestamp", "ts", "@timestamp", "level", "msg", "message"]
        ordered = [k for k in priority if k in seen] + [k for k in seen if k not in priority]
        fields = ordered

    table = Table(show_header=True, header_style="bold")
    for f in fields:
        table.add_column(f, overflow="fold")

    for r in records:
        row = []
        level = r.get("level", "")
        for f in fields:
            v = r.get(f, "")
            s = "" if v is None else str(v)
            if f == "level":
                style = _level_style(level)
                row.append(f"[{style}]{s}[/{style}]" if style else s)
            else:
                row.append(s)
        table.add_row(*row)

    console.print(table)


def render_json(records: Iterable[Dict], fields: Optional[List[str]] = None, out=None) -> None:
    if out is None:
        out = sys.stdout
    for r in records:
        if fields:
            r = {k: r.get(k) for k in fields}
        out.write(json.dumps(r, default=str) + "\n")


def render_raw(raw_lines: Iterable[str], out=None) -> None:
    if out is None:
        out = sys.stdout
    for line in raw_lines:
        if not line.endswith("\n"):
            line = line + "\n"
        out.write(line)
