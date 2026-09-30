from datetime import timedelta

from conftest import NOW, REQUEST

from approval_testkit import Approval
from approval_testkit.models import ERROR, FAIL, PASS
from approval_testkit.runner import run_all


def test_secure_verifier_passes_every_invariant(secure):
    report = run_all(secure, REQUEST, now=NOW)
    assert set(report.invariants().values()) == {PASS}
    assert len(report.invariants()) == 7
    assert report.exit_code == 0


def test_vulnerable_verifier_fails_arguments_and_replay(vulnerable):
    report = run_all(vulnerable, REQUEST, now=NOW)
    assert sorted(report.failed) == ["argument binding", "replay protection"]
    assert report.exit_code == 1


def test_amount_mutation_accepted_by_vulnerable_rejected_by_secure(vulnerable, secure):
    def amount_status(factory):
        report = run_all(factory, REQUEST, now=NOW)
        return next(r.status for r in report.results if r.probe.startswith("args.amount ->"))

    assert amount_status(vulnerable) == FAIL
    assert amount_status(secure) == PASS


class _Base:
    def __init__(self):
        self.approvals = {}
        self.used = set()

    def create_approval(self, request, *, now):
        a = Approval(str(len(self.approvals)), request, now, now + timedelta(minutes=5))
        self.approvals[a.id] = a
        return a


class RejectAll(_Base):
    def verify(self, attempt, *, now, policy_version):
        return False


class AcceptAll(_Base):
    def verify(self, attempt, *, now, policy_version):
        return True


class RaisesOnDeny(_Base):
    def verify(self, attempt, *, now, policy_version):
        a = self.approvals[attempt.approval_id]
        if (attempt.actor, attempt.tool, attempt.args, attempt.target) != (
            a.request.actor, a.request.tool, a.request.args, a.request.target
        ) or now >= a.expires_at or policy_version != a.request.policy_version:
            raise PermissionError("denied")
        if a.id in self.used:
            raise PermissionError("replay")
        self.used.add(a.id)
        return True


def test_reject_all_verifier_is_an_error_not_a_pass():
    report = run_all(RejectAll, REQUEST, now=NOW)
    assert report.results[0].status == ERROR
    assert report.exit_code == 1


def test_accept_all_verifier_fails_everything():
    report = run_all(AcceptAll, REQUEST, now=NOW)
    assert set(report.invariants().values()) == {FAIL}


def test_raising_counts_as_rejection():
    report = run_all(RaisesOnDeny, REQUEST, now=NOW)
    assert report.exit_code == 0


def test_mutation_subset(secure):
    from approval_testkit.mutations import REGISTRY

    report = run_all(secure, REQUEST, [REGISTRY["replay"]], now=NOW)
    assert list(report.invariants()) == ["replay protection"]
