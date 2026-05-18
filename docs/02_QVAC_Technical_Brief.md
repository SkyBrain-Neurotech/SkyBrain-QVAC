# SkyBrain × QVAC: Technical Integration Brief

**Supporting document for ecosystem partnership proposal**
**Submitting org:** SkyBrain Neurotech
**Contact:** Rakesh C. Jakati — rakesh@skybrain.in
**Date:** May 2026

---

## Purpose of this document

This brief is the engineer-to-engineer supplement to the strategic proposal. It describes how SkyBrain's existing platform integrates into the QVAC ecosystem, the architectural choices behind the two-phase delivery, and the technical commitments SkyBrain makes around interfaces, open-source boundaries, and platform compatibility.

If anything in this brief is technically off or QVAC's team has preferred patterns we should align with, we'd appreciate direct feedback so we can revise.

> **Build status — May 2026.** A reference implementation of the Phase 1 deliverables is already live and public at https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC under Apache 2.0, tagged `v0.1.0`. Four of six endpoints functional; 16 tests passing against the real SkyBrain SDK 1.5.0; SHA-256 audit log per inference; cross-platform CI; the architecture, adapter boundary, and demo-grade auto-summary (Berger-effect detection on eyes-open / eyes-closed real recordings) are reviewable today. The full milestone schedule in §9 below reflects this — Phase 1 grant funds the remaining two endpoints (`/v1/bci/classify`, `/v1/eeg/ingest`), Cognitive Edge integration, cross-platform verification, and the demo recording.

---

## 1. Architectural overview

### Current state of SkyBrain platform

SkyBrain's processing layer is implemented in Python 3.11+. The core capabilities relevant to QVAC integration:

