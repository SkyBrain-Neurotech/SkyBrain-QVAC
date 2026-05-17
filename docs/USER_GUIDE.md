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

## Step 4 — The SkyBrain SDK (only if you have access)

The bridge wraps SkyBrain Neurotech's **proprietary EEG/BCI SDK** —
the engine that powers SkyBrain's commercial product line (Studio,
Analyze, Enterprise API, Cognitive Edge). The SDK is not currently
distributed for general developer use. It's gated to:

1. SkyBrain's own commercial products, and
2. The Tether grants team for the duration of the QVAC grant review,
   so reviewers can run this bridge end-to-end against the real engine.

### If you have SDK access

You'll have been added as a Read collaborator to
`SkyBrain-Neurotech/sdk-release`. **Accept the invite first** — check
your GitHub notifications inbox or the email GitHub sent you. The
clone in the next step will fail with `Repository not found` if you
haven't accepted yet.

```powershell
# Clone the private SDK repo as a SIBLING of this bridge repo.
# (you should be standing inside the SkyBrain-QVAC folder when running these;
#  if your prompt shows `(.venv)`, you're in the right venv)
git clone https://github.com/SkyBrain-Neurotech/sdk-release.git ..\sdk-release

# Install the wheel into THIS bridge's venv
pip install ..\sdk-release\wheels\skybrain_eeg_sdk-1.5.0-py3-none-any.whl
```

#### If `git clone` prompts you for credentials

On a fresh machine, GitHub will ask you to authenticate before letting
you clone a private repo. Three ways this typically resolves:

1. **Browser-based auth (default on Windows 10/11 and macOS).** Git
   Credential Manager opens a browser window automatically. Log into
   github.com with the account you were invited under. Credentials get
   cached locally for ~30 days; subsequent clones just work.
2. **SSH key.** If you have an SSH key registered with your GitHub
   account, use the SSH URL instead:
   ```powershell
   git clone git@github.com:SkyBrain-Neurotech/sdk-release.git ..\sdk-release
   ```
