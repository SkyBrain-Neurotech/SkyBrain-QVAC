# SkyBrain SDK Strategy — Language, Platform & Roadmap

**Prepared by:** SkyBrain Engineering Team
**Date:** March 2026

---

## 1. Why Python SDK First?

### 1.1 The Research Community Speaks Python

EEG and neuroscience research runs on Python. The tools researchers already use — and expect to integrate with — are all Python-native:

| Tool | Role | Our Integration |
|------|------|----------------|
| **MNE-Python** | De-facto EEG analysis standard | `to_mne_raw()`, `from_mne_epochs()`, `to_mne_evoked()` — bidirectional conversion |
| **NumPy / SciPy** | Numerical computing | Core dependency — all signal processing, all models |
| **Jupyter Notebooks** | Interactive analysis | 5 ready-made notebooks in `notebooks/` |
| **scikit-learn** | ML standard | Our Bayesian models follow the `fit(X, y)` / `predict(X)` contract |
| **matplotlib** | Plotting | `viz/plots.py` — 6 publication-ready plot functions |
| **pandas** | Data manipulation | DataFrames for features, results, exports |

A C++ SDK would require researchers to learn a new build system, manage memory, and lose access to their existing tool ecosystem. Python eliminates all of that.

### 1.2 Rapid Prototyping of BCI Models

We currently ship **6 Bayesian BCI models** across **7 paradigms**. The pace of BCI research means new model architectures emerge regularly. In Python:

- A new model class takes **1 day** to implement, test, and ship — inherit `BaseBayesianModel`, implement `_fit()` and `_predict_proba()`, done
- Researchers can subclass our models or swap in their own — no recompilation
- Online adaptation (our `AdaptiveStateSpace` with Extended Kalman Filter) was prototyped and validated in **3 days**

In C++, the same iteration cycle would take **2–4 weeks** per model (memory management, template specialization, cross-platform build testing).

### 1.3 Foundation Model Readiness

As foundation BCI models (pre-trained on large multi-subject datasets) become available, Python is the natural deployment target:

- Pre-trained weights load from pickle/joblib — standard Python serialization
- Fine-tuning on user data uses the same `fit()` API with transfer learning
- Our `SessionState` persistence (JSON-serializable) enables session-to-session adaptation
- Future foundation models from the research community will ship as Python packages first

### 1.4 Deployment Simplicity

```bash
pip install skybrain-sdk
```

That's the entire installation. No compiler toolchain, no CMake, no platform-specific binaries (except our Cython-compiled licensing modules, which ship as pre-built wheels).

The SDK runs on:
- Windows 10+ (primary)
- macOS 12+
- Linux (Ubuntu 22.04+)
- Any system with Python 3.11+ and numpy/scipy

### 1.5 What We Already Compile for Performance

Python-first does not mean Python-only. We already use compiled code where it matters:

| Component | Technology | Why |
|-----------|-----------|-----|
| **Circular buffer operations** | Numba `@jit(nopython=True)` | 3–5x faster than pure NumPy for real-time buffer updates |
| **Sample entropy, Lempel-Ziv, Higuchi FD** | Numba `@jit(nopython=True, cache=True)` | Complexity metrics — O(n²) algorithms need machine code |
| **Multiscale entropy, DFA** | Numba `@jit(parallel=True)` | Parallel computation across time scales |
| **Preprocessing filters** | Cython → `.pyd` | Compiled IIR/FIR filter implementations |
| **Connectivity metrics** | Cython → `.pyd` | Advanced connectivity (PLI, wPLI, Granger) |
| **Therapy metrics** | Cython → `.pyd` | Complexity and connectivity hot paths |
| **Pipeline core** | Cython → `.pyd` | Main pipeline execution loop |
| **Licensing** | Cython → `.pyd` (11 modules) | Cryptographic validation, tamper resistance |

**Total: 21 compiled `.pyd` modules + 9 Numba JIT functions** — all callable transparently from Python. The user writes `pipeline.run(recording)` and gets machine-code performance without knowing it.

---

## 2. When Do We Need C++?

### 2.1 The Trigger Points

C++ becomes necessary when **any** of these conditions are true:

