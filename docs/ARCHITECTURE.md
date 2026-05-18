# Architecture

> Developer-oriented walkthrough of `skybrain-qvac-bci`. Read this if you're contributing to the code, reviewing the design, or planning to extend the service with a new endpoint.
>
> For a beginner end-to-end run-through: [`USER_GUIDE.md`](USER_GUIDE.md).
> For the QVAC ecosystem context: [`qvac-api-reference.md`](qvac-api-reference.md).

---

## What kind of system this is

`skybrain-qvac-bci` is a small, single-process Python HTTP service. It's deliberately not a framework, not a plugin host, not a distributed system. The whole thing is:

- A FastAPI app
- Six endpoint routers under `/v1/`
- One adapter file that wraps the proprietary SkyBrain SDK
- A few Pydantic schemas
- A JSON Lines audit logger
- A pyproject and CI workflow

That's it. Total source ~1,500 lines of Python. The smallness is intentional — every line either serves a Phase 1 deliverable or enforces a boundary that protects the proprietary/open-source split.

## High-level shape

```
                ┌────────────────────────────────┐
   HTTP/JSON    │  service.main.create_app()     │
  ────────────▶ │  FastAPI app + global error    │
                │  handler (RequestValidationError)
                └──────────────┬─────────────────┘
                               │ mounts 6 routers under /v1
                               ▼
       ┌─────────────────┬─────────────────┬─────────────────┐
       │  health.py      │  capabilities.py│  biomarkers.py  │  (live)
       │  classify.py    │  ingest.py      │  compare.py     │  (501 stubs)
       └─────────────────┴────────┬────────┴─────────────────┘
                                  │ Depends(get_adapter)
                                  ▼
                ┌────────────────────────────────┐
                │  service.dependencies          │
                │  get_adapter() — lazy import   │
                │  of SkyBrainSdkAdapter         │
                └──────────────┬─────────────────┘
                               │
                               ▼
                ┌────────────────────────────────┐
                │  service.adapters.protocol     │
                │  SkyBrainAdapter (Protocol)    │  ◀── abstract surface
                └──────────────┬─────────────────┘
                               │
                               ▼
                ┌────────────────────────────────┐
                │  service.adapters.skybrain_sdk │  ◀── ONLY skybrain_sdk
                │  SkyBrainSdkAdapter            │      import site
                └──────────────┬─────────────────┘
                               │
                               ▼
                ┌────────────────────────────────┐
                │  skybrain_sdk (proprietary)    │
                │  load_recording, compute_*,    │
                │  run_analysis, predict_bci, …  │
                └────────────────────────────────┘

                Side-effects on every inference:
                ─────────────────────────────────
                ┌────────────────────────────────┐
                │  service.audit.log             │
                │  sha256_of_file + write_entry  │
                │  → {AUDIT_DIR}/YYYY-MM-DD.jsonl │
                └────────────────────────────────┘
```

## Request lifecycle — one trip from curl to response

Walk through `POST /v1/eeg/biomarkers`:

1. **Client sends HTTP.** `curl` / `Invoke-RestMethod` posts JSON to `http://127.0.0.1:8765/v1/eeg/biomarkers` with a body like `{"session_file": "...", "biomarker_set": "spectral"}`.
2. **FastAPI parses the body via Pydantic.** `BiomarkerRequest` (in `service/models/biomarkers.py`) validates `session_file` is a string and `biomarker_set` is one of the five enum values. If validation fails, the global `RequestValidationError` handler in `service.main` returns a 422 with a structured `ErrorResponse` envelope.
3. **Endpoint handler runs.** `service.endpoints.biomarkers.post_biomarkers` (the only function in that router file). It:
   - Resolves the file path with `Path.expanduser().resolve()` and checks `is_file()`. Missing → 404 with `code: recording_not_found`.
   - Generates a UUID `request_id`.
   - Streams the input file through `service.audit.log.sha256_of_file` (1 MiB chunks) to produce a `input_sha256`.
   - Starts a `time.perf_counter()` timer.
