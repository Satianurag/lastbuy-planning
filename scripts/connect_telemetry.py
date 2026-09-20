"""Connect the dedicated development App Insights resource without logging credentials."""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = "rg-anuragsati6476-5065"


def main():
    app = json.loads(
        subprocess.check_output(
            [
                "az",
                "monitor",
                "app-insights",
                "component",
                "show",
                "--app",
                "lastbuy-dev-insights",
                "--resource-group",
                GROUP,
                "--output",
                "json",
            ]
        )
    )
    connection = {
        "properties": {
            "category": "AppInsights",
            "target": app["id"],
            "authType": "ApiKey",
            "credentials": {"key": app["connectionString"]},
            "metadata": {"ApiType": "Azure", "ResourceId": app["id"]},
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as file:
        json.dump(connection, file)
        file.flush()
        subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "put",
                "--url",
                "https://management.azure.com"
                + json.loads((ROOT / "evidence/azure-project.json").read_text())["id"]
                + "/connections/lastbuy-dev-telemetry?api-version=2026-05-01",
                "--body",
                "@" + file.name,
                "--output",
                "none",
            ],
            check=True,
        )
    record = {
        "connection": "lastbuy-dev-telemetry",
        "target": app["id"],
        "credential_handling": "Temporary 0600 file removed; no credential saved in planning workspace",
    }
    (ROOT / "evidence/telemetry-connection.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
