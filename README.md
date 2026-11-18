# sommebeer 🍺

> ⚠️ **Alcohol notice**: alcohol consumption is **discouraged**; in particular
> during pregnancy, breastfeeding, while on medication and when driving. This
> project is intended exclusively for **adults** (18+ / legal drinking age
> depending on jurisdiction) and aims to be an informative, responsible
> recommendation tool. Drink in moderation and safely; when in doubt, consult
> a healthcare professional.

[![tests](https://github.com/Edorka/sommebeer/actions/workflows/tests.yml/badge.svg)](https://github.com/Edorka/sommebeer/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/HTTP-FastAPI-009688?logo=fastapi&logoColor=white)
![Lit](https://img.shields.io/badge/UI-Lit-324FFF?logo=lit&logoColor=white)
![Git submodule](https://img.shields.io/badge/data-beertor-F0DB4F?logo=gitbook&logoColor=black)

![LangGraph](https://img.shields.io/badge/agent-LangGraph-1C3C3C?logo=langchain&logoColor=white)
![LangChain](https://img.shields.io/badge/LLM-LangChain-1C3C3C)
![Pydantic](https://img.shields.io/badge/config-Pydantic-e92063?logo=pydantic&logoColor=white)
![OpenAI-compatible](https://img.shields.io/badge/API-OpenAI--compatible-412991?logo=openai&logoColor=white)

![Weaviate](https://img.shields.io/badge/vector_DB-Weaviate-0B6BAC?logo=weaviate&logoColor=white)
![BM25](https://img.shields.io/badge/search-BM25%20%2B%20near_vector-8E44AD)

![Phoenix](https://img.shields.io/badge/observability-Arize_Phoenix-FF5C38?logo=arize&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/tracing-OpenTelemetry-4256F4?logo=opentelemetry&logoColor=white)

![llama.cpp](https://img.shields.io/badge/local_LLM-llama.cpp-6E4B9E?logo=llamadotcpp&logoColor=white)
![Qwen3](https://img.shields.io/badge/local_model-Qwen3--4B-615CEB)
![DeepInfra](https://img.shields.io/badge/LLM_provider-DeepInfra-0080FF)
![Vertex AI](https://img.shields.io/badge/LLM_provider-GCP_Vertex_AI-4285F4?logo=googlecloud&logoColor=white)

A kind and helpful beer shop tender agent. Answers "recommend me an IPA" or
"something like Flower Power" using a Weaviate vector database of 3,197 beers —
through a CLI, an HTTP API and a small Lit web UI — with pluggable LLMs and
Phoenix tracing.

> **Data source**: [beertor](./beertor) (git submodule) — the SQLite beer.db +
> Weaviate vector store that powers the beer knowledge. Clone with
> `git clone --recurse-submodules`.


## Architecture

```
question → router (LLM intent classification, Pydantic-validated)
   ├─ by_style    → BM25 over style fields
   ├─ by_likeness → near_vector with the reference beer's own taste-profile vector
   └─ general     → no retrieval
→ generate: grounded system prompt ("recommend ONLY from stock") → answer
                                              everything traced in Phoenix
```

- **Orchestration**: LangGraph (`sommebeer/graph.py`), Pydantic-typed state
- **Config**: pydantic-settings — one `.env`, validated at startup
  (`SOMMEBEER_LLM__*`, `SOMMEBEER_WEAVIATE__*`, `SOMMEBEER_PHOENIX__*`)
- **LLMs**: `local` (llama-server/Ollama, OpenAI-compatible) · `deepinfra` ·
  `gcp` (Vertex AI)
- **Retrieval**: Weaviate (`Beer` collection), 11-dim taste-profile vectors (taste-alike similarity)
- **Tracing**: Arize Phoenix (OTel + OpenInference LangChain instrumentation)

## Layout

```
sommebeer/          # core agent package (graph, retriever, llm, config, tracing)
cli/agent.py        # CLI deliverable — thin wiring only
backend/            # HTTP deliverable — FastAPI + its own requirements
frontend/           # UI — Lit web components, served by Vite
tools/              # one-off ops scripts (vector backfill)
tests/              # one suite for core + backend
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r backend/requirements.txt
cp .env.example .env            # adjust provider/endpoints if needed
.venv/bin/python -m tools.backfill_vectors   # one-time: taste-profile vectors
```

## Run

```bash
phoenix serve --port 6006       # optional: tracing UI (default endpoint)

# CLI
.venv/bin/python -m cli.agent                     # interactive chat
.venv/bin/python -m cli.agent -q "recommend me an IPA"

# HTTP API (docs at http://localhost:8000/docs)
.venv/bin/uvicorn backend.main:app --reload
curl -s localhost:8000/chat -H 'Content-Type: application/json' \
     -d '{"question": "something similar to Flower Power"}'

# Web UI — http://localhost:5173 (Vite proxies /chat + /health to the API)
cd frontend && npm install && npm run dev
```

## Switching LLM provider

In `.env`:

```ini
# local
SOMMEBEER_LLM__PROVIDER=local
# deepinfra
SOMMEBEER_LLM__PROVIDER=deepinfra
SOMMEBEER_LLM__DI_MODEL=Qwen/Qwen2.5-72B-Instruct
SOMMEBEER_LLM__DI_API_KEY=...
# gcp
SOMMEBEER_LLM__PROVIDER=gcp
SOMMEBEER_LLM__GCP_PROJECT=my-project
```

## Tests

```bash
.venv/bin/python -m pytest tests/    # 35 unit tests, no services needed
```

Integration tests (live Weaviate queries + a full agent roundtrip) run
automatically when the stack is up, and auto-skip otherwise.

## Tags

**agents / RAG**: `langgraph` `langchain` `llm-agent` `rag` `near-vector-search` `bm25`

**python stack**: `python` `fastapi` `pydantic` `pydantic-settings` `weaviate` `vector-database`
`llama-cpp` `qwen3` `deepinfra` `google-cloud` `vertex-ai` `openai-compatible-api`

**observability**: `arize-phoenix` `opentelemetry` `openinference`

**frontend**: `lit` `web-components` `vite` `shadow-dom` `javascript`

**domain**: `beer`
