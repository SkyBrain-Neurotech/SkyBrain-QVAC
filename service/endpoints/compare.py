"""POST /v1/eeg/compare — Phase 1 stub (returns 501)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from service.models.common import ErrorDetail, ErrorResponse

router = APIRouter()


@router.post(
    "/eeg/compare",
    responses={501: {"model": ErrorResponse}},
    tags=["eeg"],
)
def post_compare() -> None:
    """Two-recording statistical comparison — deferred to Phase 1 week 11-12."""
    raise HTTPException(
        status_code=501,
        detail=ErrorResponse(
            error=ErrorDetail(
                code="not_implemented",
                type="not_implemented",
                message=(
                    "/v1/eeg/compare is scaffolded but not yet wired. "
                    "SDK exposes quick_compare() for single-file segment "
                    "comparisons; two-recording compare requires composing "
                    "skybrain_sdk.stats primitives (see plan §2 gap #6)."
                ),
            )
        ).model_dump(),
    )
