"""POST /v1/bci/classify — Phase 1 stub (returns 501)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from service.models.common import ErrorDetail, ErrorResponse

router = APIRouter()


@router.post(
    "/bci/classify",
    responses={501: {"model": ErrorResponse}},
    tags=["bci"],
)
def post_classify() -> None:
    """BCI classifier inference — wiring deferred to Phase 1 week 5-6 milestone."""
    raise HTTPException(
        status_code=501,
        detail=ErrorResponse(
            error=ErrorDetail(
                code="not_implemented",
                type="not_implemented",
                message=(
                    "/v1/bci/classify is scaffolded but not yet wired. "
                    "Tracked for Phase 1 week 5-6; depends on BCIModelStore "
                    "provenance decision (see plan §2 gap #3)."
                ),
            )
        ).model_dump(),
    )
