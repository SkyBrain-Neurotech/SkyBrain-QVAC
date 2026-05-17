# `plugin-manifest/` — design docs, not runtime config

> **Why is this a docs folder rather than a single `qvac-plugin.json` file?**
> Because QVAC plugins are **not JSON manifests**. They are TypeScript npm
> packages with two entry points (`./client` and `./plugin`), declared via
> `definePlugin()` + `defineHandler()`, invoked via `invokePlugin()` /
> `invokePluginStream()`. See [`docs/qvac-api-reference.md`](../docs/qvac-api-reference.md)
> §5 for the full breakdown extracted from `docs.qvac.tether.io`.

This folder ships three deliverables for the Phase 1 grant milestone:

| File | Purpose |
|---|---|
| `README.md` (this file) | Architecture for the Phase 2 bridge plugin, explaining the relationship between this Python service and the future npm package. |
| `capability-schema.json` | JSON Schema describing our `/v1/*` HTTP contract — drives TypeScript client codegen for the Phase 2 bridge. |
| `package.json.example` | Sample of the Phase 2 `@skybrain/qvac-bci-addon` package manifest in the exact shape QVAC requires. |

The actual TypeScript implementation of the bridge plugin is **Phase 2
scope**, not Phase 1. Phase 1 ships only the Python HTTP service plus
this design package so the QVAC team can sign off on the integration
shape during the Week 2 alignment call.

## The bridge plugin design

In Phase 2 we publish `@skybrain/qvac-bci-addon` to npm. A QVAC SDK
consumer installs it and registers it in `qvac.config.json`:

```jsonc
{
  "plugins": ["@skybrain/qvac-bci-addon/plugin"]
}
```

Then in application code:

```typescript
import { loadModel } from "@qvac/sdk";
import { computeBiomarkers } from "@skybrain/qvac-bci-addon";

await loadModel({ modelType: "skybrain-eeg", modelId: "default" });

const result = await computeBiomarkers({
  modelId: "default",
  session_file: "/tmp/sample.edf",
  biomarker_set: "spectral",
});
// result: { modality, biomarker_set, profile, kind, payload, ... }
```

### Two operating modes

The plugin's `./plugin` worker entry point exposes the same handler API
in both modes; the difference is what runs underneath.

**Mode A — Python service backend (Phase 1 + early Phase 2).**
The plugin's `handler` for `computeBiomarkers` does an HTTP `fetch()` to
`http://localhost:8765/v1/eeg/biomarkers`, gets the JSON response, and
returns it. The Python service does the actual SDK work. **This mode
exists today** (call our HTTP service directly with curl) and stays
useful for research and clinical setups where the full proprietary SDK
matters.

**Mode B — Native JS port (later Phase 2).**
The plugin's `handler` calls a native-JS reimplementation of the core
biomarker pipeline (band powers, IAF, peak frequency, Hjorth, sample
entropy, single Bayesian discriminant). No Python dependency. This is
the deliverable that lets QVAC consumers ship in Expo/Bare/iOS/Android.

The selection is config-driven (e.g. `backend: "python-service" | "native"`)
so the same npm package works in both deployments.

## Capability identifier

The QVAC `modelType` we claim is `skybrain-eeg`. Phase 2+ can add
sibling model types — `skybrain-ecg`, `skybrain-ppg`, `skybrain-multimodal`
— without changing the EEG one.

Handlers exposed by the plugin (one per HTTP endpoint, names mirror the
SDK function names so the mapping is obvious):

| Plugin handler | Underlying HTTP endpoint |
|---|---|
| `computeBiomarkers` | `POST /v1/eeg/biomarkers` |
| `classifyBCI` | `POST /v1/bci/classify` |
| `ingestStream` | `POST /v1/eeg/ingest` (streaming via `invokePluginStream`) |
| `compareSessions` | `POST /v1/eeg/compare` |
| `getCapabilities` | `GET /v1/capabilities` |

## Open items for Week 2 alignment call

Items to settle with the QVAC team before locking the Phase 2 npm
manifest shape:

1. Single `skybrain-eeg` modelType with handler-level capability split,
   or one modelType per endpoint? Trade-off is QVAC's `loadModel()`
   ergonomics vs. discovery granularity.
2. Streaming convention for `/v1/eeg/ingest` — `invokePluginStream()`
   (QVAC-idiomatic) or SSE through the HTTP server (OpenAI-idiomatic)?
3. Should the npm package self-bundle the Python service binary
   (PyInstaller) for one-command installs, or document `pip install`
   as a prerequisite?
4. Does QVAC's plugin lifecycle have an `onLoad`/`onUnload` hook for
   spawning/closing the sidecar Python process? The docs only list
   `createModel`.

These are the items the technical brief flagged for Week 2 (per §6.1).
