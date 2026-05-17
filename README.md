# skybrain-qvac-bci

> **Local-first EEG/BCI biomarkers for the QVAC ecosystem.**
> A small Python HTTP service that exposes [SkyBrain's proprietary EEG/BCI SDK](https://skybrain.in) over an OpenAI-compatible API. Built as the Phase 1 deliverable of SkyBrain's [Tether QVAC integration grant](docs/01_QVAC_Strategic_Proposal.md).

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen.svg)](#testing)
[![Status: Phase 1](https://img.shields.io/badge/status-Phase%201-orange.svg)](docs/02_QVAC_Technical_Brief.md)

---

## What you get

A localhost HTTP service on `127.0.0.1:8765` that turns an EEG recording into
biomarkers. No cloud calls. No telemetry. SHA-256 audit log per inference for
CDSCO / DPDP / GDPR compliance.

```bash
# macOS / Linux / Git Bash
curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d '{"session_file":"/path/to/recording.edf","biomarker_set":"spectral"}'
```

```cmd
:: Windows cmd.exe (note: escaped double quotes, not single quotes)
curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"/path/to/recording.edf\",\"biomarker_set\":\"spectral\"}"
```

```powershell
# Windows PowerShell — use Invoke-RestMethod, not curl
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body '{"session_file":"/path/to/recording.edf","biomarker_set":"spectral"}'
```

```json
{
  "modality": "eeg",
  "biomarker_set": "spectral",
  "kind": "features",
  "payload": {
    "channel_features": { ... },
    "global_features": { ... },
    "windows": [ ... ],
    "computation_params": { ... }
  },
  "request_id": "a5488520-2e5a-4d67-ad20-484dce675cf3",
  "input_sha256": "a5ff6f4a817048b25757cc7a5e92a972d24b70e32462bb2910ae5ccde10a8a7c",
  "latency_ms": 125.3
}
```

## Architecture

```
   Any HTTP client (QVAC SDK / Cognitive Edge / curl / your app)
                              │
                       HTTP/JSON
                              ▼
   ┌──────────────────────────────────────────────────────┐
   │  FastAPI service on localhost:8765                   │
   │                                                      │
   │   GET  /v1/health                                    │
   │   GET  /v1/capabilities                              │
   │   POST /v1/eeg/biomarkers     ◀── live               │
   │   POST /v1/bci/classify       ◀── Phase 1 wk 5–6     │
   │   POST /v1/eeg/ingest         ◀── Phase 1 wk 9–10    │
   │   POST /v1/eeg/compare        ◀── Phase 1 wk 11–12   │
   └────────────────────┬─────────────────────────────────┘
                        │ adapter Protocol
                        │ (sole skybrain_sdk import site)
                        ▼
   ┌──────────────────────────────────────────────────────┐
   │  skybrain_eeg_sdk (proprietary, pip install)         │
   │  50+ biomarkers · 7 paradigms · 5 Bayesian models    │
   └────────────────────┬─────────────────────────────────┘
                        │
                        ▼
   ┌──────────────────────────────────────────────────────┐
   │  BrainBit / DragonEEG / OpenBCI / any EDF file       │
   └──────────────────────────────────────────────────────┘
```

The **one architectural rule that matters**:
`service/adapters/skybrain_sdk.py` is the *only* file that may
`import skybrain_sdk`. Everything else depends on the
`SkyBrainAdapter` Protocol. Enforced by `import-linter` in CI — try
adding the import anywhere else and the build breaks.

## Three-command quickstart

Full beginner walkthrough in **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)**.

```bash
# 1. Clone
git clone https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC.git
cd SkyBrain-QVAC

# 2. Install (downloads SDK wheel from this repo's GitHub release)
python -m venv .venv
.venv/Scripts/activate    # PowerShell:  .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pip install https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/releases/latest/download/skybrain_eeg_sdk-1.5.0-py3-none-any.whl

# 3. Run
python -m service.main
```

In another shell, try the live endpoints. **Important — Windows users:** `curl` in PowerShell is aliased to `Invoke-WebRequest` (different flag set); cmd.exe's curl needs escaped double quotes. Pick the form for your shell.

**Windows PowerShell** (recommended — cleanest):

```powershell
Invoke-RestMethod http://127.0.0.1:8765/v1/health
Invoke-RestMethod http://127.0.0.1:8765/v1/capabilities
```

**Windows cmd.exe:**

```cmd
curl http://127.0.0.1:8765/v1/health
curl http://127.0.0.1:8765/v1/capabilities
```

**macOS / Linux / Git Bash:**

```bash
curl http://127.0.0.1:8765/v1/health
curl http://127.0.0.1:8765/v1/capabilities
```

Don't have an EEG recording? Generate one with the SDK's own CLI, then send it to the biomarker endpoint.

```bash
skybrain-generate-edf --output samples/demo --duration 30 --channels 4 --pre-duration 10 --post-duration 10
```

**PowerShell:**

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}'
```

**cmd.exe** (escaped double quotes — single quotes don't work in cmd):

```cmd
curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"spectral\"}"
```

**macOS / Linux / Git Bash:**

```bash
curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}'
```

## Endpoint status

| Endpoint | Status | Notes |
|---|---|---|
| `GET /v1/health` | **live** | Liveness + SDK version |
| `GET /v1/capabilities` | **live** | 7 paradigms × 5 classifiers × 5 biomarker sets |
| `POST /v1/eeg/biomarkers` | **live** | `spectral · cognitive · qc · advanced · full` |
| `POST /v1/bci/classify` | scaffolded (501) | Wired in Phase 1 week 5-6 |
| `POST /v1/eeg/ingest` | scaffolded (501) | Wired in Phase 1 week 9-10 |
| `POST /v1/eeg/compare` | scaffolded (501) | Wired in Phase 1 week 11-12 |

All six endpoints exist; the three scaffolded ones return structured JSON
explaining what they're blocked on, so client integration can begin against
the live contracts.

## Scope

Phase 1 ships **EEG biomarkers only**. The URL is `/v1/eeg/biomarkers`
(not `/v1/biomarkers`) so it never collides with biomarkers QVAC may
already aggregate from wearables or smartphone sensors. The response
schema reserves a `modality` field with values
`eeg | ecg | ppg | multimodal` so future phases can add
`/v1/ecg/biomarkers` and `/v1/ppg/biomarkers` as additive siblings.

Phase 2 (separately scoped, contingent on Phase 1 acceptance) ports the
core to native JavaScript and publishes `@skybrain/qvac-bci-addon` to
npm — see [`plugin-manifest/README.md`](plugin-manifest/README.md) for
the Phase 2 bridge plugin design.

## Privacy & determinism

- **No cloud calls** during inference. Default bind is `127.0.0.1`.
- **No telemetry** to SkyBrain servers. The bridge is fully offline-capable.
- **SHA-256** of every input recording, **timestamped JSON Lines** audit
  entry per inference at `${SKYBRAIN_QVAC_AUDIT_DIR:-./audit}/YYYY-MM-DD.jsonl`.
- **Deterministic computation**: the SDK uses fixed seeds. Same input + same
  SDK version → same output, bit for bit.

## Configuration

Every setting is environment-driven with the `SKYBRAIN_QVAC_` prefix:

| Env var | Default | Purpose |
|---|---|---|
| `SKYBRAIN_QVAC_HOST` | `127.0.0.1` | Bind address. |
| `SKYBRAIN_QVAC_PORT` | `8765` | HTTP port. |
| `SKYBRAIN_QVAC_AUDIT_DIR` | `./audit` | Audit log directory. |
| `SKYBRAIN_QVAC_MODEL_STORE_DIR` | `./bci_models` | Trained BCI model store (Phase 1 wk 5-6). |
| `SKYBRAIN_QVAC_DEFAULT_ANALYSIS_PROFILE` | `skybrain_4ch` | SDK analysis profile fallback. |
| `SKYBRAIN_QVAC_REQUIRE_SDK` | `true` | Set `false` to run docs-only (no SDK). |

## Relationship to QVAC

QVAC ships its own OpenAI-compatible HTTP server on port **11434**
(Ollama-default). We're a sibling service on port **8765** — different
port, no collision.

QVAC plugins are *not* JSON manifests — they're TypeScript npm
packages built with `definePlugin()` + `invokePlugin()`. The Phase 2
deliverable wraps this Python service into such a plugin so QVAC
applications (Cognitive Edge, QVAC Health, MedPsy) can call our
biomarkers via `invokePlugin({ modelId, handler: "computeBiomarkers", ... })`.

See [`docs/qvac-api-reference.md`](docs/qvac-api-reference.md) for the
full QVAC API surface we condensed from [docs.qvac.tether.io](https://docs.qvac.tether.io).

## Documentation

- **[User guide](docs/USER_GUIDE.md)** — beginner-friendly end-to-end walkthrough
- **[QVAC API reference](docs/qvac-api-reference.md)** — QVAC SDK + HTTP server surface
- **[Strategic proposal](docs/01_QVAC_Strategic_Proposal.md)** — Tether grant context
- **[Technical brief](docs/02_QVAC_Technical_Brief.md)** — six-endpoint architecture
- **OpenAPI / Swagger UI** — `http://127.0.0.1:8765/docs` once the service is running

## Testing

```bash
pytest                 # 13 tests, all green against the real SDK
ruff check .           # lint
black --check .        # format
mypy service/          # type-check
lint-imports           # architecture boundary
```

CI runs the full sweep on macOS, Ubuntu, and Windows for Python 3.11 + 3.12 —
see [`ci/github-actions/ci.yml`](ci/github-actions/ci.yml).

## License

[Apache 2.0](LICENSE).

The proprietary `skybrain-eeg-sdk` package is licensed separately by
SkyBrain Neurotech and is **not bundled** with this repository. The SDK
is distributed as a versioned wheel on this repo's GitHub Releases
page; obtaining access requires a SkyBrain license.
