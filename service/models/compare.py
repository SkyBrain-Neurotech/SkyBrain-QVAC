"""Schemas for POST /v1/eeg/compare — two-recording differential."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CompareRequest(BaseModel):
    """Request body for POST /v1/eeg/compare.

    The classic use case is eyes-open vs eyes-closed — same subject, two
    short recordings, look at how biomarkers change between conditions.
    Any two recordings work; the labels just go into the response for
    readability.
    """

    model_config = ConfigDict(extra="forbid")

    session_a_file: str = Field(
        ...,
        description="Absolute or repo-relative path to the first recording.",
        examples=["docs/examples/eyes-open.csv"],
    )
    session_b_file: str = Field(
        ...,
        description="Absolute or repo-relative path to the second recording.",
        examples=["docs/examples/eyes-closed.csv"],
    )
    label_a: str = Field(
        default="condition_a",
        description="Friendly label for session A (e.g. 'eyes_open').",
    )
    label_b: str = Field(
        default="condition_b",
        description="Friendly label for session B (e.g. 'eyes_closed').",
    )
    profile: str = Field(
        default="skybrain_4ch",
        description="SkyBrain SDK analysis profile to use for both recordings.",
    )


class MetricDifference(BaseModel):
    """One row of the top-differences table."""

    metric: str = Field(..., description="Metric name (e.g. 'band_power_alpha').")
    channel: str | None = Field(
        default=None,
        description="Channel the metric was computed on (e.g. 'O1'); None for global metrics.",
    )
    value_a: float
    value_b: float
    delta: float = Field(..., description="value_b minus value_a.")
    percent_change: float = Field(
        ...,
        description="100 * (value_b - value_a) / |value_a|. Capped at +/- 10000 to avoid Inf.",
    )
    direction: Literal["increase_in_b", "decrease_in_b", "unchanged"]


class MetricsExtracted(BaseModel):
    """Catalogue of every metric the compare endpoint touched."""

    count: int
    names: list[str]


class CompareResponse(BaseModel):
    """Response body for POST /v1/eeg/compare.

    The response is deliberately curated — full per-metric dumps belong in
    the biomarker endpoint with `view=detailed`. This one is for demos and
    integration tests: 'here are the metrics we extract, here's what
    changed the most, here's a one-line summary.'
    """

    modality: Literal["eeg"] = "eeg"
    condition_a: str
    condition_b: str
    profile: str
    metrics_extracted: MetricsExtracted
    top_differences: list[MetricDifference] = Field(
        ...,
        description="Up to 15 entries, sorted by |percent_change| descending.",
    )
    summary: str = Field(
        ...,
        description="One-line auto-generated description of the strongest finding.",
    )
    request_id: str
    input_sha256_a: str
    input_sha256_b: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
