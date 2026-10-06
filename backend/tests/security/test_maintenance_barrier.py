from fastapi.testclient import TestClient

from app.main import create_app


def test_maintenance_file_blocks_api_but_keeps_health_available(tmp_path, monkeypatch) -> None:
    marker = tmp_path / ".dentia-maintenance"
    monkeypatch.setenv("DENTIA_MAINTENANCE_FILE", str(marker))
    marker.write_text("target_sha=test\n", encoding="utf-8")
    client = TestClient(create_app(), base_url="http://127.0.0.1")

    blocked = client.get("/api/patient-imports/dentalink/sources")
    assert blocked.status_code == 503
    assert blocked.json()["detail"]["code"] == "MAINTENANCE_ACTIVE"
    assert blocked.headers["retry-after"] == "300"

    health = client.get("/health")
    assert health.status_code == 200


def test_removing_maintenance_file_reopens_normal_auth_gate(tmp_path, monkeypatch) -> None:
    marker = tmp_path / ".dentia-maintenance"
    monkeypatch.setenv("DENTIA_MAINTENANCE_FILE", str(marker))
    marker.write_text("target_sha=test\n", encoding="utf-8")
    client = TestClient(create_app(), base_url="http://127.0.0.1")

    assert client.get("/api/maintenance-test-not-found").status_code == 503
    marker.unlink()
    assert client.get("/api/maintenance-test-not-found").status_code == 404
