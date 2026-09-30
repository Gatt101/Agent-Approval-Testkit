from __future__ import annotations

import json
from dataclasses import asdict

from rich.console import Console
from rich.table import Table

from approval_testkit import __version__
from approval_testkit.models import PASS, Report

_STYLE = {"PASS": "bold green", "FAIL": "bold red", "ERROR": "bold yellow"}


def _failing_probes(report: Report, invariant: str) -> list[str]:
    return [r.probe for r in report.results if r.invariant == invariant and r.status != PASS]


def _summary(report: Report) -> str:
    return f"Failures: {len(report.failed)} / {len(report.invariants())}"


def terminal(report: Report, console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Approval Integrity Report", title_justify="left")
    table.add_column("Status")
    table.add_column("Invariant")
    table.add_column("Accepted mutations")
    for invariant, status in report.invariants().items():
        table.add_row(f"[{_STYLE[status]}]{status}[/]", invariant,
                      "\n".join(_failing_probes(report, invariant)))
    console.print(table)
    console.print(f"{_summary(report)}\nExit code: {report.exit_code}")


def to_json(report: Report) -> str:
    return json.dumps({
        "version": __version__,
        "summary": {"invariants": len(report.invariants()), "failed": len(report.failed),
                    "exit_code": report.exit_code},
        "invariants": report.invariants(),
        "cases": [asdict(r) for r in report.results],
    }, indent=2)


def to_markdown(report: Report) -> str:
    icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}
    lines = ["## Approval Integrity Report", "", "| Status | Invariant | Accepted mutations |",
             "|---|---|---|"]
    for invariant, status in report.invariants().items():
        probes = "<br>".join(f"`{p}`" for p in _failing_probes(report, invariant))
        lines.append(f"| {icon[status]} {status} | {invariant} | {probes} |")
    lines += ["", f"**{_summary(report)}**", ""]
    return "\n".join(lines)
