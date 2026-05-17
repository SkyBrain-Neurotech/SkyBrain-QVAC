# Sample outputs and demo recordings

Real recordings + real `/v1/*` responses captured from a live service so a
reviewer can inspect what the API actually returns *without installing
anything*. Run the bridge against the committed recordings to reproduce
identical numbers (the SDK is deterministic).

## Demo recordings (committed CSV)

| File | What it is | Channels | Duration | Sample rate |
|---|---|---|---|---|
| `eyes-open.csv` | Real EEG recording, eyes open | O1, O2, T3, T4 | ~60 s | 250 Hz |
| `eyes-closed.csv` | Real EEG recording, eyes closed (same subject) | O1, O2, T3, T4 | ~60 s | 250 Hz |

These are the canonical eyes-open vs eyes-closed pair for demonstrating
the Berger alpha effect (alpha power increase over occipital channels
when eyes close). Sharing EEG data is standard in the field — PhysioNet,
OpenNeuro, Kaggle, and BCI Competition datasets all host similar
recordings publicly.

Format is SDK-native CSV: `timestamp_unix` plus one column per channel.
Same loader that handles EDF / EDF+ / BDF.

## Sample API outputs

| File | Endpoint called | Notes |
|---|---|---|
| `compare-eyes-open-vs-closed-output.json` | `POST /v1/eeg/compare` on the two recordings above | **The marquee demo.** Auto-summary detects the Berger effect explicitly. 212 metrics extracted; top 15 differences sorted by %-change. Latency ~600 ms on a cold cache. |
| `biomarkers-spectral-summary-output.json` | `POST /v1/eeg/biomarkers` on `eyes-open.csv` with `view=summary` | Demo of the `view` parameter; `windows` time-series arrays dropped. |
| `biomarkers-spectral-output.json` | `POST /v1/eeg/biomarkers` with `view=detailed` (legacy capture, was the default) | Full per-window output for comparison. |
| `biomarkers-qc-output.json` | `POST /v1/eeg/biomarkers` with `biomarker_set=qc` | Quality-control report only. |
| `biomarkers-full-output.json` | `POST /v1/eeg/biomarkers` with `biomarker_set=full` | Complete `run_analysis` output (recording metadata, QC, features, summary, annotations). |

## What's in each

- **`compare-eyes-open-vs-closed-output.json`** — the response shape that
  matters for QVAC integration: a `metrics_extracted` catalogue (count +
  names of every numeric metric we touched), a `top_differences` table
  (15 entries, ranked by absolute percent change, each with metric name,
  channel, both values, delta, percent-change, and direction), and a
  one-line `summary` auto-generated from the data. Open the file in
  any JSON viewer and read the summary — that's the whole demo.
- **`spectral`** — per-channel band powers (delta/theta/alpha/beta/gamma),
  relative band powers, peak frequencies, total power, beta/alpha and
  theta/beta ratios, Hjorth parameters, sample entropy, permutation
  entropy. The `summary` view drops per-window time series; `detailed`
  keeps them.
- **`qc`** — pass/fail summary, channel-by-channel quality scores, issue
  list. The "is this recording usable?" check.
- **`full`** — `run_analysis` complete output: QC report, full feature
  set, segment metrics, recording metadata, profile hash, SDK version.

## Reproducing these locally

```bash
# 1. Install the bridge per ../USER_GUIDE.md steps 1-5
# 2. Boot the service
python -m service.main

# 3. Run the eyes-open vs eyes-closed compare (PowerShell):
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8765/v1/eeg/compare `
  -ContentType "application/json" `
  -Body '{"session_a_file":"docs/examples/eyes-open.csv","session_b_file":"docs/examples/eyes-closed.csv","label_a":"eyes_open","label_b":"eyes_closed"}' `
  | ConvertTo-Json -Depth 10
```

The SDK is deterministic — same input + same SDK version produces
bit-identical output. If your numbers don't match, something is wrong
with the install or SDK version.

## Known issue — `cognitive` biomarker set not captured

The `cognitive` bundle (`POST /v1/eeg/biomarkers` with
`biomarker_set: "cognitive"`) hits an `AttributeError: 'EegRecording'
object has no attribute 'get'` — the adapter currently passes the
`EegRecording` object to `skybrain_sdk.cognitive_metrics.compute_all_scores`
which expects a different argument type (probably a feature dict or
DataFrame). Adapter fix scheduled for Phase 1 week 5-6. The four working
bundles (spectral, qc, advanced, full) exercise the full SDK path.
