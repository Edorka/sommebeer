# sombeer 🍺

A kind and helpful beer shop tender agent. Answers "recommend me an IPA" or
"something like Flower Power" using a Weaviate vector database of 3,197 beers,
with pluggable LLMs and Phoenix tracing.

## Architecture

```
question → router (LLM intent classification, Pydantic-validated)
   ├─ by_style    → BM25 over style fields
   ├─ by_likeness → near_vector with the reference beer's own taste-profile vector
   └─ general     → no retrieval
→ generate: grounded system prompt ("recommend ONLY from stock") → answer
                                              everything traced in Phoenix
```

- **Orchestration**: LangGraph (`sombeer/graph.py`), Pydantic-typed state
- **Config**: pydantic-settings — one `.env`, validated at startup
  (`SOMBEER_LLM__*`, `SOMBEER_WEAVIATE__*`, `SOMBEER_PHOENIX__*`)
- **LLMs**: `local` (llama-server/Ollama, OpenAI-compatible) · `deepinfra` ·
  `gcp` (Vertex AI)
- **Retrieval**: Weaviate (`Beer` collection), 11-dim taste-profile vectors (taste-alike similarity)
- **Tracing**: Arize Phoenix (OTel + OpenInference LangChain instrumentation)

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # adjust provider/endpoints if needed
.venv/bin/python backfill_vectors.py   # one-time: taste-profile vectors (skips already-vectorized)
```

## Run

```bash
phoenix serve --port 6006       # optional: tracing UI (default endpoint)
.venv/bin/python agent.py                    # interactive chat
.venv/bin/python agent.py -q "recommend me an IPA"
.venv/bin/python agent.py -q "something similar to Flower Power"
```

## Switching LLM provider

In `.env`:

```ini
# local
SOMBEER_LLM__PROVIDER=local
# deepinfra
SOMBEER_LLM__PROVIDER=deepinfra
SOMBEER_LLM__DI_MODEL=Qwen/Qwen2.5-72B-Instruct
SOMBEER_LLM__DI_API_KEY=...
# gcp
SOMBEER_LLM__PROVIDER=gcp
SOMBEER_LLM__GCP_PROJECT=my-project
```
