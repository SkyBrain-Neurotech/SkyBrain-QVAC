# QVAC SDK & HTTP API Reference (extracted for skybrain-qvac-bci)

> **Source:** docs.qvac.tether.io, fetched and condensed during the Phase 1 build planning session. Last fetched: 2026-05-17.
> **Authoritative URL when in doubt:** https://docs.qvac.tether.io
> **Purpose:** Local reference for building `skybrain-qvac-bci`. Quotes verbatim where they constrain implementation choices; paraphrases everything else.

---

## 1 · What QVAC is

QVAC is a JavaScript/TypeScript SDK (`@qvac/sdk`) for building local and P2P AI applications. It runs on:

- Node.js
- **Bare** runtime (https://bare.pears.com) — Pear/Holepunch's minimal JS runtime
- **Expo** (iOS / Android)

**Out-of-the-box capabilities** (built-in plugins, see §4):
text generation (LLM), embeddings, RAG, fine-tuning, multimodal, image generation, audio transcription (ASR), text-to-speech (TTS), voice assistant, translation (NMT), OCR.

**Two consumption surfaces:**

1. **Programmatic** — `import { ... } from "@qvac/sdk"` in JS/TS code.
2. **HTTP server** — `qvac serve openai` launches an OpenAI-compatible HTTP API for clients in any language. **This is the surface our Phase 1 Python service mimics.**

---

## 2 · QVAC's OpenAI-compatible HTTP API

> Default port: **11434** (Ollama-compatible). Our SkyBrain service uses **8765** per the technical brief — different port, no collision.

### Launch

```bash
npm install @qvac/sdk @qvac/cli
qvac serve openai [options]
```

Flags:
- `-p, --port <number>` (default `11434`)
- `-H, --host <address>` (default `127.0.0.1`)
- `--api-key <key>` — require `Authorization: Bearer <key>` header
- `--cors` — enable CORS
- `-c, --config <path>` — config file path

**Default bind is `127.0.0.1`** (local-only). CORS off by default.

### Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/models` | GET | List loaded models |
| `/v1/models/:id` | GET | Get model details |
| `/v1/models/:id` | DELETE | Unload a model |
| `/v1/chat/completions` | POST | Chat completions (blocking + SSE streaming) |
| `/v1/embeddings` | POST | Text embeddings |
| `/v1/audio/transcriptions` | POST | Audio transcription |

### `/v1/models` response shape

```json
{
  "object": "list",
  "data": [
    { "id": "my-llm", "object": "model", "created": 1718000000, "owned_by": "qvac" }
  ]
}
```

Model registration is **static via config** under `serve.models` in `qvac.config.*` — no runtime registration endpoint.

### `model` field semantics

- **Required.** Requests omitting it return `400`.
- **Valid values:** model aliases declared in `qvac.config.*` under `serve.models`.
- **Routing:** the server matches the alias to determine which capability (LLM, embeddings, transcription) to invoke.
- The `"default": true` flag in `serve.models[*]` does NOT act as a fallback — clients must explicitly specify `model`.

### Streaming

Server-Sent Events (SSE) — set `"stream": true` in the request body. (The docs example shows the flag; the exact `data:`-prefixed event format and `[DONE]` terminator are inherited from the OpenAI spec but not re-specified on the QVAC page.)

### Authentication

- **Default:** unauthenticated (only safe because default bind is loopback).
- **With key:** `qvac serve openai --api-key my-secret-token` requires `Authorization: Bearer my-secret-token`.
- Invalid token → `401`.

### Example curl invocations

```bash
# List models
curl http://localhost:11434/v1/models

# Chat (blocking)
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "my-llm", "messages": [{"role": "user", "content": "Hello!"}]}'

# Embeddings (batch)
curl http://localhost:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "my-embed", "input": ["First sentence", "Second sentence"]}'

# Transcription (multipart)
curl http://localhost:11434/v1/audio/transcriptions \
  -F "file=@audio.wav" -F "model=whisper" -F "response_format=json"
```

### Error response shape

**Not documented on the QVAC HTTP server page.** Our service should adopt OpenAI's convention as the closest precedent:

```json
{
  "error": {
    "code": "license_required",
    "type": "invalid_request_error",
    "message": "SkyBrain SDK license tier 'commercial' required.",
    "param": null
  }
}
```

QVAC's SDK uses numeric codes in the 50001–54000 range (client errors 50001–52000, server errors 52001–54000) — examples: `MODEL_NOT_FOUND` (52002), `TRANSCRIPTION_FAILED` (52403), `LIFECYCLE_OPERATION_BLOCKED` (53602). These belong to the SDK's `QvacErrorBase`, not the HTTP layer.

---

## 3 · `qvac.config.*` — the SDK configuration file

Filenames (any of):
- `qvac.config.json`
- `qvac.config.js`
- `qvac.config.ts`

Location: project root, or via `QVAC_CONFIG_PATH` env var. **Optional for SDK-only usage; required for the HTTP server.**

### Top-level keys

- `plugins: string[]` — which plugins to load (omit/empty = all built-ins)
- `loggerConsoleOutput`, `loggerLevel`
- `swarmRelays` — P2P relay public keys
- `cacheDirectory` — model cache path
- `httpDownloadConcurrency`, `httpConnectionTimeoutMs`
- `registryDownloadMaxRetries`, `registryStreamTimeoutMs`
- `deviceDefaults` — per-device hardware config overrides
- `serve.models` — HTTP server model registration map

### `serve.models` entry shape

```jsonc
{
  "serve": {
    "models": {
      "my-llm": {
        "model": "<SDK constant or descriptor>",     // e.g. "QWEN3_600M_INST_Q4"
        "src": "<source>",                            // local path, https URL, or pear://
        "type": "<llm|embedding|asr|tts|nmt|ocr|generation|custom>",
        "default": false,
        "preload": true,
        "config": { /* model-specific options */ }
      }
    }
  }
}
```

---

## 4 · Built-in plugins (8 ship with QVAC)

| Import path | Capability |
|---|---|
| `@qvac/sdk/llamacpp-completion/plugin` | LLM completion (llama.cpp fork) |
| `@qvac/sdk/llamacpp-embedding/plugin` | Text embeddings |
| `@qvac/sdk/whispercpp-transcription/plugin` | ASR (Whisper.cpp) |
| `@qvac/sdk/parakeet-transcription/plugin` | ASR (Parakeet, alternative) |
| `@qvac/sdk/nmtcpp-translation/plugin` | Neural machine translation |
| `@qvac/sdk/onnx-tts/plugin` | Text-to-speech (ONNX) |
| `@qvac/sdk/onnx-ocr/plugin` | OCR (ONNX) |
| `@qvac/sdk/sdcpp-generation/plugin` | Image generation (SD/SDXL/FLUX via sd.cpp) |

If `plugins` in config is omitted or empty, all built-ins are bundled. If set, **only** the listed plugins are bundled.

---

## 5 · How a "plugin" is structured (THE KEY FINDING)

> **QVAC plugins are not JSON manifests.** A plugin is a TypeScript/JavaScript npm package with two entry points — a client wrapper and a worker-side plugin definition. This shapes our `qvac-plugin.json` decision entirely (see §7).

### Directory layout

```
my-plugin/
├── package.json
├── src/
│   ├── client/
│   │   └── index.ts
│   └── plugin/
│       └── index.ts
└── dist/
    ├── client/
    │   └── index.js
    └── plugin/
        └── index.js
```

### `package.json` (the manifest — there is no separate `qvac-plugin.json`)

```json
{
  "name": "qvac-echo-plugin",
  "exports": {
    ".": {
      "types": "./dist/client.d.ts",
      "import": "./dist/client.js"
    },
    "./plugin": {
      "types": "./dist/plugin.d.ts",
      "import": "./dist/plugin.js"
    }
  }
}
```

- Root `.` export: client-facing wrappers. Must be **Metro-safe** (so it works in Expo/React Native).
- `./plugin` export: worker-side plugin definition. **Bare-only**.

### Plugin definition (worker-side, `src/plugin/index.ts`)

```typescript
import { z } from "zod";
import { definePlugin, defineHandler } from "@qvac/sdk/plugin-utils";
import type { CreateModelParams, PluginModelResult } from "@qvac/sdk";

export const echoPlugin = definePlugin({
  modelType: "echo",                              // capability identifier
  displayName: "Echo Plugin",
  addonPackage: "none",
  loadConfigSchema: z.object().catchall(z.unknown()),

  createModel: (params: CreateModelParams): PluginModelResult => {
    const model = { id: params.modelId, load: async () => {} };
    return { model };
  },

  handlers: {
    echo: defineHandler({
      requestSchema: z.object({ message: z.string() }),
      responseSchema: z.object({ echoed: z.string(), timestamp: z.number() }),
      handler: async (request) => ({
        echoed: `Echo: ${request.message}`,
        timestamp: Date.now(),
      }),
    }),
  },
});
```

### Client wrapper (`src/client/index.ts`)

```typescript
import { invokePlugin, invokePluginStream } from "@qvac/sdk";

export async function echo(options: { modelId: string; message: string }) {
  return invokePlugin<{ echoed: string; timestamp: number }>({
    modelId: options.modelId,
    handler: "echo",
    params: options,
  });
}

export async function* echoStream(options: { modelId: string; message: string }) {
  for await (const chunk of invokePluginStream<{ char: string | null; done: boolean }>({
    modelId: options.modelId,
    handler: "echoStream",
    params: options,
  })) {
    if (!chunk.done && chunk.char) yield chunk.char;
  }
}
```

### Loading a custom plugin

```jsonc
// qvac.config.json
{
  "plugins": ["qvac-echo-plugin/plugin"]
}
```

Then consumer code:

```typescript
import { loadModel } from "@qvac/sdk";
import { echo } from "qvac-echo-plugin";

await loadModel({ modelType: "echo", modelId: "my-echo" });
const result = await echo({ modelId: "my-echo", message: "hi" });
```

**Lifecycle hooks documented:** only `createModel`. No `onLoad`/`onUnload`/`onRequest` hooks are listed.

**Custom HTTP endpoints:** *not* a documented capability of plugins. A plugin is invoked via `invokePlugin()` / `invokePluginStream()` from the SDK, not via a fresh path under `/v1/`. To expose a capability over HTTP, the model must be registered in `serve.models` — but the QVAC HTTP server only exposes the OpenAI endpoint set, not arbitrary plugin handlers.

---

## 6 · Relevant SDK functions for our bridge

From the SDK API reference (`/reference/api/`):

- **`loadModel(params)`** — loads LLM, embedding, ASR, TTS, NMT, OCR, diffusion, or custom plugin models from local paths, HTTP(S) URLs, or Hyperdrive (`pear://`).
- **`unloadModel(params)`** — unloads, auto-closes RPC when last model unloads.
- **`invokePlugin<T>(params)`** — non-streaming custom plugin call. Params: `{ modelId, handler, params }`.
- **`invokePluginStream<T>(params)`** — streaming variant; returns an `AsyncIterable<T>`.
- **`startQVACProvider() / stopQVACProvider()`** — P2P provider lifecycle (relevant for Phase 2's "delegated EEG inference across peers" exploration).
- **`heartbeat()`** — test delegate or local worker responsiveness.

### Streaming patterns the SDK uses

```
completion(...) → CompletionRun {
  events: AsyncIterable<CompletionEvent>    // { type: "contentDelta" | "toolCall" | ... }
  final: Promise<CompletionFinal>
}

transcribeStream(...) → AsyncGenerator<string | TranscribeSegment>

textToSpeech(...) → TextToSpeechStreamResult {
  buffer: Promise<number[]>
  bufferStream: AsyncGenerator<number>
  chunkUpdates: AsyncGenerator<TtsSentenceChunkUpdate>
}
```

Our streaming endpoint (`/v1/eeg/ingest`) — when we build it — should emit either SSE (to match QVAC's HTTP layer) or expose `invokePluginStream`-compatible chunks via the eventual JS bridge.

---

## 7 · What this means for `skybrain-qvac-bci` Phase 1

The technical brief assumed `plugin-manifest/qvac-plugin.json` could declare our service to QVAC. **The QVAC docs show this is not how it works.** Reconciling:

| Phase 1 deliverable (per technical brief §2) | What it actually maps to in QVAC |
|---|---|
| `qvac-plugin.json` manifest | There is no JSON manifest. The manifest is `package.json` of an npm package. Phase 1 ships a **design doc** (`plugin-manifest/README.md`) describing the future Phase 2 npm package; the JSON manifest gets renamed to a YAML/JSON **capability descriptor** that the Phase 2 bridge plugin will consume. |
| HTTP service discoverable by QVAC | QVAC doesn't auto-discover external HTTP services. Discovery happens through the JS bridge plugin (Phase 2) that internally `fetch()`es `http://localhost:8765`. Phase 1 consumers call our HTTP API directly via curl / any HTTP client. |
| `qvac serve openai` integration | Not in scope. Our service is its own OpenAI-style server on port 8765. QVAC's own server is independent on port 11434. |

### Phase 1 plugin-manifest deliverable

Instead of a fictional `qvac-plugin.json`:

- `plugin-manifest/README.md` — describes the bridge plugin's architecture, namespace, and `package.json` (the actual QVAC plugin manifest format).
- `plugin-manifest/capability-schema.json` — JSON Schema of our HTTP API contract, suitable for code-generating TypeScript client wrappers for the Phase 2 bridge plugin.
- `plugin-manifest/package.json.example` — sample of the Phase 2 npm package's `package.json` with the `exports` map QVAC expects.

The Week 2 alignment call with the QVAC team is where this reconciliation lands officially. Until then, this is our best read of public docs.

### The Phase 2 bridge plugin (informational)

When Phase 2 begins, the npm package will look like:

```
@skybrain/qvac-bci-addon/
├── package.json                     ← QVAC plugin manifest
├── src/
│   ├── client/index.ts              ← computeBiomarkers(), classifyBCI(), etc. → invokePlugin()
│   └── plugin/index.ts              ← definePlugin({ modelType: "skybrain-eeg", ... })
│       └── handlers: fetch() to http://localhost:8765 in Phase 1 mode,
│                     pure JS implementation in Phase 2 mode (eliminates Python dependency)
└── dist/
```

`modelType` candidates: `skybrain-eeg-biomarkers`, `skybrain-eeg-classify`, etc., or a single `skybrain-eeg` with handler-level capability discrimination. To be decided in the Week 2 call.

---

## 8 · What is NOT documented on docs.qvac.tether.io (gaps for the Week 2 call)

- Exact SSE wire format (data: prefix, `[DONE]` terminator) for QVAC's streaming HTTP endpoints — implied to follow OpenAI but not confirmed
- Plugin manifest version field / compatibility range
- Recommended pattern for plugins that wrap external HTTP services
- Whether `loadModel({ modelType: "..." })` supports lazy/remote loading where the model lives in a sibling process
- Discovery for external services (no Bonjour/mDNS doc, no service registry)
- Detailed error envelope at the HTTP layer (numbered codes are SDK-internal)

These are the open questions to bring to the Week 2 alignment call (per Phase 1 milestone schedule, technical brief §6.1).
