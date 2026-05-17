"""Schema for GET /v1/capabilities.

Mirrors `docs/capabilities.md` enums so QVAC consumers can discover what this
service supports without reading the markdown.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from service.models.common import BiomarkerSet, Modality


class ParadigmDescriptor(BaseModel):
    name: str
    type: Literal["evoked", "active", "passive"]
    classes: str
    channel_requirement: str
    trial_duration_seconds: float


class ClassifierDescriptor(BaseModel):
    name: str
    strength: str
    typical_inference_ms: float


class CapabilitiesResponse(BaseModel):
    service: str = "skybrain-qvac-bci"
    service_version: str
    sdk_version: str
    modalities_supported: list[Modality] = Field(
        default_factory=lambda: [Modality.EEG],
        description="Phase 1 ships EEG only. ECG/PPG/multimodal are Phase 2+.",
    )
    biomarker_sets: list[BiomarkerSet] = Field(
        default_factory=lambda: [
            BiomarkerSet.SPECTRAL,
            BiomarkerSet.COGNITIVE,
            BiomarkerSet.QC,
            BiomarkerSet.ADVANCED,
            BiomarkerSet.FULL,
        ],
    )
    paradigms: list[ParadigmDescriptor]
    classifiers: list[ClassifierDescriptor]


def default_paradigms() -> list[ParadigmDescriptor]:
    """Per capabilities.md §1 BCI Engine table."""
    return [
        ParadigmDescriptor(
            name="p300",
            type="evoked",
            classes="2 (target / non-target)",
            channel_requirement="Fz, Cz, Pz, P3, P4, P7, P8",
            trial_duration_seconds=4.0,
        ),
        ParadigmDescriptor(
            name="ssvep",
            type="evoked",
            classes="2-8 frequencies",
            channel_requirement="Fz, Cz, Pz, P3, P4, P7, P8",
            trial_duration_seconds=3.0,
        ),
        ParadigmDescriptor(
            name="gesture",
            type="active",
            classes="4-6 (Neutral / Left-Right Clench / Full Clench / Blinks)",
            channel_requirement="any 4+ channels",
            trial_duration_seconds=1.5,
        ),
        ParadigmDescriptor(
            name="motor_imagery",
            type="active",
            classes="3-4 (Rest / Left / Right Hand / Feet)",
            channel_requirement="any 4+ channels",
            trial_duration_seconds=1.5,
        ),
        ParadigmDescriptor(
            name="cognitive_workload",
            type="passive",
            classes="2-4 levels",
            channel_requirement="any 4+ channels",
            trial_duration_seconds=30.0,
        ),
        ParadigmDescriptor(
            name="cognitive_stress",
            type="passive",
            classes="2-4 levels",
            channel_requirement="any 4+ channels",
            trial_duration_seconds=30.0,
        ),
        ParadigmDescriptor(
            name="cognitive_drowsiness",
            type="passive",
            classes="2-4 levels",
            channel_requirement="any 4+ channels",
            trial_duration_seconds=30.0,
        ),
    ]


def default_classifiers() -> list[ClassifierDescriptor]:
    """Per capabilities.md §1 Classifier Architecture table + lines 374-384."""
    return [
        ClassifierDescriptor(
            name="bayesian_lda",
            strength="default; robust, fast, small datasets",
            typical_inference_ms=15.0,
        ),
        ClassifierDescriptor(
            name="bayesian_qda",
            strength="non-linear decision boundaries",
            typical_inference_ms=25.0,
        ),
        ClassifierDescriptor(
            name="bayesian_multinomial",
            strength="high class-count scenarios",
            typical_inference_ms=30.0,
        ),
        ClassifierDescriptor(
            name="bayesian_state_space",
            strength="temporal smoothing, Kalman-filter, drift-resistant",
            typical_inference_ms=30.0,
        ),
        ClassifierDescriptor(
            name="adaptive_state_space",
            strength="online adaptation, EKF for non-stationary EEG",
            typical_inference_ms=30.0,
        ),
    ]