4. **Adapter call.** `adapter.compute_biomarkers(file_path, biomarker_set, profile)` — `adapter` is injected via FastAPI's `Depends(get_adapter)`. The endpoint depends only on the `SkyBrainAdapter` Protocol; it has no knowledge of the concrete SDK adapter.
5. **Inside the adapter (`service/adapters/skybrain_sdk.py`).** This is the only file in the whole project that imports `skybrain_sdk`. The adapter:
   - Calls `load_recording(file_path)` → `EegRecording`.
   - Dispatches on `biomarker_set`:
     - `spectral` → `compute_features(recording, profile)`
     - `qc` → `compute_qc(recording)`
     - `advanced` / `full` → `run_analysis(recording, profile)`
     - `cognitive` → lazy-import `skybrain_sdk.cognitive_metrics.compute_all_scores`
   - Normalises the return object via `_to_dict()` — tries `.to_dict()` → `dataclasses.asdict()` → `.model_dump()` → `__dict__`. Never assumes a particular schema; works against whatever shape the SDK returns.
   - Wraps the result in `{modality, biomarker_set, profile, kind, payload}`.
6. **Latency captured.** Endpoint computes `latency_ms` from `time.perf_counter()`.
7. **Audit log written.** `service.audit.log.write_entry` appends a JSON line to `${SKYBRAIN_QVAC_AUDIT_DIR}/{YYYY-MM-DD}.jsonl`. Fields: timestamp, endpoint, request_id, input_sha256, latency_ms, modality, extras (biomarker_set, profile, kind).
8. **Response serialised.** Endpoint returns a `BiomarkerResponse` Pydantic model; FastAPI serialises it to JSON and returns 200.

Errors anywhere in steps 4–7 are caught at the endpoint level and translated to structured `ErrorResponse` envelopes (`recording_not_found` → 404, `invalid_biomarker_set` → 422, anything else → 500 with `code: sdk_error`).

## File-by-file purpose

### `service/__init__.py`
Just exposes `__version__ = "0.1.0"`. The version flows into `/v1/health` and `/v1/capabilities` responses.

### `service/main.py` — FastAPI app factory
- `create_app()` instantiates `FastAPI(title="skybrain-qvac-bci", ...)`.
- Mounts six routers under `/v1` (in fixed order: health, capabilities, biomarkers, classify, ingest, compare).
- Registers a single global exception handler for `RequestValidationError` so 422 responses use our structured `ErrorResponse` envelope instead of FastAPI's default detail format.
- `run()` is the console-script entrypoint (`skybrain-qvac-bci` in `pyproject.toml`), starting uvicorn at `settings.host:settings.port`.
- `app = create_app()` at module level so `uvicorn service.main:app` works.

### `service/config.py` — pydantic-settings
- Single `Settings` class with `env_prefix="SKYBRAIN_QVAC_"`.
- Fields: `host` (default `127.0.0.1`), `port` (default `8765`), `audit_dir`, `model_store_dir`, `default_analysis_profile`, `require_sdk`.
- `get_settings()` is a pure function returning a `Settings()` — used as a FastAPI dependency.
- `extra="ignore"` so unrelated env vars don't break startup.

### `service/dependencies.py` — DI providers
- `get_adapter()` is the single source of truth for "give me the SkyBrain adapter."
- `@lru_cache(maxsize=1)` so the adapter is built once per process.
- Lazy-imports `SkyBrainSdkAdapter` inside the function — this is what lets `pip install -e .` succeed *without* the `[sdk]` extra (docs builds, CI lint runs, etc.).
- If the import fails:
  - `settings.require_sdk == True` → raises `RuntimeError` with a clear install hint.
  - `settings.require_sdk == False` → returns a `_UnavailableAdapter` fallback (lets the service boot for docs but every inference call fails with a friendly message).

### `service/adapters/protocol.py` — `SkyBrainAdapter` Protocol
- A `typing.Protocol` with two methods: `sdk_version()` and `compute_biomarkers(file_path, biomarker_set, profile)`.
- Every other module in the codebase depends on **this** Protocol, not on the concrete `SkyBrainSdkAdapter`.
- Tests substitute fakes that conform to the Protocol without importing the proprietary SDK.