| Condition | Why C++ | Current Status |
|-----------|---------|----------------|
| **Embedded deployment** (ARM Cortex, RISC-V) | No Python runtime available | Not yet needed |
| **Hard real-time guarantee** (<1 ms jitter) | Python GC pauses are unpredictable | Our current ~570 ms BCI loop tolerates GC |
| **On-device processing** (headband MCU) | Microsecond-level power constraints | Hardware partner decision |
| **Mobile SDK** (iOS/Android native) | App Store requires native code | Not yet needed |
| **Medical device certification** (IEC 62304) | Deterministic execution required for Class II+ | Future regulatory path |
| **Kernel-space drivers** | BLE stack customization | Currently using vendor SDK (NeuroSDK) |

### 2.2 What We Do NOT Need C++ For Today

| Current Need | Why Python Is Sufficient |
|-------------|------------------------|
| BCI inference at <30 ms | Already achieved — BayesianLDA runs in <15 ms in pure NumPy |
| Real-time streaming at 250 Hz | 4 ms inter-sample interval is well within Python's capability |
| Feature extraction (26 features) | NumPy vectorized operations, <5 ms per window |
| Complexity metrics | Already Numba-compiled to machine code |
| Desktop GUI performance | PySide6/Qt handles 30 FPS waveform display |

### 2.3 The C++ Transition Path

When C++ is needed, we don't rewrite — we **extract**:

```
Phase 1 (now):     Python SDK — full functionality, rapid iteration
Phase 2 (future):  C++ core library — extracted from proven Python algorithms
Phase 3 (future):  Python bindings (pybind11) wrapping the C++ core
```

This means:
- Python users see **zero API change** — same `Pipeline.run()`, same `StreamingSession`
- C++ users get a native library with the same algorithms
- Both share the same tested, validated computation kernels

---

## 3. Embedded Deployment — What Goes On-Board?

### 3.1 The Embedded Subset

Not everything needs to run on the headband. Here's what makes sense on-device vs what stays on the host:

| Component | On-Device (MCU) | On-Host (PC/Phone) | Rationale |
|-----------|:---:|:---:|-----------|
| **ADC sampling** | ✓ | | Hardware function |
| **Bandpass filter (5–35 Hz)** | ✓ | | Simple IIR, ~100 bytes RAM |
| **Notch filter (50/60 Hz)** | ✓ | | Single biquad, trivial |
| **Bad channel detection** | ✓ | | Flatline/saturation check — 3 comparisons per sample |
| **Feature extraction (band power)** | ✓ | | FFT on 250-sample window, feasible on Cortex-M4+ |
| **BCI model inference (LDA)** | ✓ | | Matrix multiply: 26 features × n_classes — microseconds |
| **Confidence score** | ✓ | | Shannon entropy of 2–5 probabilities — trivial |
| **Complexity metrics** | | ✓ | O(n²) algorithms, too heavy for MCU |
| **ICA decomposition** | | ✓ | Requires full dataset, not real-time |
| **Source localization** | | ✓ | Forward/inverse models need >100 MB data |
| **13 analysis views** | | ✓ | GUI — desktop only |
| **BIDS export** | | ✓ | File system operation |
| **Therapy metrics** | | ✓ | Graph theory, PAC — computationally heavy |
| **Licensing validation** | | ✓ | Requires network + crypto |

### 3.2 The Minimal Embedded Core

The smallest viable on-device BCI package would be:

```
Embedded BCI Core
├── iir_filter.c          — Bandpass + Notch (2 biquad sections)
├── channel_check.c       — Flatline/saturation/noise detection
├── fft_features.c        — Band power extraction (δ, θ, α, β, γ)
├── lda_inference.c        — BayesianLDA predict (matrix multiply)
├── confidence.c           — Shannon entropy computation
└── ring_buffer.c          — Circular sample buffer
```

**Estimated resource requirements:**

| Resource | Estimate |
|----------|----------|
| **Flash** | ~32 KB (code) |
| **RAM** | ~16 KB (buffers + model weights) |
| **CPU** | Cortex-M4F @ 80 MHz (sufficient for 250 Hz, 4 channels) |
| **Latency** | <1 ms per inference (LDA is a single matrix multiply) |
| **Power** | ~5 mW additional draw |

### 3.3 What About the Entire SDK Embedded?

**No.** The full SDK (196 files, ~56K lines, 25 modules) is not an embedded target. Reasons:

| SDK Component | Why It Can't Run on MCU |
|---------------|------------------------|
| Python runtime | Requires ~4 MB minimum (MicroPython), still no NumPy |
| NumPy/SciPy | ~30 MB installed, requires LAPACK/BLAS |
| Numba JIT | Requires LLVM (~200 MB) |
| PySide6/Qt | Desktop GUI framework |
| MNE-Python | Research analysis toolkit |
| Licensing (Cython) | Requires CPython ABI |
| pandas | ~50 MB installed |

The correct architecture is a **thin embedded core** (C, ~32 KB) that handles real-time signal conditioning and classification, with the **full SDK on the host** for advanced analysis, visualization, and export.

### 3.4 On-Device vs Host Communication

```
Headband MCU (C)                    Host Device (Python SDK)
┌────────────────────┐              ┌─────────────────────────┐
│ ADC → Filter → FFT │──── BLE ───→│ StreamingSession        │
│ → LDA → Confidence │   (result)  │ → Advanced Analysis     │
│ → BCI Class Output │             │ → 13 Views              │
└────────────────────┘              │ → Export                │
       ~1 ms total                  └─────────────────────────┘
```

Two transmission modes are possible:
1. **Raw mode** — Send raw 250 Hz samples over BLE (current approach), host does all processing
2. **Smart mode** — MCU runs filter + LDA, sends only BCI class + confidence over BLE, dramatically reducing bandwidth and host CPU load

---

## 4. Other SDKs We Can Build

### 4.1 SDK Variants from the Same Core

The Python SDK's modular architecture allows us to create purpose-built variants:

| SDK Variant | Target Audience | What It Contains | What It Excludes |
|-------------|----------------|-----------------|-----------------|
| **SkyBrain SDK (full)** | Researchers, clinicians | Everything — 25 modules, 196 files | Nothing |
| **SkyBrain BCI SDK** | BCI developers | `bci/`, `streaming/`, `features/`, `preprocessing/` | `therapy/`, `analysis/`, `export/`, `viz/`, `compliance/` |
| **SkyBrain Clinical SDK** | Therapists, clinicians | `therapy/`, `features/`, `analysis/`, `reporting/` | `bci/`, `streaming/`, `datasets/` |
| **SkyBrain Edge SDK** | IoT / embedded Python | `streaming/`, `bci/models/`, `features/` (no GUI deps) | `viz/`, `analysis/`, `therapy/`, MNE integration |
| **SkyBrain C Core** | Embedded MCU | Filter + FFT + LDA inference in C | Everything else |

### 4.2 Language-Specific SDKs

| Language | Use Case | Implementation Strategy | Priority |
|----------|----------|------------------------|----------|
| **Python** | Research, prototyping, Jupyter | ✅ Done — primary SDK | Shipped |
| **C** | Embedded MCU, on-device BCI | Extract filter + LDA core | High (when hardware partner commits) |
| **C++** | Desktop performance, mobile native | Wrap C core + add streaming | Medium |
| **JavaScript / TypeScript** | Web dashboards, browser BCI | WebSocket bridge to Python SDK backend | Medium |
| **Swift** | iOS app | C core via Swift bridging header | Low (after C core exists) |
| **Kotlin / Java** | Android app | C core via JNI / NDK | Low (after C core exists) |
| **Rust** | Safety-critical embedded | Rewrite C core with Rust safety guarantees | Future |
| **MATLAB** | Legacy research labs | Python-to-MATLAB bridge (already possible via MATLAB Engine) | Low |

### 4.3 Wrapper Architecture

Rather than rewriting the SDK in every language, we build **wrappers** around a shared core:

```
                    ┌──────────────────┐
                    │  C Core Library  │
                    │  (filter, FFT,   │
                    │   LDA, entropy)  │
                    └────────┬─────────┘
                             │
           ┌─────────┬───────┼───────┬──────────┐
           │         │       │       │          │
      ┌────▼───┐ ┌───▼──┐ ┌─▼──┐ ┌──▼──┐ ┌────▼────┐
      │pybind11│ │ JNI  │ │FFI │ │Wasm │ │ Swift   │
      │wrapper │ │bridge│ │    │ │     │ │ bridge  │
      └────┬───┘ └───┬──┘ └─┬──┘ └──┬──┘ └────┬────┘
           │         │      │       │          │
      ┌────▼───┐ ┌───▼────┐┌▼────┐┌─▼──────┐┌─▼─────┐
      │Python  │ │Android ││Rust ││Browser ││ iOS   │
      │  SDK   │ │  SDK   ││ SDK ││  SDK   ││ SDK   │
      └────────┘ └────────┘└─────┘└────────┘└───────┘
```

