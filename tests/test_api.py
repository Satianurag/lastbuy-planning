import pytest
from fastapi.testclient import TestClient

from lastbuy.api import create_app
from lastbuy.erp import SyntheticERP
from lastbuy.fixtures import FIXTURE_CLOCK
from lastbuy.service import Workflow
from lastbuy.store import Store


class Analyst:
    async def assess(self, role, snapshot, calculation):
        return {
            "assessment": {
                "role": role,
                "summary": "Explicit API test double",
                "evidence": ["pcn"],
                "findings": [],
            },
            "source": "test-double",
        }


@pytest.fixture
def client(tmp_path):
    workflow = Workflow(
        Store("sqlite:///" + str(tmp_path / "test.db")),
        Analyst(),
        SyntheticERP(str(tmp_path / "erp.db")),
        clock=lambda: FIXTURE_CLOCK,
    )
    app = create_app(workflow, demo=True)
    with TestClient(
        app, base_url="http://127.0.0.1", client=("127.0.0.1", 55555)
    ) as client:
        yield client


def login(client, persona="planner"):
    client.headers["Origin"] = "http://127.0.0.1"
    r = client.post("/api/session", json={"persona": persona})
    assert r.status_code == 200
    client.headers["X-CSRF-Token"] = r.json()["csrf"]


def test_authentication_required(client):
    assert client.get("/api/cases").status_code == 401
    assert client.get("/api/cases/LTB-2026-017/packet").status_code == 401


def test_cross_origin_login_rejected(client):
    r = client.post(
        "/api/session",
        json={"persona": "finance"},
        headers={"Origin": "https://attacker.invalid"},
    )
    assert r.status_code == 403


def test_csrf_and_origin_required_for_mutation(client):
    login(client)
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/cases/LTB-2026-017/analyze").status_code == 403


def test_role_switch_replaces_csrf_token(client):
    login(client)
    original = client.headers["X-CSRF-Token"]
    login(client, "finance")
    assert original != client.headers["X-CSRF-Token"]
    assert (
        client.post(
            "/api/cases/LTB-2026-017/analyze", headers={"X-CSRF-Token": original}
        ).status_code
        == 403
    )


def test_approver_cannot_start_or_modify_case(client):
    login(client, "engineering")
    assert client.post("/api/cases/LTB-2026-017/analyze").status_code == 403
    assert client.post("/api/cases/LTB-2026-017/demo-reservation").status_code == 403


def test_source_change_creates_valid_hashed_evidence(client):
    login(client)
    before = client.get("/api/cases/LTB-2026-017").json()
    after = client.post("/api/cases/LTB-2026-017/demo-reservation")
    assert after.status_code == 200
    body = after.json()
    assert body["snapshot_sha256"] != before["snapshot_sha256"]
    assert body["snapshot"]["lots"][0]["reserved"] == 1000
    assert body["audit_valid"]


def test_stale_edit_revision_rejected(client):
    login(client)
    before = client.get("/api/cases/LTB-2026-017").json()
    client.post("/api/cases/LTB-2026-017/demo-reservation")
    snapshot = before["snapshot"]
    snapshot["source_revision"] += 2
    result = client.put(
        "/api/cases/LTB-2026-017/snapshot",
        json={"expected_revision": before["revision"], "snapshot": snapshot},
    )
    assert result.status_code == 409


def test_browser_security_headers_and_static_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/style.css").status_code == 200
    assert client.get("/api/session").headers["Cache-Control"] == "no-store"


def test_host_rebinding_rejected(client):
    assert client.get("/", headers={"Host": "attacker.invalid"}).status_code == 400


def test_non_loopback_demo_identity_is_forbidden(tmp_path):
    workflow = Workflow(
        Store("sqlite:///:memory:"), Analyst(), SyntheticERP(str(tmp_path / "erp.db"))
    )
    with TestClient(
        create_app(workflow, demo=True),
        base_url="http://127.0.0.1",
        client=("10.0.0.4", 12345),
    ) as remote:
        assert remote.get("/api/session").status_code == 403


def test_chunked_oversize_input_rejected_before_json_parse(client):
    login(client)
    response = client.post(
        "/api/cases", content=iter([b"x" * 1_100_000, b"y" * 1_100_000])
    )
    assert response.status_code == 413


def test_import_preview_is_read_only_and_reviewed_create_is_explicit(client):
    login(client)
    snapshot = client.get("/api/import/template").json()
    preview = client.post("/api/import/preview", json=snapshot)
    assert preview.status_code == 200
    assert preview.json()["operation"] == "create"
    assert len(client.get("/api/cases").json()) == 1
    assert client.post("/api/cases", json=snapshot).status_code == 201
    assert len(client.get("/api/cases").json()) == 2
    snapshot["sources"][0]["text"] = "Tampered without updating source content hash"
    assert client.post("/api/import/preview", json=snapshot).status_code == 422