- **EEG signal ingestion** from a range of hardware (BrainBit headbands and caps, plus EDF/EDF+/BDF/HDF5/CSV/MAT/EEG file inputs from any manufacturer's recording system)
- **Preprocessing pipeline** with artifact rejection, filtering (high-pass, notch, bandpass), re-referencing, and quality scoring
- **50+ biomarker computation** spanning spectral analysis (band power, IAF, spectral edge, aperiodic decomposition), connectivity (coherence, PLI, wPLI), complexity (Hjorth, entropy, fractal dimension, DFA), and ERP measures
- **BCI inference** across five paradigms (P300, SSVEP, Motor Imagery, Gesture, Cognitive State) using five Bayesian classifiers with confidence gating
- **Statistical validation** with permutation tests, Bayesian t-tests, effect size computation
- **Real-time streaming** with sub-15ms WebSocket-based prediction latency
- **CDSCO-compliant audit trails** with SHA-256 file hashes and deterministic computation

### Where QVAC needs this

QVAC's ecosystem today exposes:

- LLM inference, embeddings, multimodal (Fabric LLM via llama.cpp fork)
- Speech-to-text and text-to-speech (Whisper.cpp, Parakeet, ONNX Runtime)
- Translation (Bergamot NMT)
- OCR, image generation
- OpenAI-compatible HTTP API surface (default port 11434)
- Peer-to-peer primitives via Holepunch
- QVAC Health: observational wearable data import (heart rate, sleep, activity, voice-driven biomarker logging)

What's missing is the **algorithmic neural-signal layer** — real-time EEG biomarkers, BCI inference, and time-synchronised multi-modal physiology fusion (EEG + ECG + PPG aligned). QVAC Health imports observational cardiovascular data from wearables but has no neural-signal processing, no developer-facing health SDK, and no signal-fusion pipeline. The QVAC SDK is JavaScript-based; plugins are **TypeScript npm packages** using `definePlugin()` + `invokePlugin()` (not JSON manifests as we initially assumed — confirmed by reading docs.qvac.tether.io during Phase 0 of the build).

### The integration challenge

SkyBrain's stack is Python. QVAC's stack is JavaScript. Bridging these without losing the local-first, peer-to-peer thesis is the architectural problem this proposal solves.

We propose a phased approach: a local HTTP service in Phase 1 (preserves Python ecosystem, ships fast, leverages QVAC's existing OpenAI-compatible API surface), followed by a native JavaScript port in Phase 2 (eliminates Python runtime dependency, fits QVAC plugin model natively).

This is the same pattern QVAC itself uses internally: Fabric LLM is a fork of llama.cpp (a C++ project), wrapped in a unified JS API surface. We extend that pattern to Python signal processing.

---

## 2. Phase 1: QVAC-compatible BCI service layer

### What gets built

A local HTTP service exposing SkyBrain SDK capabilities through QVAC's OpenAI-compatible API format.

```
┌──────────────────────────────────────────────────────────────┐
│                    User Device (Desktop or Mobile)            │
│                                                                │
│   ┌──────────────┐         ┌────────────────────────────┐     │
│   │  QVAC SDK    │◄────────│  Application Layer         │     │
│   │  (JavaScript)│         │  (Cognitive Edge, QVAC     │     │
│   └──────┬───────┘         │  Health, custom apps)      │     │
│          │                  └────────────────────────────┘     │
│          │ HTTP/localhost                                      │
│          │ OpenAI-compatible API                               │
│          ▼                                                     │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  SkyBrain BCI Service (Python, FastAPI)              │    │
│   │                                                       │    │
│   │  • EEG ingestion endpoint                            │    │
│   │  • Biomarker computation endpoint                    │    │
│   │  • BCI classification endpoint                       │    │
│   │  • Quality scoring endpoint                          │    │
│   │  • Pre/post comparison endpoint                      │    │
│   └──────────┬───────────────────────────────────────────┘    │
│              │                                                 │
│              ▼                                                 │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  SkyBrain SDK (proprietary Python)                   │    │
│   │  50+ biomarkers, 5 paradigms, 5 classifiers          │    │
│   └──────────┬───────────────────────────────────────────┘    │
│              │                                                 │
│              ▼ Bluetooth/USB                                  │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  BrainBit Hardware (or any compatible EEG device)    │    │
│   └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

All processing happens on the device. No cloud calls. No telemetry to SkyBrain servers during inference.

### API surface

The Phase 1 service implements endpoints mirroring QVAC's OpenAI-compatible patterns. Current state at v0.1.0 — final shapes will be reconciled with the QVAC team in the Week 1-2 alignment call:

**Live endpoints (functional against the real SkyBrain SDK 1.5.0):**

```
GET  /v1/health
     Liveness probe + reported SDK version.

GET  /v1/capabilities
     Static catalogue: 7 paradigms, 5 Bayesian classifiers, 5 biomarker bundles.

POST /v1/eeg/biomarkers
     Body: { session_file, biomarker_set, profile, view }
       biomarker_set ∈ {spectral, cognitive, qc, advanced, full}
       view          ∈ {summary, detailed}  (default summary)
     Returns: { modality: "eeg", biomarker_set, kind, payload, request_id,
                input_sha256, latency_ms, warnings }

POST /v1/eeg/compare        (← shipped pre-application; was originally scheduled
                              for Phase 1 Week 11-12. Built early because the
                              two-recording differential gives reviewers an
                              instantly recognisable scientific result (Berger
                              alpha effect) versus an opaque biomarker dump.)
     Body: { session_a_file, session_b_file, label_a, label_b, profile }
     Returns: { modality: "eeg", condition_a, condition_b, metrics_extracted:
                { count, names }, top_differences: [up to 15], summary,
                request_id, input_sha256_a, input_sha256_b, latency_ms }
     The auto-summary detects the Berger effect explicitly when alpha-band
     power increases > 50 % over occipital channels.
```

**Scaffolded endpoints (return HTTP 501 with structured envelopes pointing at
the milestone that unblocks them):**

```
POST /v1/bci/classify    ← Phase 1 Week 3-4 (after alignment call)
POST /v1/eeg/ingest      ← Phase 1 Week 7-8 (file-replay streaming via
                            SDK's StreamingSession; live BLE/LSL hardware
                            ingestion is Phase 2 alongside the JS port)
```

The service runs on `localhost:PORT` (default 8765, configurable; QVAC's own server defaults to 11434 — no collision). The proprietary SkyBrain SDK is gated to approved parties via private GitHub collaborator access at `SkyBrain-Neurotech/sdk-release`. Default-tier endpoints (biomarkers + compare) run with no key required.

### Open-source repository structure (as shipped at v0.1.0)

```
SkyBrain-QVAC/
├── README.md, LICENSE (Apache 2.0), pyproject.toml, .gitignore, .pre-commit-config.yaml
├── docs/
│   ├── 01_QVAC_Strategic_Proposal.md          ← this proposal
│   ├── 02_QVAC_Technical_Brief.md             ← this brief
│   ├── USER_GUIDE.md                          ← beginner end-to-end walkthrough
│   ├── ARCHITECTURE.md                        ← code-level developer doc
│   ├── BRAINSTORM_BRIEF.md                    ← pasteable context for LLM brainstorming
│   ├── qvac-api-reference.md                  ← QVAC SDK + HTTP server contract we extracted from docs.qvac.tether.io
│   ├── SDK_README.md, SDK_STRATEGY.md, capabilities.md
│   └── examples/                              ← real demo data committed
│       ├── eyes-open.csv, eyes-closed.csv     ← real EEG recordings
│       ├── compare-eyes-open-vs-closed-output.json
│       ├── biomarkers-spectral-output.json, biomarkers-spectral-summary-output.json
│       ├── biomarkers-full-output.json, biomarkers-qc-output.json
│       └── README.md
├── service/
│   ├── main.py, config.py, dependencies.py
│   ├── adapters/
│   │   ├── protocol.py                        ← abstract SkyBrainAdapter Protocol
│   │   └── skybrain_sdk.py                    ← ONLY skybrain_sdk import site, enforced by import-linter
│   ├── audit/log.py                           ← JSON Lines + SHA-256
│   ├── endpoints/                             ← one router per file
│   ├── models/                                ← Pydantic v2 schemas
│   └── tests/                                 ← 16 passing tests
├── plugin-manifest/
│   ├── README.md                              ← architecture for the Phase 2 npm bridge plugin
│   ├── capability-schema.json                 ← JSON Schema of the HTTP contract for TS codegen
│   └── package.json.example                   ← sample @skybrain/qvac-bci-addon manifest
└── .github/workflows/ci.yml                   ← macOS / Ubuntu / Windows × Python 3.11/3.12; active
```

The proprietary SkyBrain SDK is installed from a separate **private** repo (`SkyBrain-Neurotech/sdk-release`) accessible only to approved parties via GitHub collaborator invite. Reviewers email info@skybrain.in to be added. The bridge boots in docs-only mode (`SKYBRAIN_QVAC_REQUIRE_SDK=false`) without the SDK — useful for inspecting the API surface before access is granted.

Open layer = integration code, Apache 2.0, public. Proprietary layer = signal-processing intelligence, gated, used in SkyBrain's commercial products (BCI Studio, SkyBrain Analyze, Enterprise API, Cognitive Edge).

### Cross-platform compatibility for Phase 1

- **macOS (Apple Silicon and Intel):** Native support via Python 3.11+
- **Linux (Ubuntu, Debian, Fedora):** Native support
- **Windows 10/11:** Native support
- **Android:** Service runs as background process in companion mobile app (initial release); future iteration explores Termux for direct on-device Python
- **iOS:** Phase 1 service does not run natively on iOS due to Python runtime restrictions. Mobile demo uses companion app architecture pattern.

The iOS gap is the strongest argument for the Phase 2 native JavaScript port.

### Demo deliverable

End-to-end working demonstration at Phase 1 completion:

1. User opens Cognitive Edge on Android device
2. Headband connects via Bluetooth
3. User starts a 60-second baseline recording
4. SkyBrain service computes Preparedness Index, Cognitive Load, Stress, Relaxation in real-time
5. Biomarkers displayed within Cognitive Edge UI
6. Same biomarkers pushed to QVAC Health dashboard
7. Pre/post intervention session: user performs 10-min meditation, post-recording, statistical comparison auto-generated
8. Plain-English summary via QVAC MedPsy reasoning on EEG biomarker deltas
9. All processing local, all data stays on device, complete audit trail

---

## 3. Phase 2: Native JavaScript port and Cognitive Edge as QVAC reference

### What gets built

Core SkyBrain biomarker computation ported from Python to TypeScript, packaged as an npm-published `@skybrain/qvac-bci-addon` conforming to QVAC plugin architecture.

```
┌──────────────────────────────────────────────────────────────┐
│                    User Device (Desktop or Mobile)            │
│                                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  QVAC SDK (JavaScript)                               │    │
│   │                                                       │    │
│   │  ┌────────────────────────────────────────────────┐  │    │
│   │  │  @skybrain/qvac-bci-addon (npm package, OSS)   │  │    │
│   │  │                                                 │  │    │
│   │  │  • Spectral biomarkers (TypeScript)            │  │    │
│   │  │  • Band power, IAF, spectral edge              │  │    │
│   │  │  • Complexity measures                         │  │    │
│   │  │  • Real-time streaming pipeline                │  │    │
│   │  └────────────────────────────────────────────────┘  │    │
│   └──────────────────────────────────────────────────────┘    │
│                          │                                     │
│                          ▼                                     │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  Bluetooth/USB bridge for EEG hardware               │    │
│   └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### What gets ported, what stays proprietary

The Phase 2 npm package includes:

- Real-time signal preprocessing (filtering, artifact detection, quality scoring)
- Core spectral biomarkers (band power, IAF, peak frequency, spectral edge)
- Complexity measures (Hjorth parameters, sample entropy)
- A simplified classifier (single Bayesian discriminant) sufficient for basic gesture and cognitive state inference
- Cross-platform Bluetooth/USB bridge

The npm package gives developers a usable BCI capability inside QVAC for many real-world applications without requiring a separate Python runtime.

The full proprietary SkyBrain platform remains the upstream source for advanced capabilities: the five-classifier suite, full 50+ biomarker computation, advanced statistical validation, the full BCI Studio paradigm engine. Developers who need these continue to use SkyBrain SDK alongside QVAC. The Phase 1 Python service remains available for advanced workflows.

### Native compatibility

Phase 2 delivers QVAC's promised cross-platform promise for BCI:

- **iOS:** Native via Expo + React Native bridge to QVAC SDK
- **Android:** Same
- **Desktop:** All three platforms via Node.js or Bare runtime
- **Embedded:** Tested on Raspberry Pi-class hardware for low-power deployment scenarios

### Peer-to-peer extension

A modest portion of Phase 2 explores delegated EEG inference using QVAC's Holepunch P2P primitives. A consumer device with a 4-channel headband can offload complex foundation model inference to a paired desktop or research compute peer, while keeping raw EEG on-device. The peer receives anonymized biomarker vectors, runs inference, returns the result. This is a working prototype, not a production system, but it demonstrates the path toward QVAC's larger swarm vision applied to neural data.

---

## 4. Integration with QVAC MedPsy

QVAC MedPsy is a medical psychological reasoning model running locally on phones. EEG biomarkers provide physiological ground truth that text-based reasoning cannot access. The integration this proposal enables:

A user reports they feel anxious in QVAC MedPsy. MedPsy can ask for subjective context, but cannot verify the underlying physiological state. With the SkyBrain integration, the user's recent Cognitive Edge measurements (stress index, alpha power asymmetry, theta-beta ratio) flow into MedPsy's reasoning context.

This is not a clinical diagnostic claim. It is a richer reasoning substrate for a model designed to handle medical and psychological questions. The integration provides MedPsy with measurable biomarkers it can reference, compare across time, and use to ground its outputs.

A reference Jupyter notebook delivered in Phase 1 demonstrates this end-to-end with anonymized example data.

---

## 5. Hardware compatibility

### Primary partner: BrainBit (CE-certified)

SkyBrain operates as an authorized BrainBit India dealer and is in joint LOI negotiation covering global software bundling. BrainBit's product line:

- BrainBit Headband (4-channel, dry electrodes, T3/T4/O1/O2 placement, 12-hour battery)
- BrainBit Flex (8-channel, dry/wet electrodes, expanded paradigm coverage)
- DragonEEG (21+3 channel, clinical-grade)

The QVAC integration supports all three BrainBit form factors through SkyBrain's existing hardware abstraction layer.

### Other hardware compatibility

SkyBrain's existing platform supports recordings from any manufacturer in standard formats (EDF, EDF+, BDF, HDF5, CSV, MAT, EEG). Hardware-agnostic file processing is preserved in the QVAC integration. Researchers using OpenBCI, ANT Neuro, Nihon Kohden, Brain Products, or any other EEG system can use the same QVAC-integrated SkyBrain workflow.

### Cognitive Edge mobile

Cognitive Edge runs on Android (iOS planned in Phase 2). It connects to BrainBit hardware via Bluetooth and serves as the primary mobile UI for the BCI integration.

---

## 6. Privacy, consent, and data architecture

This is non-negotiable for SkyBrain and we believe aligned with QVAC's stated principles:

- **All inference local.** No EEG data leaves the device during normal operation.
- **No telemetry from SkyBrain platform to SkyBrain servers.** Standard operating mode is fully offline-capable.
- **Optional consent-driven data marketplace.** SkyBrain Chain (running on Base) lets users explicitly opt in to monetize their de-identified data through onchain consent records and burn-on-access NFT mechanics. Completely separate from the QVAC integration. Users who do not opt in see zero data leave their device.
- **Audit trails.** Every inference is locally recorded with SHA-256 hashing and deterministic reproducibility for CDSCO compliance.
- **DPDP Act 2023 compliance** for Indian users; GDPR-ready architecture for European deployments.

The integration follows the QVAC principle that the user's device is the trust boundary. Nothing in the partnership changes that.

---

## 7. IP boundaries (recap from proposal)

**Open-sourced under permissive license (Phase 1 and Phase 2 deliverables):**

- HTTP service layer code
- Plugin manifests
- npm-published BCI addon
- Integration documentation
- Cross-platform compatibility scaffolding
- Reference notebooks and demos

**Remains SkyBrain proprietary:**

- Full BCI Studio acquisition platform
- Five Bayesian classifier implementations
- SkyBrain Analyze desktop application (13 views)
- Per-user adaptive calibration logic
- Hybrid EMG-EEG signal decomposition methods (patent filing in progress)
- Preparedness Index composite scoring (patent filing in progress)
- Onchain consent and burn-on-access infrastructure (patent filing in progress)
- Hardware partnership terms with BrainBit

This separation is analogous to how Tether maintains QVAC Fabric (open-source) alongside proprietary Tether Data business operations. The open layer accelerates ecosystem adoption. The proprietary layer sustains the business that builds the open layer.

---

## 8. Engineering team and capacity

### Phase 1 team

- Rakesh Jakati (founder, technical lead, Python and architecture)
- Two engineering interns (rotating, supporting infrastructure and testing)
- Dr. Bhaskar Tripathi (AI/ML advisor, signal processing review)
- Aranyak Banerjee (BCI research scientist, validation and benchmarking)

### Phase 2 team additions (funded from Phase 2 grant)

- One mid-level JavaScript/TypeScript engineer hired for the native port (6-month engagement)
- One mobile engineer (contract) for Expo/React Native integration
- Continued involvement from Phase 1 team

### Why this scope is realistic

Phase 1 is essentially packaging an existing platform behind a new API surface. The underlying signal processing, biomarker computation, classifier inference, and statistical methods are already built and in production at universities. The new work is the HTTP service layer, the QVAC plugin manifest, and the cross-platform packaging.

Phase 2 is the more substantial engineering effort because it requires porting performance-critical numerical code to JavaScript. We are sizing it accordingly with dedicated engineering hires from the grant funds.

---

## 9. Milestones and checkpoints

### Pre-grant work already completed (May 2026, pre-submission)

- Repository scaffolded and public at github.com/SkyBrain-Neurotech/SkyBrain-QVAC under Apache 2.0
- Service architecture, SDK adapter boundary (enforced by import-linter), Pydantic models
- 4 of 6 endpoints functional against the real SkyBrain SDK 1.5.0 (`/v1/health`, `/v1/capabilities`, `/v1/eeg/biomarkers`, `/v1/eeg/compare`)
- `/v1/eeg/compare` ships an auto-summary that detects the classic Berger alpha effect from real eyes-open / eyes-closed recordings committed to the repo
- 16 tests passing; cross-platform CI workflow (macOS, Ubuntu, Windows × Python 3.11/3.12)
- SHA-256 + JSON Lines audit log per inference; sub-200 ms biomarker latency on warm cache
- All public docs aligned (USER_GUIDE, ARCHITECTURE, plugin-manifest design package)
- Gated SDK distribution via the private `SkyBrain-Neurotech/sdk-release` repo, with documented collaborator-invite intake

### Phase 1 (12 weeks, grant-funded)

- **Week 1-2:** Initial technical alignment call with QVAC team. Lock OpenAI-envelope details, plugin namespace, streaming transport convention. The `compare` endpoint shipping pre-application means Week 11-12 of the original schedule is reclaimed for cross-platform verification and demo recording.
- **Week 3-4:** Wire `POST /v1/bci/classify` (BCI classifier inference endpoint). Build `BCIModelStore` on disk keyed on `(paradigm, n_channels)`. Surface uncalibrated-baseline warnings on the synthetic-default model.
- **Week 5-6:** Cognitive Edge mobile app gets a minimal additive "Connect to QVAC" mode that pushes biomarkers to the local service for QVAC MedPsy ingestion. Reference Jupyter notebook demonstrates EEG-grounded prompts to MedPsy end-to-end with example data.
- **Week 7-8:** Wire `POST /v1/eeg/ingest` (streaming endpoint, file-replay via SDK's `StreamingSession`). Live BLE/LSL hardware ingestion stays in Phase 2 scope alongside the JS port.
- **Week 9-10:** Cross-platform compatibility verified on macOS, Linux, Windows desktops; Android verified via the Cognitive Edge mobile bridge.
- **Week 11-12:** Demo recording produced; final documentation; Phase 1 review with QVAC team.

### Phase 2 (months 4-7)

- **Month 4:** Hired JS engineer onboarded, port of preprocessing pipeline begins
- **Month 5:** Spectral biomarkers ported and benchmarked against Phase 1 Python service
- **Month 6:** Simplified classifier ported, npm package draft published
- **Month 7:** Full Cognitive Edge running on QVAC SDK directly, P2P prototype delivered, public announcement

### Acceptance criteria

Specific acceptance criteria for each milestone will be agreed in writing with the QVAC team before Phase 1 begins. SkyBrain will not invoice for any milestone payment until deliverables are accepted.

---

## 10. Open questions for QVAC team

Listed honestly because we'd rather surface these now than discover them later. Several have been at least partially resolved during the pre-application Phase 0 build and are noted as such:

1. **License** — Apache 2.0 (chosen and applied).
2. **Plugin architecture conventions.** Reading docs.qvac.tether.io confirmed plugins are TypeScript npm packages using `definePlugin()` + `invokePlugin()`, not JSON manifests. The Phase 1 deliverable shipped is therefore a *design package* (`plugin-manifest/README.md` + `capability-schema.json` + `package.json.example`); the Phase 2 deliverable is the actual `@skybrain/qvac-bci-addon` npm package. We'd appreciate review of the package shape before publishing to npm.
3. **Streaming transport for `/v1/eeg/ingest`.** SSE (OpenAI-style) vs WebSocket (familiar to SkyBrain's existing relay) vs `invokePluginStream` (QVAC-idiomatic but only callable from JS clients). The Phase 1 deliverable defaults to file-replay; the streaming wire format needs the alignment call to lock.
4. **BCIModelStore provenance.** Should `/v1/bci/classify` accept caller-provided model paths, maintain an on-disk store keyed on `(paradigm, n_channels)`, or fall back to synthetic-baseline defaults with a loud warning? Phase 1 Week 3-4 needs this resolved.
5. **Cognitive Edge as a QVAC reference app.** Does QVAC team want this submitted through a particular process? Branding alignment expectations?
6. **WDK integration.** Should the integration include WDK for any payment flows (e.g., participants in the optional consent-driven data marketplace receiving USDT)? We are open to scoping this in if it advances QVAC's broader vision.
7. **Holepunch / Pears P2P primitives.** Phase 2 explores delegated inference. Are there Holepunch reference implementations we should align with?
8. **iOS native runtime.** Phase 2 targets iOS via Expo. Is there a preferred QVAC mobile pattern beyond Expo we should evaluate?

---

## 11. Repository placement

We propose:

- **Primary repository:** SkyBrain-owned GitHub org, public, MIT or Apache 2.0
- **Mirror or fork:** Whatever placement QVAC team prefers in their ecosystem (under tetherto org, listed in QVAC documentation, etc.)
- **Coordination:** Discord and Keet for direct communication; GitHub issues for technical discussion

If QVAC team prefers the repository live primarily inside the tetherto org with SkyBrain as maintainer, we are equally open to that.

---

## 12. Closing technical note

We have built most of what is needed for QVAC to ship a real BCI capability. The work to integrate is bounded, the architecture is clean, and the boundary between open and proprietary is honest. We are proposing this partnership because it accelerates work we are doing anyway and aligns the output with the ecosystem we believe in.

The two-phase structure is a discipline imposed on ourselves to make the bet less risky for QVAC. Phase 1 ships in three months and proves the architecture. Phase 2 follows only if Phase 1 lands well. The total grant ask is sized to what the work genuinely costs, not what we think we can extract.

If anything in this brief is technically off, or QVAC team wants to restructure scope before formal application, we welcome direct technical conversation.

---

**Rakesh C. Jakati**
Founder & CEO, SkyBrain Neurotech
rakesh@skybrain.in
www.skybrain.in
Bengaluru, India
