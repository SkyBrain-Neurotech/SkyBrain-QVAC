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
        view: str = "summary",
    ) -> dict[str, Any]:
        """Compute EEG biomarkers for a single recording file.

        Args:
            file_path: Absolute path to an EDF / EDF+ / BDF / CSV recording.
            biomarker_set: One of `spectral | cognitive | qc | advanced | full`.
                Dispatches to a different SDK call path per set.
            profile: SDK analysis profile (e.g. "skybrain_4ch", "clinical").
            view: `summary` (default) narrows payload to top-level per-channel
                metrics. `detailed` returns the full SDK output.

        Returns:
            A JSON-serialisable dict shaped for `BiomarkerResponse`. The exact
            keys depend on the biomarker_set; see `service.models.biomarkers`.

        Raises:
            FileNotFoundError: If the recording file is missing.
            ValueError: If `biomarker_set` is unknown.
            RuntimeError: If the underlying SDK call fails.
        """
        ...

    def compare_recordings(
        self,
        file_a: str,
        file_b: str,
        label_a: str,
        label_b: str,
        profile: str,
    ) -> dict[str, Any]:
        """Compare two EEG recordings and return curated metric differences.

        Walks every numeric metric produced by `run_analysis` on each file,
        computes delta + percent change, ranks by |percent_change|, returns
        the top 15 along with the full list of metric names extracted and a
        one-line auto-summary.

        Args:
            file_a: Path to the first recording (e.g. eyes-open).
            file_b: Path to the second recording (e.g. eyes-closed).
            label_a: Friendly label for the first condition.
            label_b: Friendly label for the second condition.
            profile: SDK analysis profile.

        Returns:
            Dict shaped for `CompareResponse` (without request-id, hashes,
            latency — those are added by the endpoint).

        Raises:
            FileNotFoundError: If either recording file is missing.
            RuntimeError: If the underlying SDK call fails.
        """
        ...
