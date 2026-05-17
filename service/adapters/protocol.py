"""Abstract SkyBrainAdapter interface.

Every endpoint depends on this Protocol, not on `service.adapters.skybrain_sdk`.
That keeps the SDK swappable for tests and enforces the proprietary/open-source
boundary: the rest of the service has zero knowledge that `skybrain_sdk` exists.
"""

from __future__ import annotations

from typing import Any, Protocol


class SkyBrainAdapter(Protocol):
    """The minimal capability surface every endpoint relies on.

    Implementations:
      - `service.adapters.skybrain_sdk.SkyBrainSdkAdapter` — production, calls
        the proprietary SDK.
      - Test fakes may implement this Protocol without importing skybrain_sdk.
    """

    def sdk_version(self) -> str:
        """Return the underlying SkyBrain SDK version string, or 'unavailable'."""
        ...

    def compute_biomarkers(
        self,
        file_path: str,
        biomarker_set: str,
        profile: str,
    ) -> dict[str, Any]:
        """Compute EEG biomarkers for a single recording file.

        Args:
            file_path: Absolute path to an EDF / EDF+ / BDF / CSV recording.
            biomarker_set: One of `spectral | cognitive | qc | advanced | full`.
                Dispatches to a different SDK call path per set.
            profile: SDK analysis profile (e.g. "skybrain_4ch", "clinical").

        Returns:
            A JSON-serialisable dict shaped for `BiomarkerResponse`. The exact
            keys depend on the biomarker_set; see `service.models.biomarkers`.

        Raises:
            FileNotFoundError: If the recording file is missing.
            ValueError: If `biomarker_set` is unknown.
            RuntimeError: If the underlying SDK call fails.
        """
        ...
