from __future__ import annotations

from datetime import UTC, datetime

from approval_testkit.adapter import AdapterFactory
from approval_testkit.models import (
    ERROR,
    FAIL,
    PASS,
    ApprovalRequest,
    CaseResult,
    ExecutionAttempt,
    Report,
)
from approval_testkit.mutations import MUTATIONS, Mutation


def _accepts(adapter, attempt: ExecutionAttempt, now: datetime, policy_version: str) -> bool:
    try:
        return bool(adapter.verify(attempt, now=now, policy_version=policy_version))
    except Exception:
        return False  # raising is a valid way to deny


def run_all(
    factory: AdapterFactory,
    request: ApprovalRequest,
    mutations: list[Mutation] | None = None,
    now: datetime | None = None,
) -> Report:
    now = now or datetime.now(UTC)
    mutations = MUTATIONS if mutations is None else mutations

    # Baseline: a verifier that rejects everything would otherwise "pass" every invariant.
    adapter = factory()
    approval = adapter.create_approval(request, now=now)
    if not _accepts(adapter, ExecutionAttempt.from_approval(approval), now, request.policy_version):
        return Report([CaseResult("baseline", "baseline", "unmodified approved action", ERROR,
                                  "verifier rejected the exact approved action; fix the adapter")])

    results = []
    for m in mutations:
        for i in range(len(m.probes(approval, now))):
            # Fresh adapter + approval per probe so one probe's state can't mask another.
            adapter = factory()
            fresh = adapter.create_approval(request, now=now)
            probe = m.probes(fresh, now)[i]
            if probe.replay:
                if not _accepts(adapter, probe.attempt, now, request.policy_version):
                    results.append(CaseResult(m.name, m.invariant, probe.label, ERROR,
                                              "first (legitimate) execution was rejected"))
                    continue
            accepted = _accepts(adapter, probe.attempt, probe.now, probe.policy_version)
            results.append(CaseResult(
                m.name, m.invariant, probe.label,
                FAIL if accepted else PASS,
                "accepted unauthorized execution" if accepted else "rejected",
            ))
    return Report(results)
