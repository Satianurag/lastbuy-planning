"""Versioned, reproducible Foundry release. Never deletes shared Azure resources."""

import argparse
import hashlib
import io
import json
import os
import zipfile
from datetime import timedelta
from pathlib import Path

from azure.ai.projects import AIProjectClient, models
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
NAME = "lastbuy-analysis"
RECORD = ROOT / "evidence/lastbuy-agent-release.json"
FILES = [
    "hosted/requirements.txt",
    "hosted/main.py",
    "lastbuy/__init__.py",
    "lastbuy/domain.py",
    "lastbuy/solver.py",
    "lastbuy/agents.py",
    "lastbuy/reconciliation.py",
]


def archive():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zipped:
        for file in FILES:
            path = ROOT / file
            name = path.name if file.startswith("hosted/") else file
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(info, path.read_bytes())
    content = out.getvalue()
    sha = hashlib.sha256(content).hexdigest()
    release = ROOT / "evidence/releases" / f"{NAME}-{sha[:16]}.zip"
    release.parent.mkdir(exist_ok=True)
    release.write_bytes(content)
    return content, sha, release


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["package", "deploy", "status", "route"])
    parser.add_argument("--new-version", action="store_true")
    args = parser.parse_args()
    if args.action == "package":
        _, sha, path = archive()
        print(json.dumps({"archive": str(path), "sha256": sha}))
        return
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    with (
        AzureCliCredential(process_timeout=60) as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as client,
    ):
        if args.action == "deploy":
            if RECORD.exists() and not args.new_version:
                raise RuntimeError(
                    "Release exists. Inspect status, or explicitly request --new-version."
                )
            content, sha, path = archive()
            code = io.BytesIO(content)
            code.name = path.name
            version = client.agents.create_version_from_code(
                agent_name=NAME,
                definition=models.HostedAgentDefinition(
                    cpu="1",
                    memory="2Gi",
                    code_configuration=models.CodeConfiguration(
                        runtime="python_3_13",
                        entry_point=["python", "main.py"],
                        dependency_resolution=models.CodeDependencyResolution.REMOTE_BUILD,
                    ),
                    environment_variables={
                        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "false",
                        "AZURE_AI_MODEL_DEPLOYMENT_NAME": os.getenv(
                            "AZURE_AI_MODEL_DEPLOYMENT_NAME", "lastbuy-dev-mini"
                        ),
                    },
                    protocol_versions=[
                        models.ProtocolVersionRecord(
                            protocol="invocations", version="2.0.0"
                        )
                    ],
                    session_configuration=models.SessionConfiguration(
                        idle_timeout_seconds=timedelta(seconds=120)
                    ),
                ),
                code=code,
                code_zip_sha256=sha,
                description="LastBuy bounded evidence specialists and deterministic allocation. No ERP writes.",
            )
            data = {
                "agent": NAME,
                "version": version.version,
                "status": version.get("status"),
                "source_sha256": sha,
                "archive": str(path.relative_to(ROOT)),
                "routed": False,
            }
            RECORD.write_text(json.dumps(data, indent=2) + "\n")
        else:
            data = json.loads(RECORD.read_text())
            version = client.agents.get_version(
                agent_name=NAME, agent_version=data["version"]
            )
            data["status"] = version.get("status")
            if args.action == "route":
                if data["status"] != "active":
                    raise RuntimeError("Release is not active")
                client.agents.update_details(
                    agent_name=NAME,
                    agent_endpoint=models.AgentEndpointConfig(
                        version_selector=models.VersionSelector(
                            version_selection_rules=[
                                models.FixedRatioVersionSelectionRule(
                                    agent_version=data["version"],
                                    traffic_percentage=100,
                                )
                            ]
                        ),
                        protocol_configuration=models.ProtocolConfiguration(
                            invocations=models.InvocationsProtocolConfiguration()
                        ),
                    ),
                )
                data["routed"] = True
            RECORD.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
