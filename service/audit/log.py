"""JSON Lines audit logger.

One entry per inference. Daily-rotated file under ${SKYBRAIN_QVAC_AUDIT_DIR}.
File appends are line-atomic on POSIX and Windows (single write() < 4 KiB),
which is sufficient for single-process FastAPI/uvicorn. If we ever fan out to
multiple workers we'll switch to a queue + dedicated writer thread.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_of_file(file_path: str | os.PathLike[str]) -> str:
    """Stream-hash a file at `file_path` and return the hex digest.

    Reads in 1 MiB chunks so large recordings don't blow up memory.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_entry(audit_dir: Path, entry: dict[str, Any]) -> Path:
    """Append a single JSON-Lines record to today's audit file.

    Returns the file path written to so callers can surface it in responses.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    file_path = audit_dir / f"{day}.jsonl"

    line = json.dumps(entry, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    with open(file_path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return file_path


def make_entry(
    endpoint: str,
    request_id: str,
    input_sha256: str,
    latency_ms: float,
    modality: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct an audit record dict in the canonical shape."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "endpoint": endpoint,
        "request_id": request_id,
        "input_sha256": input_sha256,
        "latency_ms": round(latency_ms, 3),
        "modality": modality,
    }
    if extra:
        record["extra"] = extra
    return record