**Key principle:** The C core is the single source of truth for signal processing algorithms. Every wrapper calls the same compiled functions. This guarantees:
- Identical numerical results across all platforms
- One place to fix bugs
- One place to validate against research benchmarks

### 4.4 Web / JavaScript Strategy

For browser-based BCI applications:

| Approach | How It Works | Latency | Offline Capable |
|----------|-------------|---------|-----------------|
| **WebSocket bridge** | Browser ↔ WebSocket ↔ Python SDK backend | ~10–50 ms network overhead | No |
| **WebAssembly (Wasm)** | C core compiled to Wasm, runs in browser | ~2–5 ms (near-native) | Yes |
| **Web Bluetooth API** | Browser connects to headset directly via BLE | ~4 ms (same as native) | Yes |

The ideal web stack: **Web Bluetooth** (browser ↔ headset) + **Wasm C core** (filter + LDA in browser) = fully offline browser BCI with no server required.

### 4.5 REST API / Microservice

For cloud or server deployments:

```python
# Already possible today with the SDK
from skybrain_sdk import StreamingSession, Pipeline

# FastAPI / Flask wrapper
@app.post("/predict")
async def predict(eeg_chunk: List[List[float]]):
    result = session.process_chunk(np.array(eeg_chunk))
    return {"class": result.prediction, "confidence": result.confidence}
```

The SDK is already headless-capable (no GUI dependencies in the core). A thin HTTP wrapper turns it into a microservice.

---

## 5. SDK Comparison Matrix

| Capability | Python SDK (Now) | C Core (Future) | JS/Wasm (Future) | Mobile (Future) |
|-----------|:---:|:---:|:---:|:---:|
| BCI inference | ✓ (<30 ms) | ✓ (<1 ms) | ✓ (~5 ms) | ✓ (via C core) |
| 7 paradigms | ✓ | Subset (LDA only) | Subset | Subset |
| Real-time streaming | ✓ | ✓ | ✓ (Web Bluetooth) | ✓ |
| Feature extraction | ✓ (26 features) | ✓ (band power) | ✓ (band power) | ✓ (band power) |
| ICA / Source Loc | ✓ | ✗ | ✗ | ✗ |
| 13 analysis views | ✓ (desktop) | ✗ | ✗ | Custom UI |
| Therapy metrics | ✓ | ✗ | ✗ | ✗ |
| BIDS export | ✓ | ✗ | ✗ | ✗ |
| Jupyter integration | ✓ | ✗ | ✗ | ✗ |
| MNE-Python bridge | ✓ | ✗ | ✗ | ✗ |
| Embedded MCU | ✗ | ✓ | ✗ | ✗ |
| Browser deployment | ✗ | ✗ | ✓ | ✗ |
| App Store deployment | ✗ | ✗ | ✗ | ✓ |
| Installation | `pip install` | CMake / vendor | npm / CDN | CocoaPods / Gradle |

---

## Summary

| Question | Answer |
|----------|--------|
| **Why Python first?** | Research community standard, rapid model iteration (1 day vs 4 weeks), MNE/Jupyter/scikit-learn ecosystem, `pip install` deployment |
| **When C++?** | Embedded MCU, hard real-time (<1 ms), mobile native, medical device certification |
| **Entire SDK embedded?** | No — only the BCI core (~32 KB flash, ~16 KB RAM): filter + FFT + LDA + confidence |
| **Other SDKs?** | BCI-only, Clinical-only, Edge, C Core, JS/Wasm, Swift, Kotlin — all wrapping a shared C core |
| **Wrapper strategy?** | Single C core library → pybind11 (Python), JNI (Android), FFI (Rust), Wasm (browser), Swift bridging (iOS) |

---

*The Python SDK is our velocity layer — ship fast, iterate with researchers, validate models. The C core is our durability layer — deploy everywhere, certify for medical devices, run on microcontrollers. Both will coexist.*
