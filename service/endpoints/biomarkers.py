"""POST /v1/eeg/biomarkers — real end-to-end implementation.

Flow:
  1. Resolve and validate the input file path.
  2. SHA-256 hash the file (audit trail).
  3. Time the adapter call.
  4. Write a JSON Lines audit entry.
  5. Return the BiomarkerResponse.
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
from service.models.biomarkers import BiomarkerRequest, BiomarkerResponse
from service.models.common import ErrorDetail, ErrorResponse

router = APIRouter()


@router.post(
    "/eeg/biomarkers",
    response_model=BiomarkerResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["eeg"],
)
def post_biomarkers(
    body: BiomarkerRequest,
    adapter: SkyBrainAdapter = Depends(get_adapter),
    settings: Settings = Depends(get_settings),
) -> BiomarkerResponse:
    """Compute biomarkers for an EEG recording file."""
    file_path = Path(body.session_file).expanduser().resolve()
    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="recording_not_found",
                    type="invalid_request_error",
                    message=f"recording file not found: {file_path}",
                    param="session_file",
                )
            ).model_dump(),
        )

    request_id = str(uuid.uuid4())
    input_sha256 = sha256_of_file(file_path)

    started = time.perf_counter()
    try:
        adapter_result = adapter.compute_biomarkers(
            file_path=str(file_path),
            biomarker_set=body.biomarker_set.value,
            profile=body.profile,
        )
    except FileNotFoundError as exc:  # narrow re-raise
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="recording_not_found",
                    type="invalid_request_error",
                    message=str(exc),
                    param="session_file",
                )
            ).model_dump(),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="invalid_biomarker_set",
                    type="invalid_request_error",
                    message=str(exc),
                    param="biomarker_set",
                )
            ).model_dump(),
        ) from exc
    except Exception as exc:  # translate to structured envelope
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
            endpoint="POST /v1/eeg/biomarkers",
            request_id=request_id,
            input_sha256=input_sha256,
            latency_ms=latency_ms,
            modality="eeg",
            extra={
                "biomarker_set": body.biomarker_set.value,
                "profile": body.profile,
                "kind": adapter_result["kind"],
            },
        ),
    )

    return BiomarkerResponse(
        biomarker_set=body.biomarker_set,
        profile=body.profile,
        kind=adapter_result["kind"],
        payload=adapter_result["payload"],
        request_id=request_id,
        input_sha256=input_sha256,
        latency_ms=round(latency_ms, 3),
    )
