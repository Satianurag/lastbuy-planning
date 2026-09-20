from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from lastbuy.api import create_app
from lastbuy.domain import Actor
from lastbuy.fixtures import demo_snapshot
from lastbuy.service import Workflow
from lastbuy.store import Store


@pytest.fixture
def entra(tmp_path, monkeypatch):
    tenant, audience = "test-tenant", "test-api"
    monkeypatch.setenv("AZURE_TENANT_ID", tenant)
    monkeypatch.setenv("LASTBUY_API_AUDIENCE", audience)
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        jwt,
        "PyJWKClient",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=private.public_key())
        ),
    )
    store = Store("sqlite:///" + str(tmp_path / "entra.db"))
    actor = Actor(
        id="entra-person",
        name="Actual authenticated planner",
        organization="NORTHSTAR",
        roles=["planner"],
        authority_minor=0,
    )
    store.register(actor)
    workflow = Workflow(store, None, None)
    workflow.create(demo_snapshot(), actor)
    app = create_app(workflow, demo=False)

    def token(**overrides):
        now = datetime.now(UTC)
        claims = {
            "aud": audience,
            "iss": f"https://login.microsoftonline.com/{tenant}/v2.0",
            "tid": tenant,
            "oid": actor.id,
            "scp": "access_as_user",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            **overrides,
        }
        return jwt.encode(claims, private, algorithm="RS256")

    with TestClient(app, base_url="https://lastbuy.test") as client:
        yield client, token


def test_real_jwt_validation_and_no_demo_personas(entra):
    client, token = entra
    assert client.get("/api/session").json() == {"mode": "entra", "actor": None}
    assert client.get("/api/cases").status_code == 401
    client.headers["Authorization"] = "Bearer " + token()
    response = client.get("/api/session").json()
    assert response["actor"]["id"] == "entra-person" and "personas" not in response
    assert client.post("/api/session", json={"persona": "finance"}).status_code == 404
    assert client.get("/api/cases").status_code == 200
    assert (
        client.post(
            "/api/cases", json=demo_snapshot().model_dump(mode="json")
        ).status_code
        == 403
    )
    assert client.post("/api/cases/LTB-2026-017/demo-reservation").status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "other-api"},
        {"iss": "https://attacker.invalid"},
        {"tid": "other-tenant"},
        {"exp": datetime.now(UTC) - timedelta(seconds=30)},
        {"oid": "unprovisioned"},
        {"scp": ""},
    ],
)
def test_wrong_or_unprovisioned_entra_tokens_rejected(entra, overrides):
    client, token = entra
    client.headers["Authorization"] = "Bearer " + token(**overrides)
    assert client.get("/api/cases").status_code == 401
