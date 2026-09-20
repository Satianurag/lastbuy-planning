"""LastBuy Foundry analysis boundary: immutable inputs, no enterprise writes."""

import logging
from typing import Literal

from azure.ai.agentserver.invocations import InvocationAgentServerHost
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from lastbuy.agents import FoundryAnalyst
from lastbuy.domain import Contract, Snapshot, digest
from lastbuy.solver import solve

app = InvocationAgentServerHost()
analyst = FoundryAnalyst()
log = logging.getLogger("lastbuy.hosted")


class StageRequest(Contract):
    role: Literal["engineering", "service", "supply", "commitment"]
    snapshot: Snapshot


@app.invoke_handler
async def analyze(request: Request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 2_000_000:
            return JSONResponse({"error": "input_too_large"}, status_code=413)
    try:
        data = StageRequest.model_validate_json(body)
    except ValidationError:
        return JSONResponse({"error": "invalid_case_contract"}, status_code=422)
    try:
        calculation = solve(data.snapshot)
        result = await analyst.assess(data.role, data.snapshot, calculation)
        return JSONResponse(
            {
                "snapshot_sha256": digest(data.snapshot),
                "role": data.role,
                "result": result,
                "calculation": calculation if data.role == "commitment" else None,
            }
        )
    except Exception as error:
        log.error(
            "stage_failed case=%s role=%s error_type=%s",
            data.snapshot.case_id,
            data.role,
            type(error).__name__,
        )
        return JSONResponse(
            {"error": "analysis_failed", "error_type": type(error).__name__},
            # Non-success application result without platform 5xx replay. Durable
            # orchestration owns retries and reserves each admitted attempt.
            status_code=422,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088)
