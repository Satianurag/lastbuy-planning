"""Archive primary Microsoft documentation for this planning audit; no Azure mutations."""

import concurrent.futures
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "foundry-overview": "what-is-foundry",
    "agent-overview": "agents/overview",
    "hosted-agents": "agents/concepts/hosted-agents",
    "hosted-quickstart": "agents/quickstarts/quickstart-hosted-agent",
    "limits-quotas-regions": "agents/concepts/limits-quotas-regions",
    "networking-options": "agents/concepts/networking-options",
    "networking-deep-dive": "agents/concepts/agents-networking-deep-dive",
    "resilience": "agents/concepts/long-running-agent-resilience",
    "state-store": "agents/concepts/agent-state-store",
    "dev-tools": "how-to/develop/install-cli-sdk",
    "deploy-hosted": "agents/how-to/deploy-hosted-agent",
    "vs-code-workflow": "how-to/develop/vs-code-agents-workflow-pro-code",
    "toolbox": "agents/concepts/toolbox-overview",
    "agent-identity": "agents/concepts/agent-identity",
    "hosted-permissions": "agents/concepts/hosted-agent-permissions",
    "guardrails": "guardrails/guardrails-overview",
    "hosted-guardrails": "agents/how-to/add-hosted-agent-guardrails",
    "tracing": "observability/concepts/trace-agent-concept",
    "monitoring": "observability/how-to/how-to-monitor-agents-dashboard",
    "optimizer": "agents/concepts/agent-optimizer-overview",
    "agent-lifecycle": "agents/concepts/development-lifecycle",
    "model-catalog": "concepts/foundry-models-overview",
    "foundry-iq": "agents/concepts/what-is-foundry-iq",
    "ga-status": "concepts/general-availability",
    "capability-reference": "concepts/capability-reference",
    "capability-map": "concepts/capabilities",
    "hosted-evaluation": "observability/quickstarts/quickstart-evaluate-hosted-agent",
    "hosted-cicd": "agents/quickstarts/set-up-cicd-hosted-agent",
}


def capture(item):
    name, path = item
    url = "https://learn.microsoft.com/en-us/azure/foundry/" + path
    request = urllib.request.Request(url, headers={"Accept": "text/markdown"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read()
            final = response.url
        (ROOT / "evidence" / (name + ".md")).write_bytes(body)
        return {
            "name": name,
            "url": url,
            "final_url": final,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "status": "captured",
        }
    except OSError as exc:
        return {"name": name, "url": url, "status": "failed", "error": str(exc)}


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records = list(pool.map(capture, PATHS.items()))
    payload = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": records,
    }
    (ROOT / "evidence" / "docs-manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    for record in records:
        print(
            record["name"], record["status"], record.get("bytes", record.get("error"))
        )
