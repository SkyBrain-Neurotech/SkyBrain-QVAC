# SkyBrain × QVAC: Brain-Computer Interface Layer for Local-First AI

**Proposal type:** Ecosystem partnership and enhancement grant
**Submitting org:** SkyBrain Neurotech, Bengaluru, India
**Contact:** Rakesh C. Jakati, Founder & CEO — rakesh@skybrain.in
**Date:** May 2026

---

> **Status — May 2026.** A reference implementation of the Phase 1 deliverables is already live and public at **https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC** under Apache 2.0, tagged `v0.1.0`. **Four of six endpoints** are functional end-to-end against the real SkyBrain SDK 1.5.0: `/v1/health`, `/v1/capabilities`, `/v1/eeg/biomarkers` (five biomarker bundles, `view=summary | detailed`), and `/v1/eeg/compare` — a two-recording differential whose auto-summary correctly identifies the classic eyes-closed Berger alpha effect (1600 %+ alpha increase over occipital channels) from real eye-open / eye-closed CSV recordings committed to the repo. Sixteen tests pass against the real SDK; cross-platform GitHub Actions CI is scaffolded for macOS, Linux, and Windows on Python 3.11 and 3.12; SHA-256 input hashing and timestamped JSON Lines audit logging are wired per the CDSCO-compliance commitment. Warm-cache latency on a 30-second, 4-channel recording: 125 ms for spectral biomarkers, 140 ms for full analysis — well inside the sub-200 ms budget. The proprietary SDK is gated to the Tether grants team for the duration of review via private GitHub collaborator invite (`SkyBrain-Neurotech/sdk-release`). This grant funds the remaining 9 weeks of Phase 1 — the two scaffolded endpoints (BCI classify, streaming ingest), Cognitive Edge integration, reference Jupyter notebook, cross-platform verification, and demo recording.

---

## The opportunity in one paragraph

