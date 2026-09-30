from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any

from approval_testkit.models import Approval, ExecutionAttempt


@dataclass(frozen=True)
class Probe:
    """One execution the verifier must reject."""

    label: str
    attempt: ExecutionAttempt
    now: datetime
    policy_version: str
    replay: bool = False  # runner executes the valid attempt first, then this one


@dataclass(frozen=True)
class Mutation:
    name: str
    invariant: str
    description: str
    probes: Callable[[Approval, datetime], list[Probe]]


def perturb(value: Any) -> Any:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value * 10 if value else 1
    if isinstance(value, str):
        return value + "-mutated"
    return "mutated"


def _probe(approval: Approval, now: datetime, label: str, **changes: Any) -> Probe:
    attempt = replace(ExecutionAttempt.from_approval(approval), **changes)
    return Probe(label, attempt, now, approval.request.policy_version)


def _actor(a: Approval, now: datetime) -> list[Probe]:
    actor = perturb(a.request.actor)
    return [_probe(a, now, f"actor -> {actor!r}", actor=actor)]


def _tool(a: Approval, now: datetime) -> list[Probe]:
    tool = perturb(a.request.tool)
    return [_probe(a, now, f"tool -> {tool!r}", tool=tool)]


def _target(a: Approval, now: datetime) -> list[Probe]:
    t = perturb(a.request.target)
    return [_probe(a, now, f"target -> {t!r}", target=t)]


def _arguments(a: Approval, now: datetime) -> list[Probe]:
    args = a.request.args
    probes = [
        _probe(a, now, f"args.{k} -> {perturb(v)!r}", args={**args, k: perturb(v)})
        for k, v in args.items()
    ]
    probes += [
        _probe(a, now, f"args.{k} dropped", args={x: v for x, v in args.items() if x != k})
        for k in args
    ]
    probes.append(_probe(a, now, "args.__injected added", args={**args, "__injected": True}))
    return probes


def _expiry(a: Approval, now: datetime) -> list[Probe]:
    late = a.expires_at + timedelta(seconds=1)
    return [replace(_probe(a, now, "executed 1s after expiry"), now=late)]


def _replay(a: Approval, now: datetime) -> list[Probe]:
    return [replace(_probe(a, now, "same approval executed twice"), replay=True)]


def _policy(a: Approval, now: datetime) -> list[Probe]:
    old = a.request.policy_version
    new = perturb(old)
    return [replace(_probe(a, now, f"policy {old!r} -> {new!r}"), policy_version=new)]


MUTATIONS = [
    Mutation("actor", "actor binding", "Different user/session presents the approval", _actor),
    Mutation("tool", "tool binding", "Approval used for a different tool", _tool),
    Mutation("arguments", "argument binding", "Arguments changed, dropped, or added", _arguments),
    Mutation("target", "target binding", "Resource/recipient/destination changed", _target),
    Mutation("expiry", "expiry enforcement", "Approval used after it expired", _expiry),
    Mutation("replay", "replay protection", "Approval reused after a successful run", _replay),
    Mutation("policy", "policy version binding", "Policy changed since approval", _policy),
]
REGISTRY = {m.name: m for m in MUTATIONS}
