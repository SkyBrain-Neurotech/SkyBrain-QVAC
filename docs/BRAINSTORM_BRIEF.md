# Brainstorm brief — SkyBrain × QVAC

> Self-contained context dump for pasting into a fresh LLM chat to brainstorm what to do next. Captures the project, where we are right now, what's pending, and the open questions that benefit from outside thinking.

---

## What this project is, in one paragraph

SkyBrain Neurotech builds EEG/BCI infrastructure: a proprietary Python SDK that turns raw brain-signal recordings into 50+ biomarkers and runs 7 BCI paradigms across 5 Bayesian classifiers, with time-synchronised EEG + ECG + PPG capture across BrainBit, Polar H10, and Polar Verity. Tether's QVAC ecosystem ships local-first AI (LLM, embeddings, ASR, TTS, OCR, NMT, image gen) plus **QVAC Health** — which today does observational import of wearable heart-rate, sleep, and activity data. What QVAC doesn't have yet is the algorithmic **neural-signal layer**: real-time EEG biomarkers, BCI inference, or time-synchronised multi-modal physiology fusion. We are open-sourcing the bridge between SkyBrain's SDK and QVAC under Apache 2.0 so QVAC consumers (Cognitive Edge, QVAC Health, QVAC MedPsy) can ground reasoning in neural state alongside the cardiovascular and activity signals Health already collects, without raw EEG ever leaving the user's device. Phase 1 (current) is a localhost FastAPI service in Python; Phase 2 will port the core to native JavaScript for Bare/Expo and add synchronised EEG+ECG+PPG fusion explicitly designed for QVAC Health ingestion.

## Strategic context

- **Grant:** Tether Developer Grants Program, QVAC ecosystem track. Range $100k–$300k USDt per QVAC grant; we're asking $150,000.
- **Trigger:** April 9, 2026 — Paolo Ardoino (Tether CEO) publicly committed Tether to "toolkits specifically designed for robotics and brain-computer interfaces." We are proposing the BCI toolkit.
- **Phase 1 timeline:** 12 weeks once funded. Released against milestone delivery, not upfront.
- **Phase 2:** separate future application after Phase 1 acceptance. Ports core to JS for Bare/Expo (mobile, browser, embedded).
- **Hardware partner:** BrainBit (CE-certified, Europe), India dealer relationship signed, global joint LOI in progress.
- **Existing SkyBrain products (all proprietary, not in scope for open-sourcing):**
  - SkyBrain SDK (Python) — the engine we wrap
  - BCI Studio — desktop acquisition GUI (uses the SDK)
  - SkyBrain Analyze — desktop analysis app (13 views, hardware-agnostic)
  - Cognitive Edge — consumer mobile app (Preparedness Index)
  - SkyBrain Chain — blockchain consent layer on Base (out of scope)

## Architecture in one paragraph

`skybrain-qvac-bci` is a single-process FastAPI service on `localhost:8765` exposing six `/v1/*` endpoints that mirror QVAC's OpenAI-compatible HTTP pattern. Every endpoint goes through a Python `SkyBrainAdapter` Protocol; **one file** (`service/adapters/skybrain_sdk.py`) is the sole place the proprietary `skybrain_sdk` package is imported, enforced by `import-linter` in CI. Each inference produces a SHA-256-fingerprinted JSON Lines audit entry for CDSCO/DPDP/GDPR compliance. No cloud calls, no telemetry. Apache 2.0 open source. Python 3.11+, FastAPI, Pydantic v2, pytest, ruff/black/mypy.

## Where we are right now (May 2026)

### Built and shipped to GitHub
- **Repo:** https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC (public, Apache 2.0)
- **v0.1.0 commit on `main`:** ~1,500 LOC across 41 files
- **Service:** FastAPI app boots on `localhost:8765`, six endpoint routers mounted
- **Live endpoints (3 of 6):**
  - `GET /v1/health` — liveness + SDK version
  - `GET /v1/capabilities` — lists 7 paradigms × 5 classifiers × 5 biomarker bundles
  - `POST /v1/eeg/biomarkers` — five bundle types: `spectral`, `qc`, `advanced`, `full` working; `cognitive` has a known adapter bug
- **Stubbed endpoints (3 of 6, return HTTP 501 with structured envelopes):**
  - `POST /v1/bci/classify` — scheduled Week 5-6 of Phase 1
  - `POST /v1/eeg/ingest` — scheduled Week 9-10 (depends on streaming-transport decision)
  - `POST /v1/eeg/compare` — scheduled Week 11-12
- **Tests:** 13 passing against the real SkyBrain SDK 1.5.0 (`pytest`)
- **CI:** GitHub Actions workflow defined for macOS / Linux / Windows × Python 3.11/3.12 (not yet enabled — file is at `ci/github-actions/ci.yml`, needs symlink to `.github/workflows/ci.yml`)
- **Audit log:** JSON Lines per inference at `audit/YYYY-MM-DD.jsonl` with SHA-256 of input
- **Performance on a 30s × 4ch synthetic EDF:** spectral 125ms, qc 6ms, full 140ms warm-cache (target was <200ms biomarker / <15ms classify; biomarker met, classify TBD)
- **Documentation:**
  - `README.md` — public-facing quickstart
  - `docs/USER_GUIDE.md` — beginner end-to-end walkthrough
  - `docs/ARCHITECTURE.md` — code-level developer walkthrough
  - `docs/qvac-api-reference.md` — what we extracted from docs.qvac.tether.io about QVAC's API surface
  - `docs/examples/` — three real sample response JSONs
  - `plugin-manifest/` — design package for the Phase 2 JS bridge plugin

