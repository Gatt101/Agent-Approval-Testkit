"""The fixed verifier: binds the whole action by hash; enforces expiry, policy, single use."""

import hashlib
import json
import uuid
from datetime import timedelta

from approval_testkit import Approval


def action_digest(actor, tool, args, target) -> str:
    canonical = json.dumps(
        {"actor": actor, "tool": tool, "args": args, "target": target},
        sort_keys=True, separators=(",", ":"), default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


class SecurePaymentVerifier:
    def __init__(self):
        self.approvals: dict[str, tuple[Approval, str]] = {}
        self.used: set[str] = set()  # ponytail: in-memory; use a DB unique constraint in production

    def create_approval(self, request, *, now):
        approval = Approval(uuid.uuid4().hex, request, now, now + timedelta(minutes=5))
        digest = action_digest(request.actor, request.tool, request.args, request.target)
        self.approvals[approval.id] = (approval, digest)
        return approval

    def verify(self, attempt, *, now, policy_version):
        entry = self.approvals.get(attempt.approval_id)
        if entry is None or attempt.approval_id in self.used:
            return False
        approval, digest = entry
        if now >= approval.expires_at or policy_version != approval.request.policy_version:
            return False
        if action_digest(attempt.actor, attempt.tool, attempt.args, attempt.target) != digest:
            return False
        self.used.add(attempt.approval_id)
        return True
