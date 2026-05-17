"""GET /v1/health smoke test."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200_and_basic_fields(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "skybrain-qvac-bci"
    assert "service_version" in body
    assert "sdk_version" in body
    assert isinstance(body["uptime_seconds"], (int, float))


def test_unknown_route_returns_404(client: TestClient) -> None:
    response = client.get("/v1/nonexistent")
    assert response.status_code == 404
