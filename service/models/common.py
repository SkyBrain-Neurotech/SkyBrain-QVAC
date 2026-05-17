"""Shared schemas: error envelope, modality literal, biomarker-set enum.

The error envelope follows OpenAI's convention as the closest precedent for
QVAC's OpenAI-compatible HTTP layer (see docs/qvac-api-reference.md §2).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Modality(str, Enum):
    """Signal modality. Phase 1 ships EEG only; other values reserved.

    See plan §7.2 and `qvac-plugin.json` naming (`skybrain.eeg.biomarkers`,
    not `skybrain.biomarkers`) for why this enum exists from day one.
    """

    EEG = "eeg"
    ECG = "ecg"  # reserved, Phase 2+
    PPG = "ppg"  # reserved, Phase 2+
    MULTIMODAL = "multimodal"  # reserved, Phase 2+


class BiomarkerSet(str, Enum):
    """EEG biomarker bundle vocabulary. See plan §7.2 for the SDK mapping."""

    SPECTRAL = "spectral"
    COGNITIVE = "cognitive"
    QC = "qc"
    ADVANCED = "advanced"
    FULL = "full"


class ErrorDetail(BaseModel):
    """Single error object, OpenAI-shaped."""

    code: str = Field(..., description="Machine-readable error identifier.")
    type: str = Field(
        ...,
        description="Coarse error category (e.g. 'invalid_request_error', 'sdk_error').",
    )
    message: str = Field(..., description="Human-readable explanation.")
    param: str | None = Field(default=None, description="Field that triggered the error, if any.")


class ErrorResponse(BaseModel):
    """Top-level error envelope returned on non-2xx responses."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """GET /v1/health response."""

    status: Literal["ok"] = "ok"
    service: str = "skybrain-qvac-bci"
    service_version: str
    sdk_version: str
    uptime_seconds: float
