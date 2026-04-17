"""logsift CLI entry point."""

from __future__ import annotations

import glob as _glob
import sys
from collections import Counter
from typing import Iterator, List, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from .filters import make_predicates
from .output import render_json, render_raw, render_table
from .parsers import detect_format, parse_line
from .stream import follow_files
from .time_utils import extract_record_time, parse_between, parse_time


def _iter_file(path: str) -> Iterator[str]:
    with open(path, "r") as f:
        for line in f:
            yield line


def _iter_stdin() -> Iterator[str]:
    for line in sys.stdin:
        yield line


def _expand_paths(patterns: List[str]) -> List[str]:
    out: List[str] = []
    for p in patterns:
        matches = _glob.glob(p)
        if matches:
            out.extend(sorted(matches))
        else:
            out.append(p)
    return out


def _make_source(files: List[str]) -> Tuple[Iterator[str], bool]:
    """Return iterator of raw lines and whether it came from stdin."""
    if files:
        def gen() -> Iterator[str]:
            for p in files:
                try:
                    yield from _iter_file(p)
                except OSError as e:
                    click.echo(f"logsift: {p}: {e}", err=True)
        return gen(), False
    return _iter_stdin(), True


def _process(
    lines: Iterator[str],
    fmt: Optional[str],
    where: List[str],
    since,
    until,
    between,
    time_field: Optional[str],
) -> Iterator[Tuple[str, dict]]:
    """Yield (raw_line, parsed_record) for matches."""
    predicate = make_predicates(where) if where else (lambda r: True)

    # buffer for auto-detect
    buffered: List[str] = []
    detected_fmt = fmt

    if detected_fmt is None:
        # buffer up to first 20 non-empty lines
        for line in lines:
            buffered.append(line)
            non_empty = [l for l in buffered if l.strip()]
            if len(non_empty) >= 20:
                break
        detected_fmt = detect_format(buffered)

    def all_lines() -> Iterator[str]:
        for l in buffered:
            yield l
        for l in lines:
            yield l

    for raw in all_lines():
        record = parse_line(raw, detected_fmt)
        if record is None:
            continue

        # time filter
        if since or until or between:
            ts = extract_record_time(record, field=time_field)
            if ts is None:
                continue
            if since and ts < since:
                continue
            if until and ts > until:
                continue
            if between:
                start, end = between
                if ts < start or ts > end:
                    continue

        if not predicate(record):
            continue

        yield raw, record


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("files", nargs=-1)
@click.option("--where", "-w", multiple=True, help="Filter: field<op>value (=, !=, >, >=, <, <=, ~=, in)")
@click.option("--since", default=None, help="Only events since (e.g. 15m, 2h, 2024-01-01)")
@click.option("--until", default=None, help="Only events until (e.g. 2h ago, 2024-01-02)")
@click.option("--between", default=None, help="Range A..B (e.g. 10:00..11:00)")
@click.option("--time-field", default=None, help="Field holding timestamp (default: auto)")
@click.option("--fields", default=None, help="Comma-separated fields to project")
@click.option("--format", "fmt", type=click.Choice(["auto", "json", "logfmt", "plain"]), default="auto")
@click.option("--json", "json_out", is_flag=True, help="Emit JSON-lines output")
@click.option("--raw", is_flag=True, help="Emit raw original lines")
@click.option("--follow", "-f", is_flag=True, help="Tail files as they grow")
@click.option("--count", is_flag=True, help="Print match count and exit")
@click.option("--group-by", "group_by", default=None, help="Group counts by a field")
def main(
    files,
    where,
    since,
    until,
    between,
    time_field,
    fields,
    fmt,
    json_out,
    raw,
    follow,
    count,
    group_by,
):
    """logsift: search and filter structured logs (JSON-lines or logfmt)."""
    expanded = _expand_paths(list(files))

    since_dt = parse_time(since) if since else None
    until_dt = parse_time(until) if until else None
    between_tup = parse_between(between) if between else None

    if since and since_dt is None:
        click.echo(f"logsift: invalid --since: {since}", err=True)
        sys.exit(2)
    if until and until_dt is None:
        click.echo(f"logsift: invalid --until: {until}", err=True)
        sys.exit(2)
    if between and between_tup is None:
        click.echo(f"logsift: invalid --between: {between}", err=True)
        sys.exit(2)

    project_fields = [f.strip() for f in fields.split(",")] if fields else None
    effective_fmt = None if fmt == "auto" else fmt

    if follow:
        if not expanded:
            click.echo("logsift: --follow requires file arguments", err=True)
            sys.exit(2)
        line_iter = follow_files(expanded)
        matches = _process(line_iter, effective_fmt, list(where), since_dt, until_dt, between_tup, time_field)
        for raw_line, record in matches:
            if raw:
                sys.stdout.write(raw_line if raw_line.endswith("\n") else raw_line + "\n")
            elif json_out:
                render_json([record], project_fields)
            else:
                render_table([record], project_fields)
            sys.stdout.flush()
        return

    line_iter, _from_stdin = _make_source(expanded)
    matches = _process(line_iter, effective_fmt, list(where), since_dt, until_dt, between_tup, time_field)

    if count:
        n = sum(1 for _ in matches)
        click.echo(str(n))
        return

    if group_by:
        counter: Counter = Counter()
        for _raw, rec in matches:
            counter[str(rec.get(group_by, ""))] += 1
        console = Console()
        table = Table(show_header=True, header_style="bold")
        table.add_column(group_by)
        table.add_column("count", justify="right")
        for key, cnt in counter.most_common():
            table.add_row(key, str(cnt))
        console.print(table)
        return

    if raw:
        render_raw((m[0] for m in matches))
        return
    if json_out:
        render_json((m[1] for m in matches), project_fields)
        return

    render_table((m[1] for m in matches), project_fields)


if __name__ == "__main__":
    main()
