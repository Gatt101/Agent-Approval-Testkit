from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    """The action a human is asked to approve."""

    actor: str
    tool: str
    args: dict[str, Any]
    target: str
    policy_version: str = "1"


@dataclass(frozen=True)
class Approval:
    id: str
    request: ApprovalRequest
    approved_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class ExecutionAttempt:
    """What the agent actually tries to execute, presented with an approval id."""

    approval_id: str
    actor: str
    tool: str
    args: dict[str, Any]
    target: str

    @classmethod
    def from_approval(cls, approval: Approval) -> ExecutionAttempt:
        r = approval.request
        return cls(approval.id, r.actor, r.tool, dict(r.args), r.target)


PASS, FAIL, ERROR = "PASS", "FAIL", "ERROR"


@dataclass(frozen=True)
class CaseResult:
    mutation: str
    invariant: str
    probe: str
    status: str
    detail: str


@dataclass
class Report:
    results: list[CaseResult]

    def invariants(self) -> dict[str, str]:
        """Roll cases up per invariant: worst status wins."""
        rank = {PASS: 0, FAIL: 1, ERROR: 2}
        out: dict[str, str] = {}
        for r in self.results:
            if rank[r.status] >= rank[out.get(r.invariant, PASS)]:
                out[r.invariant] = r.status
        return out

    @property
    def failed(self) -> list[str]:
        return [name for name, status in self.invariants().items() if status != PASS]

    @property
    def exit_code(self) -> int:
        return 1 if self.failed else 0
