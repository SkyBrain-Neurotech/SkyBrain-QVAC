"""POST /v1/eeg/compare end-to-end tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def sample_edf_pair(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Generate two synthetic EDFs with different alpha-boost params.

    The compare endpoint should surface a meaningful difference between
    them — we don't assert on Berger physiology (synthetic data has no
    physiology), only that the response shape is correct and the diff
    list is non-empty.
    """
    if shutil.which("skybrain-generate-edf") is None:
        pytest.skip("skybrain-generate-edf not on PATH; install [sdk] extra")

    out_dir = tmp_path_factory.mktemp("compare_pair")

    for label, alpha_boost in (("low_alpha", "1.0"), ("high_alpha", "3.0")):
        prefix = out_dir / label
        result = subprocess.run(
            [
                "skybrain-generate-edf",
                "--output",
                str(prefix),
                "--duration",
                "30",
                "--channels",
                "4",
                "--pre-duration",
                "10",
                "--post-duration",
                "10",
                "--alpha-boost",
                alpha_boost,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip(
                f"skybrain-generate-edf failed for {label}: "
                f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )

    edf_files = sorted(out_dir.glob("**/*.edf"))
    if len(edf_files) < 2:
        pytest.skip(f"expected two EDFs in {out_dir}, found {len(edf_files)}")
    return edf_files[0], edf_files[1]


@pytest.mark.sdk
def test_compare_two_recordings_returns_diffs(
    client: TestClient,
    sample_edf_pair: tuple[Path, Path],
) -> None:
    file_a, file_b = sample_edf_pair
    response = client.post(
        "/v1/eeg/compare",
        json={
            "session_a_file": str(file_a),
            "session_b_file": str(file_b),
            "label_a": "low_alpha",
            "label_b": "high_alpha",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["modality"] == "eeg"
    assert body["condition_a"] == "low_alpha"
    assert body["condition_b"] == "high_alpha"
    assert body["metrics_extracted"]["count"] > 0
    assert len(body["metrics_extracted"]["names"]) == body["metrics_extracted"]["count"]
    assert len(body["top_differences"]) > 0
    assert len(body["top_differences"]) <= 15
    assert isinstance(body["summary"], str) and body["summary"]
    assert len(body["input_sha256_a"]) == 64
    assert len(body["input_sha256_b"]) == 64
    assert body["latency_ms"] >= 0.0

    first = body["top_differences"][0]
    for key in ("metric", "value_a", "value_b", "delta", "percent_change", "direction"):
        assert key in first


def test_compare_rejects_missing_file_a(client: TestClient) -> None:
    response = client.post(
        "/v1/eeg/compare",
        json={
            "session_a_file": "/tmp/definitely-does-not-exist-a.edf",
            "session_b_file": "/tmp/definitely-does-not-exist-b.edf",
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["error"]["code"] == "recording_not_found"


def test_compare_rejects_unknown_field(client: TestClient) -> None:
    response = client.post(
        "/v1/eeg/compare",
        json={
            "session_a_file": "/tmp/a.edf",
            "session_b_file": "/tmp/b.edf",
            "rogue_field": "should-fail",
        },
    )
    assert response.status_code == 422
