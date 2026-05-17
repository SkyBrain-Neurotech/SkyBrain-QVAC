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
assumed to have a particular schema.
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

# Common occipital channel labels — used by the auto-summary to detect the
# Berger alpha effect (eyes-closed elevated alpha over visual cortex).
_OCCIPITAL_CHANNELS = frozenset({"O1", "O2", "Oz", "O3", "Po7", "Po8"})


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
        view: str = "summary",
    ) -> dict[str, Any]:
        """Compute EEG biomarkers for a recording.

        Dispatches biomarker_set → SDK call:
          - spectral  → compute_features(recording, profile)
          - qc        → compute_qc(recording)
          - advanced  → run_analysis(recording, profile)
          - full      → run_analysis(recording, profile)
          - cognitive → cognitive_metrics.compute_all_scores(recording)

        When `view='summary'` (default), per-window time series (`windows`
        key at any nesting depth) are dropped from the payload to give a
        demo-friendly response. `view='detailed'` returns the raw SDK output.

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

        payload_dict = _to_dict(payload)
        if view == "summary":
            payload_dict = _drop_keys(payload_dict, drop={"windows"})

        return {
            "modality": "eeg",
            "biomarker_set": biomarker_set,
            "profile": profile,
            "kind": kind,
            "view": view,
            "payload": payload_dict,
        }

    def compare_recordings(
        self,
        file_a: str,
        file_b: str,
        label_a: str,
        label_b: str,
        profile: str,
    ) -> dict[str, Any]:
        """Compare two EEG recordings and return curated metric differences.

        Walks every numeric metric produced by `run_analysis` on both files,
        computes delta + percent change, ranks by |percent_change|, returns
        the top 15 along with the full list of metric names extracted and a
        one-line auto-summary.

        Lists / time-series leaves are skipped (not meaningfully comparable
        as scalars). Booleans are not treated as numeric.
        """
        rec_a = load_recording(file_path=file_a)
        rec_b = load_recording(file_path=file_b)

        result_a = _to_dict(run_analysis(rec_a, profile=profile))
        result_b = _to_dict(run_analysis(rec_b, profile=profile))

        flat_a = _flatten_numeric(result_a)
        flat_b = _flatten_numeric(result_b)

        all_names = sorted(set(flat_a) | set(flat_b))
        common = set(flat_a) & set(flat_b)

        diffs: list[dict[str, Any]] = []
        for key in common:
            a, b = flat_a[key], flat_b[key]
            delta = b - a
            if abs(a) < 1e-12:
                pct = 10000.0 if abs(b) > 1e-12 else 0.0
            else:
                pct = 100.0 * (b - a) / abs(a)
                pct = max(-10000.0, min(10000.0, pct))

            direction: str
            if delta > 1e-12:
                direction = "increase_in_b"
            elif delta < -1e-12:
                direction = "decrease_in_b"
            else:
                direction = "unchanged"

            diffs.append(
                {
                    "metric": _metric_leaf(key),
                    "channel": _extract_channel(key),
                    "value_a": float(a),
                    "value_b": float(b),
                    "delta": float(delta),
                    "percent_change": float(pct),
                    "direction": direction,
                }
            )

        diffs.sort(key=lambda d: abs(d["percent_change"]), reverse=True)
        top = diffs[:15]

        return {
            "modality": "eeg",
            "condition_a": label_a,
            "condition_b": label_b,
            "profile": profile,
            "metrics_extracted": {"count": len(all_names), "names": all_names},
            "top_differences": top,
            "summary": _auto_summary(top, diffs, label_a, label_b),
        }


# --- helpers below; private to this module --------------------------------


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


def _drop_keys(value: Any, drop: set[str]) -> Any:
    """Recursively remove `drop` keys from nested dicts/lists. Used by view=summary."""
    if isinstance(value, dict):
        return {k: _drop_keys(v, drop) for k, v in value.items() if k not in drop}
    if isinstance(value, list):
        return [_drop_keys(v, drop) for v in value]
    return value


def _flatten_numeric(value: Any, prefix: str = "") -> dict[str, float]:
    """Flatten a nested dict to `{dot.path: float}`, keeping only numeric leaves.

    Skips:
      - bool (Python treats True/False as 1/0; not what we want here)
      - lists, tuples (time series; not comparable as scalars)
      - strings, None
      - non-finite floats (NaN, +/-Inf)
    """
    out: dict[str, float] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            path = f"{prefix}.{k}" if prefix else k
            out.update(_flatten_numeric(v, path))
    elif isinstance(value, bool):
        return out
    elif isinstance(value, (int, float)):
        f = float(value)
        if f == f and f not in (float("inf"), float("-inf")):
            out[prefix] = f
    return out


def _extract_channel(path: str) -> str | None:
    """Pull a channel label out of a flattened metric path.

    SDK structures metric trees as `channel_features.<channel>.<metric>`, so
    we look for that pattern. Returns None for global metrics.
    """
    parts = path.split(".")
    if "channel_features" in parts:
        idx = parts.index("channel_features")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def _metric_leaf(path: str) -> str:
    """Drop the channel scaffolding and return the metric's leaf name."""
    return path.rsplit(".", 1)[-1]


def _auto_summary(
    top: list[dict[str, Any]],
    all_diffs: list[dict[str, Any]],
    label_a: str,
    label_b: str,
) -> str:
    """Build a one-line description of the biggest finding.

    Detects the classic Berger effect — large alpha increase over occipital
    channels — and labels it explicitly. Otherwise returns a generic
    "top change" summary.
    """
    if not top:
        return f"No measurable differences between {label_a} and {label_b}."

    biggest = top[0]
    metric = biggest["metric"].lower()
    channel = biggest["channel"]
    pct = biggest["percent_change"]
    direction = biggest["direction"]

    if (
        "alpha" in metric
        and channel in _OCCIPITAL_CHANNELS
        and direction == "increase_in_b"
        and pct > 50.0
    ):
        return (
            f"Strong alpha-band power increase ({pct:.0f}%) over occipital "
            f"channel {channel} in {label_b} vs {label_a} — consistent with "
            f"the classic Berger effect (posterior alpha rhythm modulation "
            f"by visual input)."
        )

    sign = "increase" if direction == "increase_in_b" else "decrease"
    channel_str = f" on {channel}" if channel else ""
    n_large = sum(1 for d in all_diffs if abs(d["percent_change"]) > 10.0)
    return (
        f"Top change: {biggest['metric']}{channel_str} shows a "
        f"{abs(pct):.0f}% {sign} in {label_b} vs {label_a}. "
        f"{n_large} metrics changed by more than 10%."
    )
