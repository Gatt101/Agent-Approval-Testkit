import pytest
from conftest import NOW

from approval_testkit import ExecutionAttempt
from approval_testkit.mutations import MUTATIONS, REGISTRY, perturb


def test_seven_mutations_registered():
    assert list(REGISTRY) == ["actor", "tool", "arguments", "target", "expiry", "replay", "policy"]


@pytest.mark.parametrize("m", MUTATIONS, ids=lambda m: m.name)
def test_every_probe_differs_from_approved_execution(m, approval):
    baseline = (ExecutionAttempt.from_approval(approval), NOW, approval.request.policy_version)
    probes = m.probes(approval, NOW)
    assert probes
    for p in probes:
        assert p.replay or (p.attempt, p.now, p.policy_version) != baseline


def test_arguments_probes_cover_change_drop_and_inject(approval):
    labels = [p.label for p in REGISTRY["arguments"].probes(approval, NOW)]
    assert len(labels) == 2 * len(approval.request.args) + 1
    assert any("dropped" in label for label in labels)
    assert any("__injected" in label for label in labels)


def test_expiry_probe_is_after_expiry(approval):
    (p,) = REGISTRY["expiry"].probes(approval, NOW)
    assert p.now > approval.expires_at


@pytest.mark.parametrize("value", [True, 0, 5, 2.5, "x", None, [1]])
def test_perturb_always_changes_value(value):
    assert perturb(value) != value
