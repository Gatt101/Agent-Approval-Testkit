from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from approval_testkit import Approval, ApprovalRequest
from approval_testkit.adapter import load_adapter

EXAMPLES = Path(__file__).parent.parent / "examples"
VULNERABLE = EXAMPLES / "vulnerable_payment_agent"
SECURE = EXAMPLES / "secure_payment_agent"
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
REQUEST = ApprovalRequest(
    actor="user:alice", tool="send_payment",
    args={"amount": 100, "currency": "USD"}, target="acct_1", policy_version="v1",
)


@pytest.fixture
def approval():
    return Approval("appr-1", REQUEST, NOW, NOW + timedelta(minutes=5))


@pytest.fixture
def vulnerable():
    return load_adapter("verifier:VulnerablePaymentVerifier", VULNERABLE)


@pytest.fixture
def secure():
    return load_adapter("verifier:SecurePaymentVerifier", SECURE)