### Critical finding from QVAC docs review
The original technical brief assumed QVAC plugins are JSON manifests (`qvac-plugin.json`). After reading `docs.qvac.tether.io`, the truth is: **QVAC plugins are TypeScript npm packages** using `definePlugin()` + `invokePlugin()`. So the Phase 1 deliverable named "QVAC plugin manifest" in the technical brief actually becomes a *design package* (which we shipped at `plugin-manifest/`), and the Phase 2 deliverable is the npm package itself (`@skybrain/qvac-bci-addon`).

### Application status
- Identified the application channel: tether.io → Apply for a grant (single web form with structured fields: company, project description, milestones, budget, attachments)
- Drafted field-by-field form content (project description 1700 chars, milestones 1800 chars)
- Generated PDFs of the strategic proposal and technical brief at `application/`
- Strategic proposal has a "live code already exists" cover callout
- **Not yet submitted.** Still pending: cut v0.1.0 GitHub release with SDK wheel attached, verify repo public visibility, optional 60-90s demo screencast, submit the form.

## Constraints and design rules

1. **The SDK is proprietary, the bridge is open-source.** Cannot bundle, copy, or vendor SDK code into the open-source repo. SDK installs as a separate wheel.
2. **One file may import `skybrain_sdk`.** Enforced by `import-linter`. Any other module that needs SDK output must go through the `SkyBrainAdapter` Protocol.
3. **Don't guess SDK signatures.** The SDK docs are not exhaustive; when something is unclear, the rule is to ask before guessing because wrong assumptions create downstream bugs. The `_to_dict()` helper in the adapter is intentionally defensive — it tries every reasonable conversion path instead of assuming a specific schema.
4. **EEG-core, modality-ready.** Phase 1 ships EEG only. URL is `/v1/eeg/biomarkers` (not `/v1/biomarkers`) so it never collides with biomarkers QVAC may already aggregate from wearables. Response schema reserves `modality: "eeg" | "ecg" | "ppg" | "multimodal"` so Phase 2 can add sibling endpoints.
5. **Local-first, no telemetry.** Default bind is `127.0.0.1`. SHA-256 audit log stays on-device. SkyBrain Chain (consent layer) is out of scope for Phase 1.
6. **Deterministic computation.** SDK uses fixed seeds. Same input + same SDK version = same output, bit for bit.
7. **Latency budgets:** <200ms biomarker computation on a 30-second window, <15ms BCI classification on a single epoch.

## Phase 1 milestones (paid via grant)

| Week | Deliverable | Status |
|---|---|---|
| 1-2 | QVAC alignment call: API envelope, plugin namespace, streaming convention | not started — Tether arranges post-award |
| 3-4 | Service production-hardening, 3 live endpoints, CI, audit, boundary contract | **done** (shipped pre-application) |
| 5-6 | Wire `POST /v1/bci/classify`, BCIModelStore design | pending |
| 7-8 | Cognitive Edge "Connect to QVAC" mode + reference Jupyter notebook for MedPsy prompt grounding | pending — codebase path TBD |
| 9-10 | Wire `POST /v1/eeg/ingest`, file-replay impl, hardware bridge deferred to Phase 2 | pending |
| 11-12 | Wire `POST /v1/eeg/compare`, cross-platform verification, demo recording, docs | pending |

## Open questions worth brainstorming

These are the genuinely unsettled decision points. Good targets for an outside perspective:

