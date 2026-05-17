"""The three stub endpoints all return 501 with structured error envelopes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "path",
    [
        "/v1/bci/classify",
        "/v1/eeg/ingest",
        "/v1/eeg/compare",
    ],
)
def test_stub_endpoint_returns_501(client: TestClient, path: str) -> None:
    response = client.post(path, json={})
    assert response.status_code == 501
    body = response.json()
    assert body["detail"]["error"]["code"] == "not_implemented"
