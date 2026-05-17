"""POST /v1/eeg/ingest — Phase 1 stub (returns 501)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from service.models.common import ErrorDetail, ErrorResponse

router = APIRouter()


@router.post(
    "/eeg/ingest",
    responses={501: {"model": ErrorResponse}},
    tags=["eeg"],
)
def post_ingest() -> None:
    """Streaming ingest — wiring deferred to Phase 1 week 9-10 milestone."""
    raise HTTPException(
        status_code=501,
        detail=ErrorResponse(
            error=ErrorDetail(
                code="not_implemented",
                type="not_implemented",
                message=(
                    "/v1/eeg/ingest is scaffolded but not yet wired. "
                    "Streaming transport (SSE vs WebSocket) and file-replay-vs-"
                    "hardware decisions pending Week 2 alignment call (see plan "
                    "§2 gaps #4 and #5)."
                ),
            )
        ).model_dump(),
    )