3. **Personal Access Token (PAT).** On Linux/CI machines without a
   browser, create a PAT at
   [github.com/settings/tokens](https://github.com/settings/tokens)
   with the `repo` scope (Read access is enough for clones). When git
   prompts for a password, paste the token instead of your GitHub
   password.

If you see `Repository not found` instead of an auth prompt: it means
either (a) you haven't accepted the collaborator invite yet, or (b) you're
authenticated as the wrong GitHub account. Check your account at
[github.com](https://github.com) (top-right avatar) and re-accept the
invite if needed.

After this, your folder structure looks like:

```
D:\Workspace\May\
├── SkyBrain-QVAC\          ← this bridge repo (open-source)
│   ├── service\
│   ├── docs\
│   └── ...
└── sdk-release\            ← the private SDK repo (Read-collaborator-only)
    └── wheels\skybrain_eeg_sdk-1.5.0-py3-none-any.whl
```

Keeping them as siblings (rather than nesting `sdk-release` inside the
bridge repo) avoids any accidental commits of the proprietary wheel
into the public bridge repo.

Verify:

```powershell
python -c "import skybrain_sdk; print('SDK', skybrain_sdk.__version__, 'OK')"
```

You should see `SDK 1.5.0 OK`.

If your grant scope includes advanced features beyond the default
bridge surface, your API key is in your party's grant folder
(`sdk-release/grants/<your-party-name>/README.md`). Apply it once at
the top of any Python script:

```python
from skybrain_sdk import set_api_key
set_api_key("<the key string from your grant README>")
```

The default bridge endpoints (`spectral`, `qc`, `advanced`, `full`
biomarker bundles, plus health + capabilities) need no key.

### If you don't have SDK access

You can still run the bridge in **docs-only mode** to inspect the API
surface, browse the OpenAPI / Swagger UI, and design a QVAC client
against the contract. Set this env var before starting the service:

```powershell
$env:SKYBRAIN_QVAC_REQUIRE_SDK = "false"
python -m service.main
```

What works in docs-only mode:

- `GET /v1/health` — reports `sdk_version: "unavailable"` but returns 200
- `GET /v1/capabilities` — full static catalogue of paradigms, classifiers, bundles
- `http://127.0.0.1:8765/docs` — full OpenAPI / Swagger UI
- All endpoints return correctly-shaped JSON envelopes (live or error)

Inference endpoints fail with a clean `sdk_unavailable` error rather
than a stack trace.

For commercial / enterprise evaluation of SkyBrain (Studio, Analyze,
Enterprise API), that's a separate sales track. Contact
`info@skybrain.in` to discuss enterprise licensing — that conversation
happens outside this repo.

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

> **PowerShell users — important.** In PowerShell, the name `curl`
> is an alias for `Invoke-WebRequest`, which doesn't accept curl's
> `-H` / `-d` flags. Use **`Invoke-RestMethod`** (the PowerShell-native
> command, shown below) or **`curl.exe`** (the real binary that ships
> with Windows 10/11). Don't use the bare word `curl` in PowerShell.

### 6a. Check it's alive

```powershell
Invoke-RestMethod http://127.0.0.1:8765/v1/health
```

Expected output:

```
status          : ok
service         : skybrain-qvac-bci
service_version : 0.1.0
sdk_version     : 1.5.0
uptime_seconds  : 12.5
```

If you see this — congratulations, the bridge is working.

(On macOS / Linux / Git Bash, the equivalent is `curl http://127.0.0.1:8765/v1/health`.)

### 6b. See what the service can do

```powershell
Invoke-RestMethod http://127.0.0.1:8765/v1/capabilities
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
skybrain-generate-edf --output samples\demo --duration 30 --channels 4 --pre-duration 10 --post-duration 10
```

This produces `samples\demo.edf` — a 30-second 4-channel synthetic EEG
recording with known pre/post differences baked in.

### Option B: Use a real recording

Any `.edf`, `.edf+`, `.bdf`, or `.csv` file from your existing BCI
hardware works. Note the absolute path.

### Now compute biomarkers

Pick the form for your shell. All three are single-line, paste-friendly, and pipe through a formatter so the nested response is readable:

**Windows PowerShell** (recommended — handles JSON cleanly, `ConvertTo-Json -Depth 10` is needed because PowerShell otherwise truncates nested objects and shows them as `@{key=; ...}`):

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}' | ConvertTo-Json -Depth 10
```

**Windows cmd.exe** (escaped double quotes — cmd treats `'` as a literal character; pipe to `python -m json.tool` to pretty-print):

```cmd
curl -s -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"spectral\"}" | python -m json.tool
```

**macOS / Linux / Git Bash:**

```bash
curl -s -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}' | python -m json.tool
```

### Drilling into specific values (PowerShell only)

If you want to pull one biomarker out instead of seeing the whole tree:

```powershell
$r = Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}'
$r.payload.channel_features.Fp1                       # all biomarkers for the Fp1 channel
$r.payload.channel_features.Fp1.band_power_alpha      # just alpha band power on Fp1
$r.payload.global_features                            # cross-channel summary
$r.latency_ms                                         # how long the SDK took
```

> **Why three different commands?** PowerShell's `curl` is an alias for
> `Invoke-WebRequest` and rejects real curl's `-H` flag (it expects a
> dictionary, not a string). cmd.exe has real curl but doesn't honor
> single quotes — they're literal characters. Bash handles single
> quotes natively. If you want one command that works in both Windows
> shells, use `curl.exe` (forces the real binary) with cmd-style
> escaped double quotes — the cmd example above also works in
> PowerShell if you replace `curl` with `curl.exe`.

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

Run all five against the same recording to see how they differ.

**Windows PowerShell:**

```powershell
foreach ($set in @("spectral", "qc", "cognitive", "advanced", "full")) { Write-Host "`n=== biomarker_set=$set ===" -ForegroundColor Cyan; Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body "{`"session_file`":`"samples/demo.edf`",`"biomarker_set`":`"$set`"}" | ConvertTo-Json -Depth 10 }
```

**Windows cmd.exe:**

```cmd
for %S in (spectral qc cognitive advanced full) do @echo === biomarker_set=%S === && curl -s -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"%S\"}" | python -m json.tool
```

**macOS / Linux / Git Bash:**

```bash
for SET in spectral qc cognitive advanced full; do echo "=== biomarker_set=$SET ==="; curl -s -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"$SET\"}" | python -m json.tool; done
```

---

## Step 8.5 — The eyes-open vs eyes-closed demo (compare endpoint)

A much more compelling demo than dumping single-file biomarkers: send two recordings and get a curated differential. The repo ships with real eyes-open and eyes-closed EDFs under `docs/examples/` so you can run this immediately.

**Windows PowerShell:**

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/compare -ContentType "application/json" -Body '{"session_a_file":"docs/examples/eyes-open.csv","session_b_file":"docs/examples/eyes-closed.csv","label_a":"eyes_open","label_b":"eyes_closed"}' | ConvertTo-Json -Depth 10
```

