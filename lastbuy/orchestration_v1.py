"""Deterministic Durable Functions generator: no model, network or wall-clock I/O."""

from datetime import timedelta

import azure.durable_functions as df


def lastbuy_orchestrator(context):
    request = context.get_input()
    retry = df.RetryOptions(
        first_retry_interval_in_milliseconds=5000, max_number_of_attempts=2
    )
    try:
        for role in ("engineering", "service", "supply", "commitment"):
            context.set_custom_status({"phase": "analysis", "role": role})
            yield context.call_activity_with_retry(
                "analyze_stage", retry, {**request, "role": role}
            )
        result = yield context.call_activity_with_retry(
            "finalize_analysis", retry, request
        )
        if result["status"] != "READY_FOR_APPROVAL":
            return result
        context.set_custom_status(
            {
                "phase": "waiting_for_human_approvals",
                "plan_sha256": result["plan_sha256"],
            }
        )
        deadline = context.current_utc_datetime + timedelta(hours=24)
        expiry = context.create_timer(deadline)
        while True:
            state = yield context.call_activity("read_approval_status", request)
            if state["status"] not in {"READY_FOR_APPROVAL", "APPROVAL_PENDING"}:
                expiry.cancel()
                return state
            notification = context.wait_for_external_event("decision_changed")
            winner = yield context.task_any([notification, expiry])
            if winner == expiry:
                # Read authoritative state once more to handle an approval at the boundary.
                state = yield context.call_activity("read_approval_status", request)
                if state["status"] == "APPROVED":
                    return state
                return {"status": "APPROVAL_WAIT_EXPIRED"}
    except Exception:
        yield context.call_activity("record_analysis_failure", request)
        return {"status": "ANALYSIS_FAILED"}
