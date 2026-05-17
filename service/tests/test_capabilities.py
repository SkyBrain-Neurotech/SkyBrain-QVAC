"""GET /v1/capabilities smoke test."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_capabilities_lists_eeg_modality(client: TestClient) -> None:
    response = client.get("/v1/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert "eeg" in body["modalities_supported"]


def test_capabilities_enumerates_known_paradigms(client: TestClient) -> None:
    response = client.get("/v1/capabilities")
    body = response.json()
    paradigm_names = {p["name"] for p in body["paradigms"]}
    expected = {
        "p300",
        "ssvep",
        "gesture",
        "motor_imagery",
        "cognitive_workload",
        "cognitive_stress",
        "cognitive_drowsiness",
    }
    assert expected <= paradigm_names, f"missing paradigms: {expected - paradigm_names}"


def test_capabilities_enumerates_five_bayesian_classifiers(client: TestClient) -> None:
    response = client.get("/v1/capabilities")
    body = response.json()
    classifier_names = {c["name"] for c in body["classifiers"]}
    expected = {
        "bayesian_lda",
        "bayesian_qda",
        "bayesian_multinomial",
        "bayesian_state_space",
        "adaptive_state_space",
    }
    assert expected == classifier_names
