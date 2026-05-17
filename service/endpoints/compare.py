"""POST /v1/eeg/compare — two-recording differential.

Curated output: list of every metric we extract + top 15 differences ranked
by absolute percent-change + a one-line auto-summary. Mirrors the biomarkers
endpoint's structure for audit logging and SHA-256 fingerprinting.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from service.adapters.protocol import SkyBrainAdapter
from service.audit.log import make_entry, sha256_of_file, write_entry
from service.config import Settings, get_settings
from service.dependencies import get_adapter
from service.models.common import ErrorDetail, ErrorResponse
from service.models.compare import CompareRequest, CompareResponse

router = APIRouter()


@router.post(
    "/eeg/compare",
    response_model=CompareResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["eeg"],
)
def post_compare(
    body: CompareRequest,
    adapter: SkyBrainAdapter = Depends(get_adapter),
    settings: Settings = Depends(get_settings),
) -> CompareResponse:
    """Compare two EEG recordings and return curated metric differences."""
    file_a = Path(body.session_a_file).expanduser().resolve()
    file_b = Path(body.session_b_file).expanduser().resolve()

    for label, path in (("session_a_file", file_a), ("session_b_file", file_b)):
        if not path.is_file():
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="recording_not_found",
                        type="invalid_request_error",
                        message=f"recording file not found: {path}",
                        param=label,
                    )
                ).model_dump(),
            )

    request_id = str(uuid.uuid4())
    input_sha256_a = sha256_of_file(file_a)
    input_sha256_b = sha256_of_file(file_b)

    started = time.perf_counter()
    try:
        adapter_result = adapter.compare_recordings(
            file_a=str(file_a),
            file_b=str(file_b),
            label_a=body.label_a,
            label_b=body.label_b,
            profile=body.profile,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="recording_not_found",
                    type="invalid_request_error",
                    message=str(exc),
                )
            ).model_dump(),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="sdk_error",
                    type="sdk_error",
                    message=f"{type(exc).__name__}: {exc}",
                )
            ).model_dump(),
        ) from exc
    latency_ms = (time.perf_counter() - started) * 1000.0

    write_entry(
        settings.audit_dir,
        make_entry(
            endpoint="POST /v1/eeg/compare",
            request_id=request_id,
            input_sha256=f"{input_sha256_a}|{input_sha256_b}",
            latency_ms=latency_ms,
            modality="eeg",
            extra={
                "condition_a": body.label_a,
                "condition_b": body.label_b,
                "profile": body.profile,
                "metrics_extracted_count": adapter_result["metrics_extracted"]["count"],
                "top_differences_count": len(adapter_result["top_differences"]),
            },
        ),
    )

    return CompareResponse(
        condition_a=adapter_result["condition_a"],
        condition_b=adapter_result["condition_b"],
        profile=adapter_result["profile"],
        metrics_extracted=adapter_result["metrics_extracted"],
        top_differences=adapter_result["top_differences"],
        summary=adapter_result["summary"],
        request_id=request_id,
        input_sha256_a=input_sha256_a,
        input_sha256_b=input_sha256_b,
        latency_ms=round(latency_ms, 3),
    )