### `service/adapters/skybrain_sdk.py` — concrete adapter (the one place SDK is imported)
- The only file in the project that has `import skybrain_sdk` at module level.
- `SkyBrainSdkAdapter` class implements `SkyBrainAdapter`.
- The `_to_dict()` helper is deliberately defensive: it tries `.to_dict()`, `dataclasses.asdict()`, `.model_dump()`, then `__dict__`, then falls back to `repr()`. **Why:** the SDK's return-type schemas (`FeatureSet`, `QcReport`, `AnalysisResult`) aren't formally pinned in the API docs. Rather than guess at field structure (which would break on minor SDK bumps), we serialise whatever object comes back. Trade-off: response payloads have whatever shape the SDK returns — clients have to be defensive too. Long term: when the QVAC API contract is finalised (Week 2 alignment call), we can normalise to a stable Pydantic schema here.

### `service/audit/log.py` — JSON Lines audit
- Three small functions: `sha256_of_file`, `make_entry`, `write_entry`.
- File appends are line-atomic on both POSIX and Windows for writes under 4 KiB; one entry per call is well within that. Single-process FastAPI/uvicorn is fine. If we ever fan out to multiple workers, switch to a queue + dedicated writer thread.
- Daily file rotation — `YYYY-MM-DD.jsonl` keyed on UTC.
- File hashes are computed by streaming the input in 1 MiB chunks so large recordings (multi-GB BIDS sessions) don't blow up memory.

### `service/models/`
- `common.py` — `Modality` and `BiomarkerSet` enums, `ErrorDetail` / `ErrorResponse` (OpenAI-shaped), `HealthResponse`.
- `biomarkers.py` — `BiomarkerRequest`, `BiomarkerResponse`. The response has `modality: Literal["eeg"]` — Pydantic blocks accidental cross-modal responses at the type level, leaving room for `Literal["ecg"]` siblings in Phase 2.
- `capabilities.py` — `CapabilitiesResponse` plus the static `default_paradigms()` and `default_classifiers()` builders (sourced from `docs/capabilities.md` tables).

### `service/endpoints/`
One router per file. Each file contains a single `APIRouter()` and one handler function. Live ones do real work (`health`, `capabilities`, `biomarkers`); stubs return HTTP 501 with `code: not_implemented` and a message pointing at the milestone that will wire them.

The split-files layout is deliberate: when an endpoint is wired (e.g., `classify` in Week 5-6), the diff is contained to one file plus its Pydantic model — endpoints don't share state with each other.

