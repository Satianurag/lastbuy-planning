"""Drive the generator's failure/expiry paths without Azure or paid calls."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from lastbuy.orchestration import lastbuy_orchestrator_v2


class Context:
    current_utc_datetime = datetime(2026, 9, 20, tzinfo=UTC)

    def __init__(self):
        self.timer = SimpleNamespace(is_completed=False, cancelled=False)
        self.timer.cancel = lambda: setattr(self.timer, "cancelled", True)

    def get_input(self):
        return {"case_id": "CASE", "run_id": "RUN"}

    def set_custom_status(self, status):
        pass

    def call_activity_with_retry(self, name, retry, request):
        return (name, request)

    def call_activity(self, name, request):
        return (name, request)

    def create_timer(self, deadline):
        return self.timer

    def wait_for_external_event(self, name):
        return ("event", name)

    def task_any(self, tasks):
        return ("any", tasks)


def waiting():
    context = Context()
    generator = lastbuy_orchestrator_v2(context)
    step = next(generator)
    for _ in range(4):
        assert step[0] == "analyze_stage"
        step = generator.send({"status": "COMPLETE"})
    assert step[0] == "finalize_analysis"
    step = generator.send({"status": "READY_FOR_APPROVAL", "plan_sha256": "a" * 64})
    assert step[0] == "read_approval_status"
    return context, generator


def test_expiry_calls_authoritative_transition():
    context, run = waiting()
    assert run.send({"status": "APPROVAL_PENDING"})[0] == "any"
    context.timer.is_completed = True
    assert run.send(context.timer)[0] == "expire_approval_wait"
    with pytest.raises(StopIteration) as finished:
        run.send({"status": "APPROVAL_WAIT_EXPIRED"})
    assert finished.value.value["status"] == "APPROVAL_WAIT_EXPIRED"
    assert not context.timer.cancelled


def test_failed_wait_cleans_up_pending_timer_and_preserves_cancelled_state():
    context, run = waiting()
    assert (
        run.throw(RuntimeError("provider unavailable"))[0] == "record_analysis_failure"
    )
    with pytest.raises(StopIteration) as finished:
        run.send({"status": "CANCELLED"})
    assert finished.value.value["status"] == "CANCELLED"
    assert context.timer.cancelled
