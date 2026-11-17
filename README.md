# sommebeer 🍺

> ⚠️ **Alcohol notice**: alcohol consumption is **discouraged**; in particular
> during pregnancy, breastfeeding, while on medication and when driving. This
> project is intended exclusively for **adults** (18+ / legal drinking age
> depending on jurisdiction) and aims to be an informative, responsible
> recommendation tool. Drink in moderation and safely; when in doubt, consult
> a healthcare professional.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/agent-LangGraph-1C3C3C?logo=langchain&logoColor=white)
![LangChain](https://img.shields.io/badge/LLM-LangChain-1C3C3C)
![Pydantic](https://img.shields.io/badge/config-Pydantic-e92063?logo=pydantic&logoColor=white)
![Weaviate](https://img.shields.io/badge/vector_DB-Weaviate-0B6BAC?logo=weaviate&logoColor=white)
![BM25](https://img.shields.io/badge/search-BM25%20%2B%20near_vector-8E44AD)
![Phoenix](https://img.shields.io/badge/observability-Arize_Phoenix-FF5C38?logo=arize&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/tracing-OpenTelemetry-4256F4?logo=opentelemetry&logoColor=white)
![llama.cpp](https://img.shields.io/badge/local_LLM-llama.cpp-6E4B9E?logo=llamadotcpp&logoColor=white)
![Qwen3](https://img.shields.io/badge/local_model-Qwen3--4B-615CEB)
![DeepInfra](https://img.shields.io/badge/LLM_provider-DeepInfra-0080FF)
![Vertex AI](https://img.shields.io/badge/LLM_provider-GCP_Vertex_AI-4285F4?logo=googlecloud&logoColor=white)
![OpenAI-compatible](https://img.shields.io/badge/API-OpenAI--compatible-412991?logo=openai&logoColor=white)
![Git submodule](https://img.shields.io/badge/data-beertor-F0DB4F?logo=gitbook&logoColor=black)

A kind and helpful beer shop tender agent. Answers "recommend me an IPA" or
"something like Flower Power" using a Weaviate vector database of 3,197 beers,
with pluggable LLMs and Phoenix tracing.

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

## Tags

`python` `langgraph` `langchain` `pydantic` `pydantic-settings` `weaviate`
`vector-database` `bm25` `near-vector-search` `rag` `llm-agent` `llama-cpp`
`qwen3` `openai-compatible-api` `deepinfra` `google-cloud` `vertex-ai`
`arize-phoenix` `opentelemetry` `openinference` `beer`
