"""A realistic-looking approval verifier with two classic bugs.

BUG 1: arguments are not bound, so an approved $100 payment can execute as $1000.
BUG 2: approvals are not single-use, so one approval can be replayed forever.
"""

import uuid
from datetime import timedelta

from approval_testkit import Approval


class VulnerablePaymentVerifier:
    def __init__(self):
        self.approvals: dict[str, Approval] = {}

    def create_approval(self, request, *, now):
        approval = Approval(uuid.uuid4().hex, request, now, now + timedelta(minutes=5))
        self.approvals[approval.id] = approval
        return approval

    def verify(self, attempt, *, now, policy_version):
        approval = self.approvals.get(attempt.approval_id)
        if approval is None:
            return False
        req = approval.request
        return (
            attempt.actor == req.actor
            and attempt.tool == req.tool
            and attempt.target == req.target
            and now < approval.expires_at
            and policy_version == req.policy_version
        )
