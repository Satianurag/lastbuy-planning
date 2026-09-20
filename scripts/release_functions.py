"""Deploy frozen source then wire server-only export transport. Does not create spend resources."""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RG = "rg-anuragsati6476-5065"


def az(*args):
    p = subprocess.run(
        ["az", *args, "-o", "json", "--only-show-errors"],
        capture_output=True,
        text=True,
    )
    if p.returncode:
        raise RuntimeError(p.stderr[:1000])
    return json.loads(p.stdout) if p.stdout.strip() else None


agent = json.loads((ROOT / "evidence/lastbuy-agent-release.json").read_text())
assert agent["status"] == "active" and agent["routed"]
public = json.loads((ROOT / "evidence/function-public-settings.json").read_text())
public.update(
    LASTBUY_HOSTED_VERSION=agent["version"],
    LASTBUY_EXPORT_TRANSPORT="remote",
    LASTBUY_EXPORT_URL="https://lastbuy-export-4126.azurewebsites.net/api/exports",
)
key = az("functionapp", "keys", "list", "-g", RG, "-n", "lastbuy-export-4126")[
    "functionKeys"
]["default"]
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
    json.dump({**public, "LASTBUY_EXPORT_FUNCTION_KEY": key}, f)
    f.flush()
    az(
        "functionapp",
        "config",
        "appsettings",
        "set",
        "-g",
        RG,
        "-n",
        "lastbuy-dev-4126",
        "--settings",
        "@" + f.name,
    )
(ROOT / "evidence/function-public-settings.json").write_text(
    json.dumps(public, indent=2)
)
record = json.loads((ROOT / "evidence/functions-source-release.json").read_text())
az(
    "functionapp",
    "deployment",
    "source",
    "config-zip",
    "-g",
    RG,
    "-n",
    "lastbuy-dev-4126",
    "--src",
    str(ROOT / record["archive"]),
    "--build-remote",
    "true",
    "--timeout",
    "600",
)
print(
    json.dumps(
        {
            "deployed": record,
            "hosted_version": agent["version"],
            "export_transport": "remote",
        }
    ),
    flush=True,
)