1. **BCIModelStore model provenance.** When a caller hits `/v1/bci/classify`, where does the trained model come from? Three candidates: (a) caller passes a file path, (b) service maintains a `BCIModelStore` keyed on `(paradigm, n_channels)`, (c) Phase 1 only accepts the synthetic-baseline default models and loudly disclaims "not validated on real EEG." Trade-offs: (a) flexible but exposes file paths in the API surface, (b) clean but requires deciding the model file format and store layout, (c) safe but useless for production. Current lean: (b) with (c) as fallback.
2. **Streaming transport for `/v1/eeg/ingest`.** Options: SSE (OpenAI-style, simple), WebSocket (QVAC SDK's WSRelay precedent, bidirectional), `invokePluginStream` async iterators (QVAC plugin-native but only callable from JS clients). The decision affects what the Phase 2 JS bridge plugin has to wrap. No way to lock this without the Week 2 QVAC team call.
3. **Two-recording compare.** SDK exposes `quick_compare(file, segment_a_label, segment_b_label)` for single-file segment compare. For two distinct recordings (pre/post studies, intervention efficacy), the SDK appears to require manual composition via `skybrain_sdk.stats`. Worth verifying with the SkyBrain SDK source rather than the docs.
4. **`cognitive` biomarker bundle adapter bug.** Calling `skybrain_sdk.cognitive_metrics.compute_all_scores(recording)` raises `AttributeError: 'EegRecording' object has no attribute 'get'` — the SDK function expects a different argument type (probably a feature dict). Need to read the actual SDK source for `compute_all_scores` to determine the right call shape.
5. **Cognitive Edge integration approach.** Week 7-8 work. Cognitive Edge is a React Native / Flutter mobile app (codebase path TBD). The "Connect to QVAC" feature is a minimal additive screen that pushes biomarker payloads through this bridge service into QVAC MedPsy. Open: should the mobile app talk directly to `localhost:8765` (requires the user to run the Python service on a paired desktop), or should the JS-bridge plugin from Phase 2 be required (creates a Phase-1/Phase-2 ordering dependency)?
6. **Plugin manifest framing for the grant application.** The technical brief still lists `qvac-plugin.json` as a Phase 1 deliverable, but reality is the design package + Phase 2 npm package. Three framings: (a) leave the brief untouched and hope reviewers don't catch it, (b) add a footnote disclosing the find honestly, (c) rewrite the relevant paragraphs entirely. Current decision: user handles manually before submission.
7. **License-error envelope at the HTTP layer.** SDK functions decorated with `@require_license(tier=...)` raise `LicenseNotActivatedError`. Currently caught at the endpoint and translated to 500 `sdk_error`. Better: dedicated 403 `license_required` with the required tier echoed in the body. Implementable today; just hasn't been scoped.
8. **Reference Jupyter notebook content.** Phase 1 deliverable. Open: what is the most persuasive 1-notebook story for a QVAC reviewer? Candidates: "EEG stress index feeds a MedPsy prompt and changes the response," "real-time cognitive load gates an LLM's verbosity," "pre/post therapy session comparison narrated by an LLM." The first one ties to QVAC MedPsy explicitly which is the strategic prize.

## Things this brief is NOT for

So you don't ask Claude chat to do these — they're already handled:

- ❌ Writing the FastAPI service from scratch (it's shipped at v0.1.0)
- ❌ Picking the budget number ($150,000 USDt, locked)
- ❌ Picking the license (Apache 2.0, locked)
- ❌ Designing the adapter boundary (done; enforced by `import-linter`)
- ❌ Choosing the biomarker bundle vocabulary (`spectral | cognitive | qc | advanced | full`, locked)
- ❌ The grant application channel (it's a web form at tether.io → Apply for a grant)

## Suggested prompts for the brainstorm

Tight scoped questions you can ask Claude chat with this brief attached:

1. *"Given the constraints above, what's the strongest single Jupyter notebook I could ship in Phase 1 Week 7-8 to demonstrate EEG-grounded prompts to QVAC MedPsy?"*
2. *"Help me pick between SSE, WebSocket, and `invokePluginStream` for the streaming `/v1/eeg/ingest` endpoint. Walk through trade-offs for both Phase 1 (Python service) and Phase 2 (JS bridge plugin) consumers."*
3. *"How should I frame the `qvac-plugin.json`-doesn't-exist discovery in the grant application? Is it a strength (we did real research) or a weakness (the brief promised something that doesn't fit)? Draft the paragraph."*
4. *"Critique the EEG-core, modality-ready design. Where will this hurt us in Phase 2 when ECG/PPG get added? Are there reserved fields I haven't thought of?"*
5. *"What's the smallest change to the Cognitive Edge mobile app that gets a working 'Connect to QVAC' demo without requiring users to run a Python server on a paired desktop?"*
6. *"Sanity-check the milestone schedule. Is 'wire `/v1/bci/classify` in 2 weeks' realistic given the BCIModelStore provenance question is still open?"*

## Repo links

| | URL / path |
|---|---|
| GitHub repo | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC |
| README | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/blob/main/README.md |
| User guide | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/blob/main/docs/USER_GUIDE.md |
| Architecture doc | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/blob/main/docs/ARCHITECTURE.md |
| QVAC API reference | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/blob/main/docs/qvac-api-reference.md |
| Sample biomarker outputs | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/tree/main/docs/examples |
| Plugin-manifest (Phase 2 design) | https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/tree/main/plugin-manifest |

## Quick stats for the LLM's mental model

- **Languages:** Python 3.11+ only (Phase 1); TypeScript planned for Phase 2 bridge plugin.
- **Lines of code:** ~1,500 across 41 committed files.
- **Tests:** 13 passing, all against the real SkyBrain SDK 1.5.0.
- **Dependencies:** FastAPI, Uvicorn, Pydantic v2, pydantic-settings, python-multipart. Dev: pytest, ruff, black, mypy, pre-commit, import-linter. Optional: `skybrain-eeg-sdk` (proprietary).
- **Default port:** 8765 (chosen by technical brief; QVAC's own server defaults to 11434).
- **Default bind:** 127.0.0.1 (loopback only).
- **Audit format:** JSON Lines, daily rotated, SHA-256 + ISO timestamp per entry.
