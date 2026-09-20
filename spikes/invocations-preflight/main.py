"""Setup-only probe, adapted from Microsoft's Foundry Invocations basic sample.

No LastBuy business logic or enterprise data. The probe verifies a real model tool
call and returns an objectively checkable result.
"""

import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.ai.agentserver.invocations import InvocationAgentServerHost
from azure.identity import AzureCliCredential, DefaultAzureCredential
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse


class ProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nonce: str = Field(pattern=r"^setup-[a-z0-9-]{1,50}$")


app = InvocationAgentServerHost()


@app.invoke_handler
async def probe(request: Request):
    try:
        payload = ProbeRequest.model_validate(await request.json())
    except (ValueError, ValidationError):
        return JSONResponse({"error": "invalid_probe_request"}, status_code=422)
    calls = []

    def setup_probe() -> str:
        """Read the diagnostic nonce. Call this to obtain the verification value."""
        calls.append("setup_probe")
        return payload.nonce

    credential = (
        AzureCliCredential(process_timeout=60)
        if os.getenv("LASTBUY_LOCAL_PROBE") == "1"
        else DefaultAzureCredential()
    )
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )
    try:
        agent = Agent(
            client=client,
            instructions="Call setup_probe exactly once. Return only its result.",
            tools=[setup_probe],
            default_options={"store": False, "max_output_tokens": 256},
        )
        result = await agent.run("Run the setup diagnostic.")
        passed = calls == ["setup_probe"] and payload.nonce == result.text.strip()
        return JSONResponse(
            {
                "ok": passed,
                "nonce": payload.nonce,
                "tool_calls": calls,
                "answer": result.text,
            },
            status_code=200 if passed else 502,
        )
    finally:
        credential.close()


if __name__ == "__main__":
    app.run(host=os.getenv("LASTBUY_PROBE_HOST", "0.0.0.0"), port=8088)
