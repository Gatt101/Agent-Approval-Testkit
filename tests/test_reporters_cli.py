import json

from conftest import NOW, REQUEST, SECURE, VULNERABLE
from rich.console import Console
from typer.testing import CliRunner

from approval_testkit import reporters
from approval_testkit.cli import app
from approval_testkit.runner import run_all

cli = CliRunner()


def test_terminal_report_lists_invariants(vulnerable):
    console = Console(record=True, width=120)
    reporters.terminal(run_all(vulnerable, REQUEST, now=NOW), console)
    text = console.export_text()
    assert "FAIL" in text and "argument binding" in text and "Failures: 2 / 7" in text


def test_json_report(vulnerable):
    data = json.loads(reporters.to_json(run_all(vulnerable, REQUEST, now=NOW)))
    assert data["summary"] == {"invariants": 7, "failed": 2, "exit_code": 1}
    assert data["invariants"]["replay protection"] == "FAIL"


def test_markdown_report(secure):
    md = reporters.to_markdown(run_all(secure, REQUEST, now=NOW))
    assert "| Status | Invariant |" in md and "Failures: 0 / 7" in md


def test_cli_vulnerable_exits_1():
    result = cli.invoke(app, ["run", str(VULNERABLE)])
    assert result.exit_code == 1
    assert "replay protection" in result.output


def test_cli_secure_exits_0():
    assert cli.invoke(app, ["run", str(SECURE)]).exit_code == 0


def test_cli_json_output_file(tmp_path):
    out = tmp_path / "r.json"
    result = cli.invoke(app, ["run", str(VULNERABLE), "-f", "json", "-o", str(out)])
    assert result.exit_code == 1
    assert json.loads(out.read_text(encoding="utf-8"))["summary"]["failed"] == 2


def test_cli_config_error_exits_2(tmp_path):
    assert cli.invoke(app, ["run", str(tmp_path)]).exit_code == 2


def test_cli_list_mutations():
    result = cli.invoke(app, ["list-mutations"])
    assert result.exit_code == 0
    assert result.output.count("\n") == 7
