"""GET /v1/health — service liveness probe."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from service import __version__
from service.adapters.protocol import SkyBrainAdapter
from service.dependencies import get_adapter
from service.models.common import HealthResponse

router = APIRouter()

_STARTED_AT = time.monotonic()


@router.get("/health", response_model=HealthResponse, tags=["service"])
def health(adapter: SkyBrainAdapter = Depends(get_adapter)) -> HealthResponse:
    """Return service liveness, uptime, and the wrapped SDK version."""
    return HealthResponse(
        service_version=__version__,
        sdk_version=adapter.sdk_version(),
        uptime_seconds=round(time.monotonic() - _STARTED_AT, 3),
    )
