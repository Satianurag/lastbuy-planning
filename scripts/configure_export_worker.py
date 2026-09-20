"""Operator-only setup for the independent synthetic ERP identity; no model access."""

import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from sqlalchemy import text

from lastbuy.sql_erp import ERPBase
from lastbuy.store import Store

ROOT = Path(__file__).resolve().parents[1]
RG = "rg-anuragsati6476-5065"
APP = "lastbuy-export-4126"


def az(*args):
    result = subprocess.run(
        ["az", *args, "-o", "json", "--only-show-errors"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr[:1800])
    return json.loads(result.stdout) if result.stdout.strip() else None


identity = az("functionapp", "identity", "show", "-g", RG, "-n", APP)
sp = az("ad", "sp", "show", "--id", identity["principalId"])
record = {
    "objectId": sp["id"],
    "clientId": sp["appId"],
    "displayName": sp["displayName"],
}
(ROOT / "evidence/export-identity.json").write_text(json.dumps(record, indent=2))
account = az("storage", "account", "show", "-g", RG, "-n", "lastbuydev4126")["id"]
# Pre-create host containers so this identity never needs archive-wide ownership.
for container in ["azure-webjobs-hosts", "azure-webjobs-secrets", "export-deployments"]:
    az(
        "storage",
        "container",
        "create",
        "--account-name",
        "lastbuydev4126",
        "--auth-mode",
        "login",
        "-n",
        container,
    )
    az(
        "role",
        "assignment",
        "create",
        "--assignee-object-id",
        sp["id"],
        "--assignee-principal-type",
        "ServicePrincipal",
        "--role",
        "Storage Blob Data Owner"
        if container.startswith("azure-")
        else "Storage Blob Data Contributor",
        "--scope",
        account + "/blobServices/default/containers/" + container,
    )
az(
    "role",
    "assignment",
    "create",
    "--assignee-object-id",
    sp["id"],
    "--assignee-principal-type",
    "ServicePrincipal",
    "--role",
    "Storage Blob Data Reader",
    "--scope",
    account + "/blobServices/default/containers/snapshots",
)
# The CLI create command may grant broad deployment storage contributor. Remove that exact grant.
for grant in az(
    "role", "assignment", "list", "--assignee", sp["id"], "--scope", account
):
    if (
        grant["scope"].lower() == account.lower()
        and grant["roleDefinitionName"] == "Storage Blob Data Contributor"
    ):
        az("role", "assignment", "delete", "--ids", grant["id"])
az(
    "functionapp",
    "vnet-integration",
    "add",
    "-g",
    RG,
    "-n",
    APP,
    "--vnet",
    "lastbuy-dev-vnet",
    "--subnet",
    "functions",
)
settings = json.loads((ROOT / "evidence/function-public-settings.json").read_text())
url = settings["LASTBUY_DATABASE_URL"]
erp_url = url.replace("/lastbuy?", "/lastbuy-erp-sim?")
primary = Store(url, initialize=False)
erp = Store(erp_url, initialize=False)
ERPBase.metadata.create_all(erp.engine)
sid = uuid.UUID(sp["appId"]).bytes_le.hex()
for store in [primary, erp]:
    with store.engine.begin() as conn:
        conn.execute(
            text(
                f"IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name='lastbuy-export') CREATE USER [lastbuy-export] WITH SID=0x{sid}, TYPE=E"
            )
        )
        actual = conn.execute(
            text(
                "SELECT CONVERT(varchar(36),CAST(sid AS uniqueidentifier)) FROM sys.database_principals WHERE name='lastbuy-export'"
            )
        ).scalar_one()
        assert actual.lower() == sp["appId"].lower()
        if store is primary:
            for table in [
                "cases",
                "people",
                "approvals",
                "plan_versions",
                "outbox",
                "audit",
            ]:
                conn.execute(text(f"GRANT SELECT ON dbo.[{table}] TO [lastbuy-export]"))
            for table in ["cases", "outbox"]:
                conn.execute(text(f"GRANT UPDATE ON dbo.[{table}] TO [lastbuy-export]"))
            conn.execute(text("GRANT INSERT ON dbo.audit TO [lastbuy-export]"))
        else:
            conn.execute(
                text(
                    "GRANT SELECT, INSERT ON dbo.synthetic_requisitions TO [lastbuy-export]"
                )
            )
public = {
    k: settings[k]
    for k in [
        "AzureWebJobsStorage__accountName",
        "AzureWebJobsStorage__credential",
        "LASTBUY_DATABASE_URL",
        "LASTBUY_SCHEMA_MODE",
        "LASTBUY_ARCHIVE_URL",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
    ]
}
public["LASTBUY_ERP_DATABASE_URL"] = erp_url
# Connection string is handled in memory and protected temporary file; never printed.
insights = az(
    "monitor",
    "app-insights",
    "component",
    "show",
    "-g",
    RG,
    "-a",
    "lastbuy-dev-insights",
)
private = {
    **public,
    "APPLICATIONINSIGHTS_CONNECTION_STRING": insights["connectionString"],
}
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
    json.dump(private, handle)
    handle.flush()
    az(
        "functionapp",
        "config",
        "appsettings",
        "set",
        "-g",
        RG,
        "-n",
        APP,
        "--settings",
        "@" + handle.name,
    )
az(
    "functionapp",
    "config",
    "appsettings",
    "delete",
    "-g",
    RG,
    "-n",
    APP,
    "--setting-names",
    "AzureWebJobsStorage",
)
(ROOT / "evidence/export-public-settings.json").write_text(json.dumps(public, indent=2))
primary.engine.dispose()
erp.engine.dispose()
print(
    "Export identity configured: no model role, archive reader, primary ledger scoped permissions, separate synthetic ERP database."
)
