"""Schemas for POST /v1/eeg/biomarkers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from service.models.common import BiomarkerSet, BiomarkerView


class BiomarkerRequest(BaseModel):
    """Request body for POST /v1/eeg/biomarkers."""

    model_config = ConfigDict(extra="forbid")

    session_file: str = Field(
        ...,
        description="Absolute path to an EDF / EDF+ / BDF / CSV recording file.",
        examples=["/tmp/sample.edf"],
    )
    biomarker_set: BiomarkerSet = Field(
        ...,
        description=(
            "Which biomarker bundle to compute. See docs/qvac-api-reference.md and "
            "the plan §7.2 for the exact SDK mapping."
        ),
    )
    profile: str = Field(
        default="skybrain_4ch",
        description="SkyBrain SDK analysis profile (e.g. 'skybrain_4ch', 'clinical').",
    )
    view: BiomarkerView = Field(
        default=BiomarkerView.SUMMARY,
        description=(
            "Output verbosity. `summary` returns top-level per-channel metrics "
            "(default; what a demo needs). `detailed` returns the full SDK "
            "payload including per-window time series."
        ),
    )


class BiomarkerResponse(BaseModel):
    """Response body for POST /v1/eeg/biomarkers.

    `modality` is locked to "eeg" in Phase 1; the field exists from day one so
    Phase 2 can add /v1/ecg/biomarkers and /v1/ppg/biomarkers as additive
    siblings without breaking this contract.
    """

    modality: Literal["eeg"] = "eeg"
    biomarker_set: BiomarkerSet
    profile: str
    kind: str = Field(
        ...,
        description=(
            "Which SDK return-object family produced the payload "
            "(features | qc | analysis | cognitive_scores)."
        ),
    )
    payload: dict[str, Any] = Field(
        ...,
        description=(
            "Raw biomarker values, shape depends on biomarker_set. "
            "See the SDK return-type docs for the exact key set."
        ),
    )
    request_id: str
    input_sha256: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
