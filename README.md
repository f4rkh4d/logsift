# logsift

Format-aware CLI for searching and filtering structured logs. Unlike `grep`,
`logsift` understands JSON-lines and logfmt formats and lets you filter by
field, operator, and time window.

## Install

```
pip install -e .
```

## Quick examples

Find all 5xx errors in an access log:

```
logsift access.log --where 'status>=500'
```

Group counts by status code:

```
logsift access.log --group-by status
```

Tail files and show only errors:

```
logsift --follow app-*.log --where level=error
```

Look at the last 15 minutes:

```
logsift app.log --since 15m --where 'level in warn,error'
```

Project specific fields as JSON:

```
cat app.log | logsift --where level=error --fields time,level,msg --json
```

Use regex:

```
logsift app.log --where 'msg~=timeout|refused'
```

## Operators

`=`, `!=`, `>`, `>=`, `<`, `<=`, `~=` (regex), `in` (comma list).

Numeric comparison is used when both sides look numeric; otherwise string
comparison.

## Time filters

- `--since 15m`, `--since 2h`, `--since 1d`
- `--until 30m` (i.e. until 30m ago)
- `--between 10:00..11:00`
- Absolute: `--since 2024-01-01T10:00:00Z`

Timestamp is read from `time`, `timestamp`, `ts`, or `@timestamp` by default.
Override with `--time-field`.

## Output

- Default: rich colored table
- `--json`: JSON lines (after filtering/projection)
- `--raw`: original input lines

## License

MIT
