"""FastAPI dependency providers.

Centralised here so tests can override `get_adapter` with a fake that conforms
to `SkyBrainAdapter` without importing skybrain_sdk.
"""

from __future__ import annotations

from functools import lru_cache

from service.adapters.protocol import SkyBrainAdapter
from service.config import get_settings


@lru_cache(maxsize=1)
def get_adapter() -> SkyBrainAdapter:
    """Build the production adapter once per process.

    Imported lazily so docs builds and `--help` invocations don't require the
    proprietary SDK to be on the path.
    """
    settings = get_settings()
    try:
        from service.adapters.skybrain_sdk import SkyBrainSdkAdapter
    except ImportError as exc:
        if settings.require_sdk:
            raise RuntimeError(
                "skybrain-sdk is not importable. Install it via `pip install "
                '-e ".[sdk]"` or set SKYBRAIN_QVAC_REQUIRE_SDK=false to run '
                "the service in docs-only mode (endpoints will fail at request "
                "time)."
            ) from exc
        return _UnavailableAdapter()
    return SkyBrainSdkAdapter()


class _UnavailableAdapter:
    """Fallback adapter used when the SDK isn't installed and require_sdk=False.

    Lets the service boot for documentation purposes; any real call will fail
    with a clear message. Conforms to SkyBrainAdapter structurally.
    """

    def sdk_version(self) -> str:
        return "unavailable"

    def compute_biomarkers(
        self,
        file_path: str,
        biomarker_set: str,
        profile: str,
        view: str = "summary",
    ) -> dict[str, object]:
        raise RuntimeError(
            "skybrain-sdk not installed; service is running in docs-only mode. "
            'Install via `pip install -e ".[sdk]"` to enable inference.'
        )

    def compare_recordings(
        self,
        file_a: str,
        file_b: str,
        label_a: str,
        label_b: str,
        profile: str,
    ) -> dict[str, object]:
        raise RuntimeError(
            "skybrain-sdk not installed; service is running in docs-only mode. "
            'Install via `pip install -e ".[sdk]"` to enable inference.'
        )
