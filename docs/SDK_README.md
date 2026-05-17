<div align="center">

# SkyBrain BCI Studio — SDK

**Turn raw EEG into clinical insights — in 3 lines of Python.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![SDK v0.2.2](https://img.shields.io/badge/SDK-v0.2.2-FF6B35.svg)](#quick-start)
[![License](https://img.shields.io/badge/license-Proprietary-E53935.svg)](#license)
[![CDSCO Compliant](https://img.shields.io/badge/CDSCO-compliant-00C853.svg)](#compliance)

[Website](https://skybrain.in) &middot; [API Reference](api_reference.md) &middot; [BCI User Guide](BCI_USER_GUIDE.md) &middot; [Capabilities](capabilities.md) &middot; [Contact Sales](mailto:info@skybrain.in)

</div>

---

## What is SkyBrain SDK?

SkyBrain SDK is a Python library for EEG signal processing, clinical analysis, brain-computer interfaces (BCI), adaptive intelligence (signal quality + artifact detection + cognitive metrics), and intervention validation. It works with everything from 4-channel consumer headbands to 19-channel clinical EEG systems.

> **Default model accuracy.** Every default model shipped in this SDK (BCI
> classifiers, signal-quality classifier, artifact detector) is trained on
> synthetic feature distributions so the pipeline runs end-to-end without
> calibration data. These baselines are **not validated on real EEG** and
> must not drive production decisions. Collect per-user calibration via
> `partial_fit()` before relying on predictions.

**One function call. Fifty biomarkers. Publication-ready statistics.**

```python
import skybrain_sdk as sky

result = sky.quick_analyze("session.edf")
print(result.summary())
```

```
Recording: 8 channels, 180.0s @ 256 Hz
QC: PASS (score: 0.94)
Alpha Power: 12.3 µV² | Theta/Beta Ratio: 2.1
Dominant Frequency: 10.2 Hz | Spectral Edge 95%: 28.4 Hz
```

---

## Why SkyBrain?

| Challenge | How SkyBrain Solves It |
|-----------|----------------------|
| **Subjective outcomes** | Objective EEG biomarkers with statistical significance testing |
| **Months of development** | 3-line integration — load, analyze, report |
| **No signal processing expertise** | Automated preprocessing, QC, and plain-English interpretation |
| **Regulatory burden** | CDSCO-compliant audit trails, deterministic computation, SHA-256 traceability |
| **Fragmented tooling** | One SDK: preprocessing → analysis → BCI → adaptive intelligence → export |
| **Per-user variability** | Adaptive intelligence learns per-user/per-device baselines via `partial_fit()` (EMA updates on class statistics) |

---

## Quick Start

### Install

```bash
pip install skybrain-sdk
```

### Analyze a Recording

```python
import skybrain_sdk as sky

recording = sky.load_recording("session.edf")
result = sky.run_analysis(recording)
print(result.summary())
```

### Compare Pre vs. Post Intervention

```python
comparison = sky.quick_compare(
    "session.edf",
    segment_a_label="baseline_pre",
    segment_b_label="baseline_post"
)
print(comparison.summary())
```

```
Alpha Power: increased 23.4% (p=0.003, d=0.72, medium effect) ✓ significant
Theta/Beta: decreased 15.1% (p=0.021, d=0.54, medium effect) ✓ significant
```

### Build a Pipeline

```python
pipeline = sky.Pipeline("clinic_workflow")
pipeline.add_filter(highpass=0.5, lowpass=45.0, notch=[50.0])
pipeline.add_qc()
pipeline.add_features("routine_eeg_default")

result = pipeline.run(recording)
```

### Stream Live from Hardware

```python
# Guided calibration with the SkyBrain Headband
result = sky.run_skybrain_live(calibrate=True, duration_sec=60)
result["model"].save_model("my_session.skybrain_model")
```

---

## Core Capabilities

### Signal Preprocessing
- **Bandpass, highpass, lowpass, notch filters** with configurable order
- **ICA artifact removal** — automated component labeling (EOG, EMG, cardiac)
- **Autoreject** — epoch-level artifact rejection
- **Re-referencing** — average, linked-ear, bipolar montages
- **Channel repair** — mirror-partner interpolation for bad electrodes
- **MNE bridge** — seamless conversion to/from MNE-Python objects

### 50+ Biomarker Extraction
- **Spectral power** — absolute/relative band power (delta, theta, alpha, beta, gamma)
- **Peak frequency, IAF, spectral edge** (SE50, SE95)
- **Spectral parameterization** — aperiodic slope, periodic peaks (FOOOF/specparam)
- **Nonlinear dynamics** — sample entropy, approximate entropy, DFA, Higuchi FD, Hurst exponent
- **Hjorth parameters** — activity, mobility, complexity
- **Connectivity** — coherence, PLI, wPLI, Granger causality, graph theory metrics
- **Cross-frequency coupling** — phase-amplitude coupling (PAC)
- **Microstates** — polarity-invariant k-means clustering

### Statistical Testing
- **Permutation tests** — non-parametric significance testing
- **Cluster permutation tests** — spatiotemporal correction
- **Bayesian t-tests** — Bayes factors for evidence quantification
- **Effect sizes** — Cohen's d, Hedge's g with confidence intervals
- **Multiple comparisons correction** — FDR, Bonferroni, Holm-Bonferroni

### Brain-Computer Interfaces (BCI)

Seven paradigms with five Bayesian classifiers — all with built-in uncertainty quantification:

**Classifiers:**

| Model | Best For |
|-------|----------|
| **BayesianLDA** | Default — fast, linear, regularized |
| **BayesianQDA** | Non-linear decision boundaries |
| **BayesianMultinomial** | Discrete/count features |
| **BayesianStateSpace** | Hidden state tracking (Kalman filter) |
| **AdaptiveStateSpace** | Online adaptation (Extended Kalman filter) |

All models support `fit()`, `predict()`, `partial_fit()`, `save_model()`, `load_model()`.

**Supported Paradigms:**

| Paradigm | Classes | Channels | Features |
|----------|---------|----------|----------|
| `cognitive_workload` | 2–4 (configurable) | Any 4+ | Band ratios, permutation entropy, LZ complexity |
| `cognitive_stress` | 2–4 (configurable) | Any 4+ | Band ratios, permutation entropy, LZ complexity |
| `cognitive_drowsiness` | 2–4 (configurable) | Any 4+ | Band ratios, permutation entropy, LZ complexity |
| `gesture` (Blink/Clench) | 4–6 classes | Any 4+ (BrainBit 4ch ideal) | MAV, WL, ZCR, RMS, Hjorth, Beta/Gamma power, cross-channel asymmetry |
| `motor_imagery` | 3–4 (Rest, L/R Hand, Feet) | Any 4+ | ERD/ERS, band power, laterality indices |
| `p300` | 2 (target / non-target) | Fz, Cz, Pz, P3, P4, P7, P8 | Event-related potential features |
| `ssvep` | 2+ (per stimulus frequency) | Fz, Cz, Pz, P3, P4, P7, P8 | Frequency-tagged response features |

**Gesture class mapping:**

| Class | Label | Description |
|-------|-------|-------------|
| 0 | Neutral | Face fully relaxed |
| 1 | Left Clench | Clench left-side teeth firmly |
| 2 | Right Clench | Clench right-side teeth firmly |
| 3 | Full Clench | Clench both sides firmly |
| 4 | Left Blink | Left eye blink |
| 5 | Right Blink | Right eye blink |

**Motor Imagery class mapping:**

| Class | Label | Description |
|-------|-------|-------------|
| 0 | Rest | No motor imagery |
| 1 | Left Hand | Imagine left hand movement |
| 2 | Right Hand | Imagine right hand movement |
| 3 | Feet | Imagine foot movement (optional, 4-class mode) |

### SkyBrain Adaptive Intelligence

SkyBrain's adaptive layer is split into three packages:

- `skybrain_sdk.adaptive` — `AdaptiveFoundation` (EKF base), `AdaptiveUserProfile`
- `skybrain_sdk.signal_quality` — `SignalQualityClassifier`, `ArtifactDetector`, `AcquisitionGuide`, `RecordingOptimizer`, `compute_metric_confidence`, `BatchAnalyzer`
- `skybrain_sdk.cognitive_metrics` — composite cognitive scores

Every classifier here is built on `AdaptiveFoundation` (an EKF-based
`AdaptiveStateSpace` subclass) and updates online via `partial_fit()` (EMA
over class statistics, not a full Bayesian posterior update).

> **Default weights are synthetic baselines.** The `generate_default_*`
> helpers fit each model on seeded random feature distributions so the
> pipeline runs end-to-end without user data. These baselines are **not
> validated on real EEG**. Collect per-user calibration before relying on
> predictions.
>
> `skybrain_sdk.zuna` is a deprecated re-export shim kept for one release;
> update imports to the new packages above.

| Module | Class | Function |
|--------|-------|----------|
| **Signal Quality** | `signal_quality.SignalQualityClassifier` | 4-class per-channel quality (NoSignal/Good/Fair/Poor). 6-feature vector: RMS, Std, Kurtosis, ZCR, Line Noise Ratio, Spectral Entropy |
| **Artifact Detection** | `signal_quality.ArtifactDetector` | 5-class artifact detection (Clean/Blink/Muscle/Drift/ElectrodePop). 6-feature vector with refractory periods |
| **Cognitive Metrics** | `cognitive_metrics.compute_all_scores` | Cognitive scores (0–100): Meditation, Cognitive Load, Drowsiness, Focus. Band-power based with EMA smoothing (α=0.15) — heuristic defaults, pending clinical validation |
| **Guidance** | `signal_quality.AcquisitionGuide` | Electrode placement feedback with quality trajectory tracking. 10-20 electrode mapping with anatomical hints |
| **Optimizer** | `signal_quality.RecordingOptimizer` | Thompson Sampling bandit for filter config auto-tuning. 6 discrete configs (notch 50/60 Hz × bandpass combinations) |
| **User Profile** | `adaptive.AdaptiveUserProfile` | Cross-session persistence in `adaptive_profiles/{device}_{user}.json`. Stores quality state, artifact state, optimizer state, baselines |
| **Foundation** | `adaptive.AdaptiveFoundation` | EKF-based AdaptiveStateSpace base class with device-type and channel-aware initialization |

**Usage:**

```python
from skybrain_sdk.signal_quality import SignalQualityClassifier, ArtifactDetector
from skybrain_sdk.cognitive_metrics import compute_all_scores

# Signal quality assessment (synthetic-baseline model; calibrate per user)
quality = SignalQualityClassifier()
labels = quality.predict(eeg_window)  # ['Good', 'Good', 'Fair', 'Poor']
quality.partial_fit(eeg_window, labels)  # Online adaptation (EMA over class statistics)

# Artifact detection (synthetic-baseline model; calibrate per user)
detector = ArtifactDetector()
artifacts = detector.predict(eeg_window)  # ['Clean', 'Blink', 'Clean', 'Muscle']

# Cognitive metrics
scores, _ = compute_all_scores(band_powers)
# {'meditation': 72.3, 'cognitive_load': 45.1, 'drowsiness': 12.8, 'focus': 68.9}
```

### Real-Time Streaming
- **Chunk-based processing** with configurable windows and overlap
- **Session state persistence** — save/restore mid-session
- **Confidence-weighted aggregation** with reject thresholds
- **WebSocket relay** (`ws://localhost:8765`) — JSON prediction streaming to external systems

### Export & Reporting
- **Formats:** JSON, CSV, Excel, PDF, EDF+, HDF5
- **BIDS export** — Brain Imaging Data Structure for open science
- **MNE bridge** — `to_mne_raw()`, `to_mne_epochs()`, `from_mne_epochs()`
- **Model files** — save/load trained BCI models (`.skybrain_model`, `.pkl`)

### Quality Control
- Automated QC scoring on every recording
- Channel dropout detection
- Line noise assessment
- Amplitude range validation
- Data integrity verification (SHA-256 file hashes)
- Real-time signal-quality monitoring during acquisition

---

## Who Is It For?

### Clinics & Wellness Centers
Prove your interventions work with objective brain data. Replace subjective questionnaires with statistical evidence. Generate client-facing reports that show real change.

### Research Institutions
Publication-ready analysis pipeline. BIDS-compliant export. Reproducible computation with experiment logging and `@reproducible` decorator. Synthetic dataset generators for method validation.

### Motorsport & Sports Performance
Real-time cognitive workload, drowsiness, and focus monitoring during competition or training. Adaptive profiling builds driver/athlete-specific baselines via `partial_fit()` calibration sessions. WebSocket streaming enables live telemetry integration.

### Pharma & MedTech
CDSCO-compliant audit trails. Deterministic, traceable computation. Batch processing for multi-site clinical trials. Statistical testing built for regulatory submissions.

### Developers & Integrators
Clean Python API. Chainable pipelines. Async support. Event bus for real-time monitoring. Plugin system for custom metrics. WebSocket BCI streaming for robotics, games, and assistive tech.

---

## Architecture

```
skybrain_sdk/
  api.py               # load_recording, run_analysis, quick_analyze, quick_compare
  pipeline.py           # Chainable analysis pipelines
  streaming/            # Real-time chunk processing, session state
  preprocessing/        # Filters, ICA, MNE bridge, autoreject
  features/             # Spectral, nonlinear, ANS feature extraction
  analysis/             # Spectral params, connectivity, microstates, source localization
  bci/                  # 5 Bayesian models, 7 paradigms, calibration, inference
  │  models/            # LDA, QDA, Multinomial, StateSpace, AdaptiveStateSpace
  │  features/          # Cognitive, gesture, P300, SSVEP, motor imagery
  │  preprocessing/     # BCI-specific filtering, trials, channel repair
  │  calibration.py     # Generic calibration loop with cross-validation
  │  calibration_gesture.py     # 60-trial Blink/Clench protocol
  │  calibration_motor_imagery.py  # Motor imagery calibration
  │  inference.py       # predict_bci() with uncertainty quantification
  │  model_store.py     # Versioned model persistence with rollback
  │  defaults.py        # Synthetic-baseline weights (dev only; calibrate per user)
  adaptive/             # Shared EKF foundation + profile store
  │  foundation.py      # AdaptiveFoundation (EKF base)
  │  user_profile.py    # AdaptiveUserProfile — cross-session persistence
  signal_quality/       # Per-channel quality + artifact detection
  │  classifier.py      # 4-class per-channel quality classifier
  │  artifact_detector.py  # 5-class artifact classifier
  │  guidance.py        # Electrode placement feedback
  │  optimizer.py       # Thompson Sampling filter tuning
  │  confidence.py      # Per-metric reliability helper
  │  batch_analyzer.py  # Offline recording analysis
  │  defaults.py        # Synthetic-baseline models (dev only; calibrate per user)
  cognitive_metrics/    # Composite cognitive scores
  │  composite_scores.py   # Meditation, CogLoad, Drowsiness, Focus
  zuna/                 # DEPRECATED re-export shim; use packages above
  stats/                # Hypothesis testing, effect sizes, corrections
  export/               # BIDS, reports, model files, EDF+, HDF5
  qc/                   # Automated quality control
  compliance/           # CDSCO audit trails, consent, GDPR
  licensing/            # RSA-signed, tiered features, revocation, audit
  config/               # Device profiles, analysis profiles
  datasets/             # Synthetic generators, PhysioNet/MOABB loaders
  io/                   # EDF/BDF/CSV loading with channel validation
  viz/                  # Plot utilities (raw, spectrum, topomap, ERP, connectivity)
```

---

## Device Support

Works out of the box with the **SkyBrain Headband** (O1, O2, T3, T4 @ 250 Hz).

Custom devices can be registered via `DeviceConfig`:

```python
sky.print_device_info()
# SkyBrain Headband: 4 channels (O1, O2, T3, T4) @ 250 Hz
```

Compatible with any EEG system that outputs EDF or CSV files (4–64 channels, 100–2000 Hz).

---

## CLI Tools

Eight command-line tools ship with the SDK:

```bash
skybrain-validate --file recording.edf           # Full QC + feature validation
skybrain-live info                                # Device specs + Bluetooth scan
skybrain-live train --file session.edf            # Train BCI model offline
skybrain-live stream --model model.joblib         # Live streaming with trained model
skybrain-live demo                                # Synthetic demo (no hardware)
skybrain-demo                                     # Full SDK feature demo
skybrain-analyze --file session.edf               # Annotated EDF analysis
```

---

## Compliance & Security

- **CDSCO-compliant** — deterministic computation, audit trails, consent management
- **GDPR-ready** — data minimization, right to erasure support
- **Traceable** — SHA-256 file hashes, experiment logging, `@reproducible` decorator
- **License-gated** — hardware-locked activation, feature tier management (Basic/Professional/Enterprise)
- **Integrity-verified** — compiled security modules, embedded RSA key validation
- **Revocation checking** — secure cached revocation list with online fallback

---

## Requirements

- Python 3.11+
- Windows / macOS / Linux
- 4 GB RAM minimum
- NumPy (<2.1.0), SciPy, pandas (core); MNE-Python, scikit-learn (optional, for advanced features)

---

## Getting Started

| Resource | Description |
|----------|-------------|
| [API Reference](api_reference.md) | Full SDK API — classes, methods, parameters |
| [BCI User Guide](BCI_USER_GUIDE.md) | BCI paradigm workflows, calibration, gesture/MI training |
| [Capabilities](capabilities.md) | Full platform capabilities for evaluation |

---

## License

Proprietary — SkyBrain Neurotech. [Contact us](mailto:info@skybrain.in) for licensing.

---

<div align="center">

**[SkyBrain Neurotech](https://skybrain.in)** &middot; [info@skybrain.in](mailto:info@skybrain.in)

*Research-grade EEG analysis, adaptive intelligence, and BCI — from electrode to insight.*

</div>
