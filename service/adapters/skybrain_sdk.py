"""SkyBrain SDK adapter — the ONLY module that imports `skybrain_sdk`.

This boundary is enforced by an import-linter contract in pyproject.toml.
Endpoints depend on `service.adapters.protocol.SkyBrainAdapter`, not on this
concrete implementation. That keeps the proprietary SDK swappable for tests
and prevents accidental SDK leakage into the open-source service code.

Conservative-signature policy
-----------------------------
We only call SDK functions whose signatures are documented in
`api_reference.md`. We do NOT guess at keyword arguments or return-type
fields. Each biomarker_set dispatches to one documented function, and the
return value is normalised to a plain dict via `_to_dict()` rather than
assumed to have a particular schema. The first verification run will print
the real dict shape and let us tighten downstream typing without inventing
keys here.
"""

from __future__ import annotations

import dataclasses
import importlib
from typing import Any

import skybrain_sdk
from skybrain_sdk import (
    compute_features,
    compute_qc,
    load_recording,
    run_analysis,
)


class SkyBrainSdkAdapter:
    """Production adapter that calls the proprietary SkyBrain SDK.

    Conforms to `service.adapters.protocol.SkyBrainAdapter`.
    """

    def sdk_version(self) -> str:
        return getattr(skybrain_sdk, "__version__", "unknown")

    def compute_biomarkers(
        self,
        file_path: str,
        biomarker_set: str,
        profile: str,
    ) -> dict[str, Any]:
        """Compute EEG biomarkers for a recording.

        Dispatches biomarker_set → SDK call:
          - spectral  → compute_features(recording, profile)
          - qc        → compute_qc(recording)
          - advanced  → run_analysis(recording, profile)
          - full      → run_analysis(recording, profile)
          - cognitive → cognitive_metrics.compute_all_scores(recording)
                        (lazy import — only loads the cognitive_metrics
                        sub-package if the request asks for it)

        Raises:
            FileNotFoundError: pass-through from load_recording.
            ValueError: unknown biomarker_set.
            RuntimeError: wraps SDK errors with context.
        """
        recording = load_recording(file_path=file_path)

        if biomarker_set == "spectral":
            payload = compute_features(recording, profile=profile)
            kind = "features"
        elif biomarker_set == "qc":
            payload = compute_qc(recording)
            kind = "qc"
        elif biomarker_set in {"advanced", "full"}:
            payload = run_analysis(recording, profile=profile)
            kind = "analysis"
        elif biomarker_set == "cognitive":
            cognitive_metrics = importlib.import_module(
                "skybrain_sdk.cognitive_metrics",
            )
            compute_all_scores = cognitive_metrics.compute_all_scores
            payload = compute_all_scores(recording)
            kind = "cognitive_scores"
        else:
            raise ValueError(
                f"unknown biomarker_set {biomarker_set!r}; "
                "expected one of: spectral, cognitive, qc, advanced, full",
            )

        return {
            "modality": "eeg",
            "biomarker_set": biomarker_set,
            "profile": profile,
            "kind": kind,
            "payload": _to_dict(payload),
        }


def _to_dict(value: Any) -> Any:
    """Best-effort conversion of SDK return objects to JSON-serialisable dicts.

    Tries common Python idioms in priority order — never invents fields,
    never guesses at object shape:
        1. .to_dict()      — most SDK result objects expose this
        2. dataclasses.asdict() — for @dataclass results
        3. .model_dump()    — for Pydantic models if the SDK uses them
        4. __dict__         — last resort for plain objects
        5. value itself     — primitives and built-in containers
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _to_dict(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_dict(v) for v in value]

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump()

    obj_dict = getattr(value, "__dict__", None)
    if isinstance(obj_dict, dict):
        return {k: _to_dict(v) for k, v in obj_dict.items() if not k.startswith("_")}

    return repr(value)
