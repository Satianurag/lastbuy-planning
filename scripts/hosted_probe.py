"""Explicit lifecycle for a setup-only Foundry hosted agent. Never deploys LastBuy.

Creates only lastbuy-setup-check; saves version before any following action.
Status, route, invoke and cleanup are separate so a timeout cannot cause an
unnoticed duplicate deployment. No tokens or keys are logged or saved.
"""

import argparse
import hashlib
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from azure.ai.projects import AIProjectClient, models
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://anuragsati6476-4126-resource.services.ai.azure.com/api/projects/anuragsati6476-4126"
NAME = "lastbuy-setup-check"
RECORD = ROOT / "evidence/hosted-probe.json"


def save(data):
    RECORD.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["create", "status", "route", "invoke", "cleanup"]
    )
    action = parser.parse_args().action
    with (
        AzureCliCredential(process_timeout=60) as credential,
        AIProjectClient(endpoint=ENDPOINT, credential=credential) as client,
    ):
        if action == "create":
            if RECORD.exists():
                raise RuntimeError(
                    "Existing probe record: inspect its status before creating anything."
                )
            try:
                client.agents.get(agent_name=NAME)
            except ResourceNotFoundError:
                pass
            else:
                raise RuntimeError(
                    "Probe name already exists; inspect before changing it."
                )
            archive = io.BytesIO()
            archive.name = "lastbuy-setup-check.zip"
            source = ROOT / "spikes/invocations-preflight"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                for name in ["main.py", "requirements.txt"]:
                    output.write(source / name, name)
            archive.seek(0)
            code_hash = hashlib.sha256(archive.getvalue()).hexdigest()
            definition = models.HostedAgentDefinition(
                cpu="0.5",
                memory="1Gi",
                code_configuration=models.CodeConfiguration(
                    runtime="python_3_13",
                    entry_point=["python", "main.py"],
                    dependency_resolution=models.CodeDependencyResolution.REMOTE_BUILD,
                ),
                environment_variables={
                    "AZURE_AI_MODEL_DEPLOYMENT_NAME": "lastbuy-dev-mini"
                },
                protocol_versions=[
                    models.ProtocolVersionRecord(
                        protocol="invocations", version="2.0.0"
                    )
                ],
                session_configuration=models.SessionConfiguration(
                    idle_timeout_seconds=timedelta(seconds=120)
                ),
            )
            version = client.agents.create_version_from_code(
                agent_name=NAME,
                definition=definition,
                code=archive,
                code_zip_sha256=code_hash,
                description="Temporary setup probe: no enterprise data or LastBuy business logic.",
            )
            save(
                {
                    "agent": NAME,
                    "version": version.version,
                    "status": version.get("status"),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "source_sha256": code_hash,
                }
            )
            return
        data = json.loads(RECORD.read_text())
        if data["agent"] != NAME:
            raise RuntimeError("Unexpected agent in probe record")
        version = data["version"]
        if action == "status":
            details = client.agents.get_version(agent_name=NAME, agent_version=version)
            data["status"] = details.get("status")
            data["checked_at"] = datetime.now(timezone.utc).isoformat()
            save(data)
        elif action == "route":
            details = client.agents.get_version(agent_name=NAME, agent_version=version)
            if details.get("status") != "active":
                raise RuntimeError("Probe version is not active")
            client.agents.update_details(
                agent_name=NAME,
                agent_endpoint=models.AgentEndpointConfig(
                    version_selector=models.VersionSelector(
                        version_selection_rules=[
                            models.FixedRatioVersionSelectionRule(
                                agent_version=version, traffic_percentage=100
                            )
                        ]
                    ),
                    protocol_configuration=models.ProtocolConfiguration(
                        invocations=models.InvocationsProtocolConfiguration()
                    ),
                ),
            )
            data["routed"] = True
            save(data)
        elif action == "invoke":
            token = credential.get_token("https://ai.azure.com/.default")
            url = (
                ENDPOINT
                + "/agents/"
                + NAME
                + "/endpoint/protocols/invocations?api-version=v1"
            )
            response = requests.post(
                url,
                headers={"Authorization": "Bearer " + token.token},
                json={"nonce": "setup-cloud-foundry-20260920"},
                timeout=(15, 180),
            )
            result = {
                "http_status": response.status_code,
                "body": response.json(),
                "version": version,
                "at": datetime.now(timezone.utc).isoformat(),
            }
            (ROOT / "evidence/cloud-probe-result.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print(json.dumps(result, indent=2))
            response.raise_for_status()
            if result["body"].get("ok") is not True:
                raise RuntimeError("Cloud probe did not verify its tool result")
        elif action == "cleanup":
            client.agents.delete_version(
                agent_name=NAME, agent_version=version, force=True
            )
            data["status"] = "deleted"
            data["deleted_at"] = datetime.now(timezone.utc).isoformat()
            save(data)


if __name__ == "__main__":
    main()
