import json
import os
from pathlib import Path

from click.testing import CliRunner

from logsift.cli import main


def _write(tmp_path: Path, name: str, lines):
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def test_cli_json_filter(tmp_path):
    log = _write(
        tmp_path,
        "app.log",
        [
            json.dumps({"time": "2024-01-01T10:00:00Z", "level": "info", "msg": "ok"}),
            json.dumps({"time": "2024-01-01T10:01:00Z", "level": "error", "msg": "boom"}),
            json.dumps({"time": "2024-01-01T10:02:00Z", "level": "warn", "msg": "hmm"}),
        ],
    )
    runner = CliRunner()
    result = runner.invoke(main, [log, "--where", "level=error", "--json"])
    assert result.exit_code == 0, result.output
    lines = [l for l in result.output.strip().splitlines() if l]
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["level"] == "error"


def test_cli_count(tmp_path):
    log = _write(
        tmp_path,
        "a.log",
        [
            json.dumps({"level": "error", "msg": "a"}),
            json.dumps({"level": "error", "msg": "b"}),
            json.dumps({"level": "info", "msg": "c"}),
        ],
    )
    runner = CliRunner()
    r = runner.invoke(main, [log, "--where", "level=error", "--count"])
    assert r.exit_code == 0
    assert r.output.strip() == "2"


def test_cli_group_by(tmp_path):
    log = _write(
        tmp_path,
        "a.log",
        [
            json.dumps({"level": "error"}),
            json.dumps({"level": "error"}),
            json.dumps({"level": "info"}),
            json.dumps({"level": "warn"}),
            json.dumps({"level": "warn"}),
            json.dumps({"level": "warn"}),
        ],
    )
    runner = CliRunner()
    r = runner.invoke(main, [log, "--group-by", "level"])
    assert r.exit_code == 0
    out = r.output
    assert "error" in out and "info" in out and "warn" in out
    # warn has highest count, should appear with 3
    assert "3" in out


def test_cli_logfmt_auto(tmp_path):
    log = _write(
        tmp_path,
        "lf.log",
        [
            'level=info msg="hello world"',
            "level=error msg=boom",
            "level=info msg=ok",
        ],
    )
    runner = CliRunner()
    r = runner.invoke(main, [log, "--where", "level=error", "--json"])
    assert r.exit_code == 0, r.output
    lines = [l for l in r.output.strip().splitlines() if l]
    assert len(lines) == 1
    assert json.loads(lines[0])["msg"] == "boom"


def test_cli_raw_output(tmp_path):
    log = _write(
        tmp_path,
        "r.log",
        [
            json.dumps({"level": "error", "msg": "x"}),
            json.dumps({"level": "info", "msg": "y"}),
        ],
    )
    runner = CliRunner()
    r = runner.invoke(main, [log, "--where", "level=error", "--raw"])
    assert r.exit_code == 0
    assert '"level": "error"' in r.output
    assert '"level": "info"' not in r.output


def test_cli_numeric_filter(tmp_path):
    log = _write(
        tmp_path,
        "n.log",
        [
            json.dumps({"status": 200, "path": "/a"}),
            json.dumps({"status": 500, "path": "/b"}),
            json.dumps({"status": 503, "path": "/c"}),
        ],
    )
    runner = CliRunner()
    r = runner.invoke(main, [log, "--where", "status>=500", "--count"])
    assert r.exit_code == 0
    assert r.output.strip() == "2"


def test_cli_stdin(tmp_path):
    runner = CliRunner()
    inp = (
        json.dumps({"level": "error", "msg": "a"}) + "\n"
        + json.dumps({"level": "info", "msg": "b"}) + "\n"
    )
    r = runner.invoke(main, ["--where", "level=error", "--count"], input=inp)
    assert r.exit_code == 0
    assert r.output.strip() == "1"
