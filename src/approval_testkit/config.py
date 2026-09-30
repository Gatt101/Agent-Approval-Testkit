from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from approval_testkit.adapter import ConfigError
from approval_testkit.models import ApprovalRequest
from approval_testkit.mutations import REGISTRY, Mutation


@dataclass
class Config:
    adapter: str
    request: ApprovalRequest
    mutations: list[Mutation]


def _read(path: Path) -> dict:
    own = path / "approval-test.toml"
    if own.is_file():
        return tomllib.loads(own.read_text(encoding="utf-8"))
    pyproject = path / "pyproject.toml"
    if pyproject.is_file():
        section = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {})
        if "approval-test" in section:
            return section["approval-test"]
    raise ConfigError(f"no approval-test.toml or [tool.approval-test] found in {path}")


def load_config(path: Path) -> Config:
    try:
        data = _read(path)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"invalid TOML: {e}") from e

    if "adapter" not in data:
        raise ConfigError("missing required key: adapter = \"module:attr\"")
    req = data.get("request")
    if not isinstance(req, dict):
        raise ConfigError("missing required table: [request]")
    missing = [k for k in ("actor", "tool", "target") if k not in req]
    if missing:
        raise ConfigError(f"[request] missing keys: {', '.join(missing)}")

    names = data.get("mutations", list(REGISTRY))
    unknown = [n for n in names if n not in REGISTRY]
    if unknown:
        raise ConfigError(f"unknown mutations: {', '.join(unknown)} (known: {', '.join(REGISTRY)})")

    request = ApprovalRequest(
        actor=str(req["actor"]),
        tool=str(req["tool"]),
        args=dict(req.get("args", {})),
        target=str(req["target"]),
        policy_version=str(req.get("policy_version", "1")),
    )
    return Config(data["adapter"], request, [REGISTRY[n] for n in names])
