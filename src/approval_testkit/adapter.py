from __future__ import annotations

import hashlib
import importlib
import importlib.util
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from approval_testkit.models import Approval, ApprovalRequest, ExecutionAttempt


class ApprovalAdapter(Protocol):
    """The only thing your app must expose. Raising from verify() counts as a rejection."""

    def create_approval(self, request: ApprovalRequest, *, now: datetime) -> Approval: ...

    def verify(self, attempt: ExecutionAttempt, *, now: datetime, policy_version: str) -> bool: ...


AdapterFactory = Callable[[], ApprovalAdapter]


class ConfigError(Exception):
    pass


def load_adapter(spec: str, base_path: Path) -> AdapterFactory:
    """Resolve "module:attr" to a zero-arg factory (a class works); one adapter per probe."""
    module_name, sep, attr = spec.partition(":")
    if not sep or not module_name or not attr:
        raise ConfigError(f"adapter must look like 'module:attr', got {spec!r}")

    base_path = base_path.resolve()
    file = base_path / (module_name.replace(".", "/") + ".py")
    try:
        if file.is_file():
            # Unique module name so two projects' "verifier.py" never collide in sys.modules.
            unique = f"_approval_adapter_{hashlib.sha1(str(file).encode()).hexdigest()[:10]}"
            loader_spec = importlib.util.spec_from_file_location(unique, file)
            module = importlib.util.module_from_spec(loader_spec)
            sys.path.insert(0, str(base_path))
            try:
                loader_spec.loader.exec_module(module)
            finally:
                sys.path.remove(str(base_path))
        else:
            module = importlib.import_module(module_name)
    except Exception as e:
        raise ConfigError(f"could not import adapter module {module_name!r}: {e}") from e

    factory = getattr(module, attr, None)
    if not callable(factory):
        raise ConfigError(f"{spec!r} is not a callable adapter factory")
    return factory
