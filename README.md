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
# 1. Clone the open-source bridge
git clone https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC.git
cd SkyBrain-QVAC

# 2. Install dev dependencies
python -m venv .venv
.venv/Scripts/activate    # PowerShell:  .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 3a. If you have SkyBrain SDK access (Tether grants team, internal use):
pip install /path/to/sdk-release/wheels/skybrain_eeg_sdk-1.5.0-py3-none-any.whl

# 3b. If you don't have SDK access, run the bridge in docs-only mode:
$env:SKYBRAIN_QVAC_REQUIRE_SDK="false"    # PowerShell
# (or `export SKYBRAIN_QVAC_REQUIRE_SDK=false` on macOS / Linux / Git Bash)

# 4. Run
python -m service.main
```

See **[About the SkyBrain SDK](#about-the-skybrain-sdk)** below for
which endpoints work without the SDK installed.

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
curl -s -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}' | python -m json.tool
```

> **Tip.** Pipe responses through `python -m json.tool` (bash/cmd) or
> `ConvertTo-Json -Depth 10` (PowerShell) for readable output. Without
> the depth flag, PowerShell shows nested objects as `@{key=; ...}`
> with empty values — the data is there, the default formatter just
> doesn't expand it.

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

## About the SkyBrain SDK

This bridge wraps **SkyBrain Neurotech's proprietary EEG/BCI SDK** —
the same engine that powers SkyBrain's commercial product line:
SkyBrain Studio (real-time acquisition GUI), SkyBrain Analyze
(desktop analysis suite), the Cognitive Edge mobile app, and SkyBrain's
Enterprise API + data vault. 50+ biomarkers, 7 BCI paradigms, 5
Bayesian classifiers, CDSCO-compliant audit, deterministic computation.

The SDK is **not currently distributed for general developer use.**
It is gated to:

1. SkyBrain's own commercial products
2. The **Tether grants team** for the duration of QVAC grant review
   (this bridge is the Phase 1 POC deliverable; reviewers need the SDK
   installed to run the bridge end-to-end)

If, as the grant progresses, Tether identifies specific SDK functions
that should be open-sourced for the broader QVAC ecosystem, that's a
future scope conversation — and SkyBrain is open to building OSS
implementations of those specific functions when there's a defined need.

### What you can do without SDK access

The bridge source code is open under Apache 2.0 — anyone can read it,
fork it, study the integration pattern, and use it as a reference for
how to plug a proprietary Python SDK into QVAC's OpenAI-compatible
HTTP surface. You can also boot the service in docs-only mode:

```bash
SKYBRAIN_QVAC_REQUIRE_SDK=false python -m service.main
```

In that mode:
- `GET /v1/health` works (reports `sdk_version: "unavailable"`)
- `GET /v1/capabilities` works (the static catalogue from `docs/capabilities.md`)
- OpenAPI / Swagger UI at `http://127.0.0.1:8765/docs` is fully browsable
- Inference endpoints fail with a clean `sdk_unavailable` error envelope

That's enough surface to design a QVAC client against the API contract
without running the SDK.

### Commercial / enterprise SkyBrain deployments

If you're evaluating SkyBrain for clinical, enterprise data collection,
or commercial-product deployments (Studio, Analyze, Enterprise API),
that's a separate commercial sales track. Contact `info@skybrain.in`
to discuss enterprise licensing — that conversation happens outside
this repo.

### What works without the SDK installed

If you set `SKYBRAIN_QVAC_REQUIRE_SDK=false`, the service still boots
and these endpoints respond:

- `GET /v1/health` (reports `sdk_version: "unavailable"`)
- `GET /v1/capabilities` (static catalogue from `docs/capabilities.md`)
- All six routes return correctly-shaped error envelopes

Inference endpoints (`/v1/eeg/biomarkers`, etc.) will fail with a
clear `sdk_unavailable` message rather than a stack trace. Useful for
docs review, OpenAPI introspection at `/docs`, and integration
testing of clients that haven't been granted SDK access yet.

## License

[Apache 2.0](LICENSE).

The proprietary `skybrain-eeg-sdk` package is licensed separately by
SkyBrain Neurotech and is **not bundled** with this repository.