### `service/tests/`
- `conftest.py` — two session-scoped fixtures: `app_audit_dir` (sets `SKYBRAIN_QVAC_AUDIT_DIR` to a temp dir before app boots), `client` (FastAPI `TestClient`), `sample_edf` (calls `skybrain-generate-edf` via subprocess; `pytest.skip` if the CLI isn't on PATH).
- `test_health.py`, `test_capabilities.py` — basic smoke tests for the two parameter-free endpoints.
- `test_biomarkers.py` — five tests: spectral happy path, qc happy path, full + latency budget, 404 on missing file, 422 on unknown biomarker_set. The three real-SDK tests are marked `@pytest.mark.sdk` so they're filterable when the SDK isn't available.
- `test_stubs.py` — parameterised test asserting each of the three stubbed endpoints returns 501 with `code: not_implemented`.

## The architectural rule that matters

**`service/adapters/skybrain_sdk.py` is the only file that may `import skybrain_sdk`.**

Why this rule exists:
- The open-source repo is Apache 2.0; the SDK is proprietary. The rule keeps the proprietary surface contained to one swappable file. Anyone reading the open-source code can understand it *without* the SDK installed.
- It makes the SDK trivially mockable in tests — tests depend on the Protocol, not the concrete adapter.
- It future-proofs Phase 2: when the JavaScript port replaces the Python SDK for some capabilities, the only Python file that needs to change is this one.
- It catches drift early. Every time someone reaches for a SkyBrain function from a new place, CI fails before review.

How it's enforced:
- `pyproject.toml` configures `import-linter` with a `forbidden` contract:
  ```toml
  [[tool.importlinter.contracts]]
  name = "Only service.adapters.skybrain_sdk may import skybrain_sdk"
  type = "forbidden"
  source_modules = [
      "service.main", "service.config", "service.dependencies",
      "service.endpoints", "service.models", "service.audit",
      "service.adapters.protocol",
  ]
  forbidden_modules = ["skybrain_sdk"]
  allow_indirect_imports = "true"
  ```
- `allow_indirect_imports = "true"` because the dependency injection in `service.dependencies.get_adapter()` *does* indirectly pull `skybrain_sdk` through the concrete adapter — that's by design. Direct imports are what we forbid.
- `lint-imports` runs in CI (`.github/workflows/ci.yml`) under the "Architecture boundary" step. The build breaks on any new direct import.

## How to add a new endpoint

Recipe, in order. About 100 lines of new code total. Concrete worked example: wiring `POST /v1/bci/classify` (the Week 5-6 milestone).

1. **Add the protocol method.** Open `service/adapters/protocol.py` and add `def classify_bci(self, file_path, paradigm, classifier_type) -> dict[str, Any]: ...` to the `SkyBrainAdapter` Protocol.
2. **Implement it in the concrete adapter.** Open `service/adapters/skybrain_sdk.py`. Import `predict_bci` from `skybrain_sdk.bci.inference` and `BCIModelStore` from `skybrain_sdk.bci.model_store`. Implement `classify_bci` — `load_recording` → load the trained model from the store keyed on `(paradigm, n_channels)` → `predict_bci(recording, model, paradigm)` → `_to_dict()` the `BCIResult`.
3. **Add the Pydantic models.** Open `service/models/classify.py` (currently doesn't exist; the stub uses `ErrorResponse` only). Define `ClassifyRequest` (file_path, paradigm enum, classifier_type enum) and `ClassifyResponse` (predictions, probabilities, uncertainty, latency_ms, request_id, input_sha256, modality).
4. **Wire the endpoint.** Open `service/endpoints/classify.py`. Replace the 501 stub with a real handler that mirrors `biomarkers.post_biomarkers`'s structure: resolve path → SHA-256 → time → adapter call → audit-log entry → response.
5. **Write tests.** Add `service/tests/test_classify.py` with at least: happy path against a real EDF, 404 on missing file, 422 on unknown paradigm. Mark SDK-dependent ones with `@pytest.mark.sdk`.

Run `pytest`, `ruff check .`, `black --check .`, `mypy service/`, `lint-imports` — all green. Done.

## Configuration model

All settings flow through `service.config.Settings`. Environment variables (prefix `SKYBRAIN_QVAC_`) override defaults. Nothing reads `os.environ` directly outside this class. The `Settings` instance is injected as a FastAPI dependency wherever a handler needs to know the audit directory or model store path.

| Env var | Default | Read by |
|---|---|---|
| `SKYBRAIN_QVAC_HOST` | `127.0.0.1` | `service.main.run` |
| `SKYBRAIN_QVAC_PORT` | `8765` | `service.main.run` |
| `SKYBRAIN_QVAC_AUDIT_DIR` | `./audit` | `service.endpoints.biomarkers` |
| `SKYBRAIN_QVAC_MODEL_STORE_DIR` | `./bci_models` | Reserved for `/v1/bci/classify` |
| `SKYBRAIN_QVAC_DEFAULT_ANALYSIS_PROFILE` | `skybrain_4ch` | Reserved for endpoint defaults |
| `SKYBRAIN_QVAC_REQUIRE_SDK` | `true` | `service.dependencies.get_adapter` |

## Audit trail design

Two design choices worth knowing:

1. **SHA-256 of the input file, not the request body.** We hash the file that was analysed, not the JSON `{session_file: ...}` request. The hash is a fingerprint of the data — same recording, same hash, regardless of how it's referenced. This is what makes audit-log entries reproducibility-grade for CDSCO compliance.
2. **JSON Lines, not SQLite.** One line per inference, daily-rotated file. Append-only, plain text, line-atomic on small writes. Trivial to ship, trivial to `grep`, trivial to ingest into anything (BigQuery, Splunk, a CSV viewer). The trade-off: no built-in query. If queryable audit becomes a Phase 2 requirement, we add a SQLite writer alongside the JSON Lines one (not replacing it).

## Testing model

- **All tests use the real SkyBrain SDK** via the `[sdk]` extra. We don't mock the adapter. Per Rakesh's session-1 directive: "real SDK from session 1, not mocks — mocking wastes a session and creates throwaway code."
- **Test fixtures are generated, not committed.** `conftest.py` calls `skybrain-generate-edf --duration 30 --channels 4 --pre-duration 10 --post-duration 10` per test session to produce a synthetic EDF. No EEG payloads in the repo.
- **SDK-dependent tests are marked.** `@pytest.mark.sdk`. CI runs them on a runner that has access to the SDK wheel; the open-source CI run skips them.
- **The stub endpoints are tested too.** `test_stubs.py` asserts each scaffolded endpoint returns 501 with the right error code. When wired, the parametrise list shrinks and the new endpoint gets its own test file.

## CI architecture

`.github/workflows/ci.yml` — active. Matrix: macOS × Linux × Windows, Python 3.11 × 3.12. Steps:

1. Checkout
2. Set up Python with pip caching
3. `pip install -e ".[dev]"` (no `[sdk]` — CI image doesn't have the proprietary wheel)
4. `ruff check .` — lint
5. `black --check .` — format
6. `mypy service/` — type-check
7. `lint-imports` — architecture boundary
8. `pytest -ra` with `SKYBRAIN_QVAC_REQUIRE_SDK=false` — runs everything except `@pytest.mark.sdk` tests

A second job (`sdk-integration`) is defined but `if: false` until the private SDK wheel index URL is provisioned. When enabled, it'll install `[sdk]` from a private index and run `pytest -m "sdk or not sdk"`.

## What this code does not do

So future contributors don't reach for things that aren't here:

- **No global state.** No singletons, no module-level mutables outside the FastAPI `app` and the cached `Settings`. Every handler gets its dependencies via `Depends`.
- **No async work yet.** Endpoints are synchronous because the SDK calls are synchronous (numba/numpy under the hood). When `/v1/eeg/ingest` arrives (Week 9-10), we'll introduce async + a streaming abstraction; not before.
- **No business logic outside the adapter.** Endpoints orchestrate (read input, hash, time, call adapter, audit, respond) but don't compute. All computation lives in the SDK, called through the adapter.
- **No persistence beyond the audit log.** No database, no Redis, no Hyperbee/Hypercore. Phase 2 may introduce a session store for the streaming endpoint; Phase 1 deliberately stays stateless.
- **No multi-tenancy.** This is a localhost service. One user, one process, one machine. Adding tenants is a Phase 3+ concern.
- **No authentication.** The default bind is `127.0.0.1` — anything that can reach the port is already on your machine. If you bind to `0.0.0.0`, add a reverse proxy with auth in front; we won't add app-level auth.

## Cross-references

| For | Read |
|---|---|
| API contract for QVAC consumers | [`qvac-api-reference.md`](qvac-api-reference.md) |
| Beginner walkthrough (install → first curl) | [`USER_GUIDE.md`](USER_GUIDE.md) |
| Phase 2 npm bridge plugin design | [`../plugin-manifest/README.md`](../plugin-manifest/README.md) |
| Grant context (why this exists at all) | [`01_QVAC_Strategic_Proposal.md`](01_QVAC_Strategic_Proposal.md) |
| Six-endpoint phase plan | [`02_QVAC_Technical_Brief.md`](02_QVAC_Technical_Brief.md) |
| SkyBrain SDK capabilities catalog | [`capabilities.md`](capabilities.md) |
| Sample API responses | [`examples/README.md`](examples/README.md) |
