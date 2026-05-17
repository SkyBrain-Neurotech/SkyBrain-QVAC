"""FastAPI app entry point for skybrain-qvac-bci.

Mounts six routers under /v1. Two real (health, capabilities, biomarkers);
three return 501 with structured envelopes pointing at the plan items that
unblock them.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from service import __version__
from service.config import Settings, get_settings
from service.endpoints import (
    biomarkers,
    capabilities,
    classify,
    compare,
    health,
    ingest,
)
from service.models.common import ErrorDetail, ErrorResponse


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="skybrain-qvac-bci",
        version=__version__,
        description=(
            "Local-first FastAPI bridge between the SkyBrain SDK (EEG/BCI) and "
            "Tether's QVAC ecosystem. Open source under Apache 2.0; the SkyBrain "
            "SDK is a proprietary pip dependency. See docs/qvac-api-reference.md "
            "for the relationship to QVAC's OpenAI-compatible HTTP server."
        ),
    )

    app.include_router(health.router, prefix="/v1")
    app.include_router(capabilities.router, prefix="/v1")
    app.include_router(biomarkers.router, prefix="/v1")
    app.include_router(classify.router, prefix="/v1")
    app.include_router(ingest.router, prefix="/v1")
    app.include_router(compare.router, prefix="/v1")

    @app.exception_handler(RequestValidationError)
    async def _validation_exception(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="invalid_request",
                    type="invalid_request_error",
                    message=str(exc.errors()),
                )
            ).model_dump(),
        )

    return app


app = create_app()


def run() -> None:
    """Entry point for `skybrain-qvac-bci` console script."""
    import uvicorn

    settings: Settings = get_settings()
    uvicorn.run(
        "service.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
