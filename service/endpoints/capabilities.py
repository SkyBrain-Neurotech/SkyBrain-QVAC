"""GET /v1/capabilities — what this service supports.

Mirrors the catalogue in docs/capabilities.md so QVAC consumers can discover
paradigms/classifiers/biomarker bundles without reading markdown.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from service import __version__
from service.adapters.protocol import SkyBrainAdapter
from service.dependencies import get_adapter
from service.models.capabilities import (
    CapabilitiesResponse,
    default_classifiers,
    default_paradigms,
)

router = APIRouter()


@router.get("/capabilities", response_model=CapabilitiesResponse, tags=["service"])
def capabilities(adapter: SkyBrainAdapter = Depends(get_adapter)) -> CapabilitiesResponse:
    """Return paradigms, classifiers, modalities, biomarker-set names."""
    return CapabilitiesResponse(
        service_version=__version__,
        sdk_version=adapter.sdk_version(),
        paradigms=default_paradigms(),
        classifiers=default_classifiers(),
    )
