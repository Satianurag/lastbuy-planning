"""Read billing, never infer zero usage from missing data or throttling."""

import json
from pathlib import Path

import requests
from azure.identity import AzureCliCredential

root = Path(__file__).resolve().parents[1]
credential = AzureCliCredential(process_timeout=60)
token = credential.get_token("https://management.azure.com/.default").token
scope = "/subscriptions/73cf0b28-d8af-4012-94d0-e7f7fc3ddd36/resourceGroups/rg-anuragsati6476-5065"
r = requests.post(
    "https://management.azure.com"
    + scope
    + "/providers/Microsoft.CostManagement/query?api-version=2023-11-01",
    headers={"Authorization": "Bearer " + token},
    json={
        "type": "ActualCost",
        "timeframe": "MonthToDate",
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ResourceId"}],
        },
    },
    timeout=45,
)
result = {
    "http_status": r.status_code,
    "scope": "Whole existing resource group, not all costs attributable to LastBuy",
    "body": r.json(),
}
(root / "evidence/cost-management-current.json").write_text(
    json.dumps(result, indent=2)
)
print(json.dumps(result)[:6000])
credential.close()