On April 9, 2026, Paolo Ardoino committed Tether to expanding the QVAC ecosystem with "toolkits specifically designed for robotics and brain-computer interfaces." SkyBrain Neurotech proposes to build the BCI toolkit. We are a CE-certified non-invasive EEG platform deployed in three Indian universities, with a working SDK, a hardware-agnostic analysis application, a published research backbone, and a partnership with BrainBit (Europe's CE-certified non-invasive BCI hardware leader). We have already built independently most of what QVAC needs to add brain-computer interface as a first-class capability. We are proposing a coordinated two-phase contribution to ship this into the QVAC ecosystem under open-source license, with SkyBrain remaining the proprietary platform that drives upstream development.

## Why this proposal exists

QVAC's stated mission is local-first, on-device, peer-to-peer AI. The current QVAC SDK supports LLM inference, embeddings, speech, vision, OCR, and translation. QVAC Health (https://qvac.tether.io/products/health/) imports observational wearable data — heart rate, sleep, activity, voice-driven biomarker logging — but does not yet have the algorithmic neural-signal layer: real-time EEG biomarkers, BCI inference, or time-synchronised multi-modal physiology fusion (EEG + ECG + PPG aligned). QVAC MedPsy reasons about medical and psychological states but lacks physiological ground truth for stress, attention, anxiety, and sleep. SkyBrain provides exactly that neural-signal layer — and ingests cleanly into the cardiovascular signals Health already collects.

Brain-computer interfaces are exactly where QVAC's local-first thesis is most needed. Neural data is the most sensitive biometric data a person can generate. Cloud-based BCI processing creates the privacy violation Tether explicitly opposes. On-device EEG inference with consent-driven data ownership is the architecture the field needs, and Tether is the only entity publicly building the infrastructure to support it at scale.

SkyBrain has spent two years building this layer. We do not need to convince anyone that BCI matters. We need to ship the BCI integration into QVAC so that the trillion-agent local-first vision Ardoino describes has a credible neural signal foundation.

## What SkyBrain brings

We are not a research lab pitching a concept. We are a working platform with shipped product:

- **SkyBrain SDK** in Python: 50+ EEG biomarkers across spectral, connectivity, complexity, burst, and ERP measures. Five Bayesian classifiers with confidence gating and online learning. Real-time streaming with sub-15ms latency. CDSCO-compliant audit trails and deterministic computation.
- **BCI Studio** acquisition platform: five BCI paradigms (P300, SSVEP, Motor Imagery, Gesture, Cognitive State) with per-user adaptive calibration.
- **SkyBrain Analyze**: desktop application with 13 analysis views, hardware-agnostic format support (EDF, EDF+, BDF, HDF5, CSV, MAT, EEG), publication-ready statistical output with permutation tests and Bayesian inference.
- **Cognitive Edge**: consumer mobile application with Preparedness Index, real-time cognitive load and stress measurement, closed pilots running.
- **Hardware partnership** with BrainBit (CE-certified, Europe-based), India dealer relationship signed, global joint LOI pending technical demo completion.
- **University deployments** at three Indian institutions (St. Joseph's, BNMIT, SEA University) generating ongoing research subscription revenue.
- **Research credibility** through Dr. Saketh Malipeddi (Head of Meditation & Consciousness Research, first author of NIMHANS/Springer paper on EEG signatures of meditation, March 2026) and Dr. Ganesh R. Naik (Head of Research, Top 2% global biomedical scientist, 150+ publications).

What this proposal funds is the work to make this platform speak QVAC's language and live inside QVAC's ecosystem.

## Proposed contribution

Two coordinated deliverables across two phases.

### Phase 1 — QVAC-compatible BCI service layer

**Duration:** 3 months
**Funding requested:** $100,000 - $150,000

SkyBrain SDK exposed as a local HTTP service implementing QVAC's OpenAI-compatible API. The QVAC SDK calls into SkyBrain over localhost for EEG ingestion, biomarker computation, and BCI classification. Runs alongside QVAC on desktop and as a backend service for QVAC Health on mobile.

Concrete deliverables at end of Phase 1:

- Open-source repository under permissive license (Apache 2.0 chosen) with the service layer code, documentation, and reference integration examples — already live at github.com/SkyBrain-Neurotech/SkyBrain-QVAC
- Plugin design package and capability schema. (Note: QVAC's plugin model is a TypeScript npm package using `definePlugin` + `invokePlugin`, not a JSON manifest as we initially assumed. The Phase 1 deliverable is a design doc + JSON Schema describing the HTTP contract that the Phase 2 `@skybrain/qvac-bci-addon` npm package will wrap.)
- End-to-end working demo: user wears BrainBit headband, opens Cognitive Edge mobile app, sees brain biomarkers (cognitive load, stress, relaxation, preparedness) displayed inside QVAC Health dashboard, all processed locally, no cloud calls
- Technical documentation suitable for inclusion in docs.qvac.tether.io
- Cross-platform compatibility: macOS, Linux, Windows desktop; Android via mobile bridge
- Reference Jupyter notebook demonstrating EEG-grounded prompts to QVAC MedPsy for psychological state reasoning

### Phase 2 — Native JavaScript port and Cognitive Edge as QVAC reference app

**Duration:** 3-4 months following Phase 1 completion
**Funding requested:** $150,000 - $350,000

Once Phase 1 has shipped and proven the architecture, Phase 2 delivers the native JavaScript port of SkyBrain SDK core capabilities, packaged as @skybrain/qvac-bci-addon following QVAC plugin conventions. Eliminates Python runtime dependency for true single-stack QVAC integration.

In parallel, Cognitive Edge is refactored to consume the QVAC SDK directly, becoming a published reference application in QVAC's ecosystem alongside Workbench and Health.

Concrete deliverables at end of Phase 2:

- npm-published @skybrain/qvac-bci-addon package conforming to QVAC plugin architecture
- Native JS implementation of core biomarker pipeline (spectral analysis, band power, complexity measures) running on Node.js, Bare runtime, and Expo
- Mobile compatibility verified on iOS and Android via Expo
- Cognitive Edge published as QVAC reference application with full documentation
- Performance benchmark comparing Phase 1 Python service against Phase 2 native JS
- Peer-to-peer extension exploring delegated EEG inference across multiple QVAC peers using Holepunch primitives

### Phase decision gate

Phase 2 funding is contingent on Phase 1 delivery quality. SkyBrain commits to ship Phase 1 deliverables before Phase 2 funds are released. If Phase 1 does not meet the agreed acceptance criteria, the partnership concludes with Phase 1 deliverables remaining open-source and freely available to the QVAC ecosystem.

## Total grant ask

**Combined Phase 1 + Phase 2: $250,000 - $500,000** based on final scope agreed with QVAC team. Paid in USDT or Bitcoin per Tether's standard grants structure. Released against milestone delivery, not upfront.

## What stays SkyBrain proprietary

Transparent boundaries from day one to prevent any IP ambiguity.

**Released as open-source under permissive license** (Apache 2.0 or MIT, QVAC team's preference):

- The QVAC service layer and plugin code (Phase 1)
- The npm-published BCI addon (Phase 2)
- Documentation, integration examples, reference notebooks
- The cross-platform compatibility layer

**Remains SkyBrain proprietary**:

- The full BCI Studio acquisition platform
- The five Bayesian classifier implementations (BayesianLDA, BayesianQDA, BayesianMultinomial, BayesianStateSpace, AdaptiveStateSpace)
- SkyBrain Analyze desktop application
- Per-user adaptive calibration logic
- Hybrid EMG-EEG signal decomposition methods (patent filing in progress)
- Preparedness Index composite scoring methodology (patent filing in progress)
- Onchain consent and burn-on-access infrastructure (patent filing in progress)
- Hardware partnership terms and pricing

The open-source addon provides the inference layer that lets QVAC applications consume SkyBrain capabilities. The full proprietary platform continues to drive research, hardware sales, and enterprise deployments that fund SkyBrain's ongoing R&D. This is the same separation Tether uses with QVAC Fabric (open-source) and the broader Tether Data business (proprietary). The open layer accelerates ecosystem adoption while the proprietary platform sustains the business that builds the open layer.

## Strategic alignment with QVAC's roadmap

This proposal advances QVAC's stated direction along four dimensions:

**Local-first AI in healthcare.** QVAC MedPsy launched May 7, 2026 explicitly to enable medical reasoning on-device. EEG provides physiological ground truth for the psychological domains MedPsy reasons about — stress, attention, anxiety, sleep, focus. The integration this proposal funds gives MedPsy a neural signal foundation that no other input modality can provide.

**Cross-platform device coverage.** QVAC's design promise is one codebase running on Linux, macOS, Windows, Android, iOS. EEG hardware is a new input modality that QVAC does not yet support. This proposal extends QVAC to a new sensor category that opens a multi-billion-dollar BCI market.

**Peer-to-peer inference.** Phase 2 explores delegated EEG inference across QVAC peers using Holepunch primitives. A research institution can offer their compute to process EEG from consumer devices that lack the GPU for local foundation model inference. This is the P2P AI swarm Ardoino describes, applied to a real use case.

**Emerging markets reach.** SkyBrain's deployments are in India. University students, researchers, wellness practitioners, and esports venues across emerging markets need consent-respecting, local-first neural AI. They cannot afford or trust cloud-based alternatives. This proposal brings QVAC's stack to a population segment that classical SaaS BCI providers do not serve.

## Why SkyBrain over other potential partners

No other entity has the combination of: working CE-certified non-invasive BCI platform, deployed in production with paying customers, with adaptive ML, hardware-agnostic analysis tooling, and published research backbone, and an existing consent-driven blockchain consent layer, run by a founder team with academic credibility through Dr. Naik and Dr. Saketh.

Most BCI companies are either invasive (Neuralink, Synchron, Precision, Paradromics, Blackrock Neurotech) or research-stage non-invasive (Merge Labs, Neurable). Blackrock is already in Tether's portfolio. SkyBrain is the natural non-invasive complement, with shipped product, multi-region deployment, and an open-source-aligned philosophy that fits QVAC's ecosystem better than alternatives.

## Team

**Rakesh C. Jakati** — Founder & CEO. Leads platform development. Solo founder with 80% ownership in a clean cap table (no prior dilution, no SAFEs, no convertibles).

**Dr. Ganesh R. Naik** — Head of Research and Academics. Top 2% global biomedical scientist, 150+ peer-reviewed publications. Recent author of *EEG Signal Processing with Python* (Springer, 2025).

**Dr. Saketh Malipeddi** — Head of Meditation & Consciousness Research. First author of NIMHANS/Springer paper on EEG signatures of meditation (Mindfulness, March 2026, DOI: 10.1007/s12671-026-02790-1).

**Dr. Bhaskar Tripathi** — AI/ML Advisor. PhD with published work in deep learning, reinforcement learning, and EEG emotion classification.

**Aranyak Banerjee** — BCI Research Scientist (PhD scholar). Leads real-time processing and EEG analysis.

**Vinay Devabhakthuni** — Blockchain infrastructure. Leads SkyBrain Chain implementation.

The Phase 1 engineering for the QVAC service layer is led by the founder with intern support. The Phase 2 native JS port adds a dedicated mid-level JavaScript engineer hired from the grant funds.

## Company snapshot

- **Stage:** Bootstrapped. Revenue-generating through university subscriptions, hardware sales, and research partnerships. Zero outside investment to date.
- **Burn rate:** Near zero. YC Student Stack credits cover infrastructure. Founders and advisors work for equity. Interns supplement engineering.
- **Cap table:** Founder Rakesh Jakati 80%, Director Kavya 20%. One non-dilutive $75,000 equity-free blockchain research grant. No SAFEs, no convertibles, no prior raises.
- **Current revenue:** Hardware sales and Research Stack subscriptions at three universities, growing.
- **Active partnerships:** BrainBit (India dealer signed, global LOI pending demo), Samsung India (three-area proposal under review), Blackrock Neurotech (NDA active), NIMHANS (research collaboration).

A grant of $250K-500K from Tether is not capital we need to keep operating. It is capital that compresses 12-18 months of work into 4-6 months and aligns the result with QVAC's ecosystem from day one. We are doing this work anyway. With Tether support, we ship it inside QVAC, open-source, faster, and in coordination with the broader ecosystem direction.

## Why now

Three things make this the right moment:

1. Tether has just published the developer grants program (May 11, 2026) and the QVAC MedPsy launch (May 7, 2026). The infrastructure to evaluate and support a BCI ecosystem contribution exists today; it did not exist six months ago.
2. SkyBrain's BrainBit partnership is closing. Once the joint LOI signs, SkyBrain becomes the validated software layer for BrainBit's hardware portfolio worldwide. Integrating with QVAC at this moment means QVAC's BCI capability arrives with a credentialed European hardware backbone, not as a research curiosity.
3. The Indian DPDP Act 2023 and the broader regulatory turn toward local-first health data make India the most fertile ground in the world for a consent-respecting BCI platform. SkyBrain is positioned to be that platform. Bringing it under the QVAC ecosystem positions Tether to lead this category globally from a non-Western starting point.

## What we ask for from QVAC team

A first technical conversation to validate scope and structure. From there:

1. Agreement on Phase 1 deliverables and milestones (2 weeks)
2. Grant agreement signed (4 weeks from initial conversation)
3. Phase 1 kickoff with weekly check-ins (3 months)
4. Phase 1 delivery and review (end of month 3)
5. Phase 2 decision (4 weeks after Phase 1 delivery)
6. Phase 2 execution (3-4 months)
7. Public announcement of SkyBrain as QVAC ecosystem partner with shipped BCI capability

## Closing

QVAC will have a BCI toolkit eventually. The question is whether it ships in 2026 with a real platform behind it, or in 2028 after the field has fragmented. SkyBrain has done the hard work to make 2026 possible. We are proposing the partnership that turns Ardoino's stated commitment into shipped product, this year.

We are available to begin discussion immediately.

---

**Rakesh C. Jakati**
Founder & CEO, SkyBrain Neurotech
rakesh@skybrain.in
www.skybrain.in
Bengaluru, India