**Windows cmd.exe:**

```cmd
curl -s -X POST http://127.0.0.1:8765/v1/eeg/compare -H "Content-Type: application/json" -d "{\"session_a_file\":\"docs/examples/eyes-open.csv\",\"session_b_file\":\"docs/examples/eyes-closed.csv\",\"label_a\":\"eyes_open\",\"label_b\":\"eyes_closed\"}" | python -m json.tool
```

**macOS / Linux / Git Bash:**

```bash
curl -s -X POST http://127.0.0.1:8765/v1/eeg/compare -H "Content-Type: application/json" -d '{"session_a_file":"docs/examples/eyes-open.csv","session_b_file":"docs/examples/eyes-closed.csv","label_a":"eyes_open","label_b":"eyes_closed"}' | python -m json.tool
```

You'll get back:

```jsonc
{
  "modality": "eeg",
  "condition_a": "eyes_open",
  "condition_b": "eyes_closed",
  "profile": "skybrain_4ch",
  "metrics_extracted": {
    "count": 156,                          // every numeric metric we computed
    "names": ["band_power_alpha", "band_power_beta", ... ]
  },
  "top_differences": [                     // top 15 by absolute %-change
    {
      "metric": "band_power_alpha",
      "channel": "O1",
      "value_a": 4.21,
      "value_b": 12.67,
      "delta": 8.46,
      "percent_change": 200.95,
      "direction": "increase_in_b"
    },
    // ... 14 more
  ],
  "summary": "Strong alpha-band power increase (201%) over occipital channel O1 in eyes_closed vs eyes_open — consistent with the classic Berger effect (posterior alpha rhythm modulation by visual input).",
  "request_id": "...",
  "input_sha256_a": "...",
  "input_sha256_b": "...",
  "latency_ms": 312.4
}
```

The Berger effect (alpha rhythm doubling over occipital channels when eyes close) has been the canonical "is this EEG real?" test since 1929. If the summary line shows it, the whole pipeline — adapter → SDK → biomarker computation — is working end-to-end against real signals.

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

Try one (use `-SkipHttpErrorCheck` in PowerShell 7+ to see the 501 body; or wrap in try/catch on Windows PowerShell 5):

**Windows PowerShell:**

```powershell
try { Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/bci/classify -ContentType "application/json" -Body '{}' } catch { $_.ErrorDetails.Message }
```

**macOS / Linux / Git Bash:**

```bash
curl -X POST http://127.0.0.1:8765/v1/bci/classify -H "Content-Type: application/json" -d '{}'
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

**Q. PowerShell says `Cannot bind parameter 'Headers'` when I use `curl -H`.**
A. In PowerShell, `curl` is an alias for `Invoke-WebRequest`, which
expects `-Headers` as a dictionary — it can't take `Content-Type: ...`
as a string. Three fixes:

1. Use `Invoke-RestMethod` (recommended, native, no quote-escaping):
   ```powershell
   Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}'
   ```
2. Use `curl.exe` (the real curl binary that ships with Windows 10/11),
   not the bare word `curl`:
   ```powershell
   curl.exe -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"spectral\"}"
   ```
3. Run the commands from Git Bash or WSL, where `curl` is real curl.

**Q. cmd.exe says my POST body parsed to `{}` even though I sent JSON.**
A. cmd.exe doesn't treat single quotes as grouping characters — they
become literal apostrophes inside the request body, mangling the JSON
before it even reaches curl. Always use **double quotes with backslash-escaped
inner quotes** in cmd:
```cmd
curl -X POST http://127.0.0.1:8765/v1/eeg/biomarkers -H "Content-Type: application/json" -d "{\"session_file\":\"samples/demo.edf\",\"biomarker_set\":\"spectral\"}"
```

**Q. PowerShell shows `payload : @{channel_features=; global_features=; windows=; computation_params=}` with empty values.**
A. The data is there — PowerShell's default display truncates nested
objects at depth 2 and renders them as `@{key=; ...}`. Pipe to
`ConvertTo-Json -Depth 10` to see the full structure, or access nested
properties directly:
```powershell
$r = Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/biomarkers -ContentType "application/json" -Body '{"session_file":"samples/demo.edf","biomarker_set":"spectral"}'
$r | ConvertTo-Json -Depth 10            # full pretty-printed tree
$r.payload.channel_features.Fp1          # one channel's biomarkers
$r.payload.global_features               # cross-channel summary
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
