# User Guide — `skybrain-qvac-bci`

A step-by-step walkthrough for someone who has never run this service
before. By the end you'll have a working local installation, a sample
recording analysed, real biomarker output on screen, and an audit log
on disk.

If you already know your way around Python and just want the
three-command install, the [README](../README.md) has it. This guide
goes slow on purpose.

---

## What this is, in one paragraph

`skybrain-qvac-bci` is a small HTTP server you run on your own
machine. You send it the path to an EEG recording (an `.edf` file from
a BrainBit headset, an OpenBCI cap, or anyone else's hardware); it
returns biomarkers — band powers, cognitive metrics, quality scores —
computed by SkyBrain's proprietary EEG SDK. Nothing leaves your
computer. It's the local glue between SkyBrain's research-grade
signal-processing engine and Tether's [QVAC](https://docs.qvac.tether.io)
local-AI ecosystem.

You don't write any code to use it. You install it, start it, and hit
its endpoints with `curl` or any HTTP client.

---

## Before you start — what you'll need

You need three things on your computer:

1. **Python 3.11 or newer.** Check by running `python --version` in a
   terminal. If you don't have it, download from
   [python.org/downloads](https://www.python.org/downloads/) and during
   install make sure to tick **"Add Python to PATH"** on Windows.
2. **Git.** Check by running `git --version`. If missing, install from
   [git-scm.com](https://git-scm.com/downloads).
3. **A SkyBrain SDK wheel.** This service wraps a proprietary library
   you can't `pip install` from PyPI. You get a versioned wheel
   (`.whl` file) from the [Releases page of this repository](https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/releases).
   It's about 5 MB.

If you want to follow along with real data you should also have either:
- a BrainBit headset (or any EEG device) that exports `.edf` files, or
- the SDK's built-in synthetic generator (we'll use it in step 6).

Operating systems supported: **macOS 12+, Linux (Ubuntu 22.04+),
Windows 10+**. The walkthrough below uses Windows PowerShell commands;
substitute `source .venv/bin/activate` for the Activate line on
macOS/Linux.

---

## Step 1 — Clone the repository

Open PowerShell (or Terminal on macOS/Linux). Pick a folder for the
work and clone:

```powershell
cd D:\projects                                        # wherever you want it
git clone https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC.git
cd SkyBrain-QVAC
```

You should now see a folder structure with `service/`, `docs/`,
`plugin-manifest/`, etc.

> **What just happened?** You downloaded the open-source bridge. None
> of SkyBrain's proprietary algorithms are in there — that's coming in
> the next step.

---

## Step 2 — Create an isolated Python environment

This keeps the bridge's dependencies from clashing with anything else
on your system.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **PowerShell complains about "running scripts is disabled"?** Run
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> once, then re-try the Activate command.

After activation your prompt should show `(.venv)` at the front. Every
Python command you run from now on uses this isolated environment.

---

## Step 3 — Install the bridge

This installs FastAPI, uvicorn, pytest, ruff, and a few other tools:

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

The `-e` makes it an editable install (so if you ever tweak the source
you don't need to reinstall). The `[dev]` extra pulls in the test and
lint tools.

---

## Step 4 — Install the SkyBrain SDK

Go to the [Releases page](https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/releases),
download the latest `skybrain_eeg_sdk-X.Y.Z-py3-none-any.whl`, and
install it:

```powershell
# Replace 1.5.0 with whatever version you downloaded
pip install C:\path\to\skybrain_eeg_sdk-1.5.0-py3-none-any.whl
```

Verify it worked:

```powershell
python -c "import skybrain_sdk; print('SDK', skybrain_sdk.__version__, 'OK')"
```

You should see `SDK 1.5.0 OK` (or your version number).

> **Permission denied / can't find the wheel?** Make sure you're in
> the activated venv (your prompt shows `(.venv)`) and that the path
> to the wheel is right. On Windows, use forward slashes or
> double-backslashes in the path.

---

## Step 5 — Start the service

```powershell
python -m service.main
```

You should see:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

Leave this terminal open. The service is now running.

---

## Step 6 — Hit your first endpoint

Open a **second** terminal (keep the service running in the first
one). Activate the venv again in this new terminal:

```powershell
cd D:\projects\SkyBrain-QVAC
.\.venv\Scripts\Activate.ps1
```

### 6a. Check it's alive

```powershell
curl http://127.0.0.1:8765/v1/health
```

Expected:

```json
{"status":"ok","service":"skybrain-qvac-bci","service_version":"0.1.0","sdk_version":"1.5.0","uptime_seconds":12.5}
```

If you see this — congratulations, the bridge is working.

### 6b. See what the service can do

```powershell
curl http://127.0.0.1:8765/v1/capabilities
```

You'll get back a JSON listing of the seven BCI paradigms, five
Bayesian classifiers, and five biomarker bundle names. This is the
"menu" of everything the SDK exposes.

### 6c. (Optional) View interactive API docs

In your browser, open `http://127.0.0.1:8765/docs`. FastAPI builds a
Swagger UI automatically — you can click "Try it out" on any endpoint
and call it from the browser.

---

## Step 7 — Analyse a recording

You need an `.edf` file. Two options:

### Option A: Use the SDK's synthetic generator (recommended for first try)

The SDK ships with a CLI that generates realistic test recordings:

```powershell
mkdir samples 2>$null
skybrain-generate-edf --output samples\demo --duration 30 --channels 4 `
                       --pre-duration 10 --post-duration 10
```

This produces `samples\demo.edf` — a 30-second 4-channel synthetic EEG
recording with known pre/post differences baked in.

### Option B: Use a real recording

Any `.edf`, `.edf+`, `.bdf`, or `.csv` file from your existing BCI
hardware works. Note the absolute path.

### Now compute biomarkers

```powershell
curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers `
  -H "Content-Type: application/json" `
  -d '{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"spectral\"}'
```

> **Tip — Windows path quoting.** PowerShell needs backslashes
> escaped inside JSON: `\"samples/demo.edf\"`. On macOS / Linux, just
> use `'{"session_file":"samples/demo.edf","biomarker_set":"spectral"}'`
> with single quotes.

You'll get a JSON response like:

```json
{
  "modality": "eeg",
  "biomarker_set": "spectral",
  "profile": "skybrain_4ch",
  "kind": "features",
  "payload": {
    "channel_features": { "O1": { ... }, "O2": { ... }, ... },
    "global_features": { ... },
    "windows": [ ... ],
    "computation_params": { ... }
  },
  "request_id": "a5488520-...",
  "input_sha256": "a5ff6f4a8170...",
  "latency_ms": 125.3,
  "warnings": []
}
```

**What you're looking at:**
- `modality` — always `"eeg"` in Phase 1.
- `biomarker_set` — echoes what you asked for.
- `kind` — which family of SDK output this is (`features`, `qc`,
  `analysis`, or `cognitive_scores`).
- `payload` — the actual biomarker numbers. The exact structure depends
  on `biomarker_set` (see the table below).
- `request_id` — unique ID for this call. Appears in the audit log.
- `input_sha256` — fingerprint of the input file. Same file ⇒ same hash.
- `latency_ms` — how long the SDK took.
- `warnings` — empty unless something needs your attention.

---

## Step 8 — Try the other biomarker sets

Same endpoint, different `biomarker_set` value. Each one runs a
different SDK function under the hood:

| `biomarker_set` | What it returns | Typical latency on a 30s × 4ch recording |
|---|---|---|
| `spectral` | Delta/theta/alpha/beta/gamma band powers per channel; global features; per-window time series. | ~125 ms (warm) |
| `qc` | Pass/fail score, bad-channel list, signal-quality issues. | ~6 ms |
| `cognitive` | Composite scores: meditation, cognitive load, drowsiness, focus. | ~50–100 ms |
| `advanced` | Full analysis with FOOOF aperiodic parameters, nonlinear measures, connectivity. | ~140 ms |
| `full` | Everything `advanced` includes, plus the QC report and metadata. | ~140 ms |

Run all five against the same recording to see how they differ:

```powershell
foreach ($set in @("spectral", "qc", "cognitive", "advanced", "full")) {
    Write-Host "`n=== biomarker_set=$set ===" -ForegroundColor Cyan
    curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers `
      -H "Content-Type: application/json" `
      -d "{\""session_file\"":\""samples/demo.edf\"",\""biomarker_set\"":\""$set\""}" `
      | python -m json.tool
}
```

---

## Step 9 — Inspect the audit log

Every inference writes a single line to a daily JSON Lines file at
`audit/YYYY-MM-DD.jsonl`. Take a look:

```powershell
Get-Content audit\*.jsonl | Select-Object -Last 5
```

You'll see something like:

```json
{"endpoint":"POST /v1/eeg/biomarkers","extra":{"biomarker_set":"spectral","kind":"features","profile":"skybrain_4ch"},"input_sha256":"a5ff6f4a...","latency_ms":125.3,"modality":"eeg","request_id":"a5488520-...","timestamp":"2026-05-17T13:11:14.023+00:00"}
```

This is your **CDSCO-compliance audit trail**. Every call, hashed,
timestamped, ordered. If you want to change the location, set the
`SKYBRAIN_QVAC_AUDIT_DIR` environment variable before starting the
service.

---

## Step 10 — Stop the service

In the terminal where the service is running, press `Ctrl + C`. You
should see `INFO: Application shutdown complete.`

---

## Endpoints that aren't live yet

Three of the six endpoints are scaffolded but return `HTTP 501`. They
exist so client integration can begin against the live contracts.
Calling them returns a structured envelope explaining what they're
blocked on:

| Endpoint | What it will do | Status |
|---|---|---|
| `POST /v1/bci/classify` | Run BCI classifier inference (P300, motor imagery, etc.) | Phase 1 wk 5-6 |
| `POST /v1/eeg/ingest` | Stream realtime EEG from hardware or file replay | Phase 1 wk 9-10 |
| `POST /v1/eeg/compare` | Two-recording statistical comparison (pre/post studies) | Phase 1 wk 11-12 |

Try one:

```powershell
curl -X POST http://127.0.0.1:8765/v1/bci/classify `
  -H "Content-Type: application/json" -d '{}'
```

You'll get a 501 with a clear message pointing at the milestone that
unblocks it.

---

## Troubleshooting

**Q. The service starts but every biomarker call returns
`{"error": {"code": "sdk_error", ...}}`.**
A. The SDK wheel didn't install correctly. Verify with
`python -c "import skybrain_sdk; print(skybrain_sdk.__version__)"`.
If it errors, re-run `pip install` on the wheel from step 4.

**Q. Port 8765 is already in use.**
A. Either stop whatever's using it, or run the service on a different
port: `$env:SKYBRAIN_QVAC_PORT=9000; python -m service.main`.

**Q. `curl` isn't recognised.**
A. On older Windows installs, `curl` is missing. Use
`Invoke-RestMethod` instead:
```powershell
Invoke-RestMethod http://127.0.0.1:8765/v1/health
```

**Q. The biomarker call returns `recording_not_found` even though the
file exists.**
A. The bridge resolves the path on the *server* side, not the client
side — i.e. relative paths are relative to where the service was
started, not where curl was run. Use absolute paths to be safe.

**Q. I want to skip the SDK install and just look around.**
A. Set `$env:SKYBRAIN_QVAC_REQUIRE_SDK="false"` before starting the
service. It'll boot, `/v1/health` and `/v1/capabilities` will work,
but biomarker calls will fail with a friendly message.

**Q. How do I run the tests?**
A. With the SDK installed: `pytest`. You should see `13 passed`.

---

## What to read next

- **[QVAC API reference](qvac-api-reference.md)** — the QVAC SDK + HTTP
  server surface this service is designed to plug into. Read this if
  you're writing a QVAC plugin or a JS/TS client.
- **[Plugin manifest design](../plugin-manifest/README.md)** — how the
  Phase 2 npm bridge plugin (`@skybrain/qvac-bci-addon`) will wrap
  this service for native QVAC consumers.
- **[Technical brief](02_QVAC_Technical_Brief.md)** — the six-endpoint
  architecture, phase plan, and IP boundaries in full.
- **OpenAPI / Swagger UI** — `http://127.0.0.1:8765/docs` (while the
  service is running). Click "Try it out" on any endpoint.

---

## Questions or problems?

File an issue at
[github.com/SkyBrain-Neurotech/SkyBrain-QVAC/issues](https://github.com/SkyBrain-Neurotech/SkyBrain-QVAC/issues),
or reach out at info@skybrain.in.
