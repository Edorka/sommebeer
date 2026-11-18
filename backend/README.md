# backend — HTTP deliverable

FastAPI service exposing the beer tender. All logic lives in the core
package; this folder is thin wiring only.

```bash
# install (from repo root) and run
.venv/bin/pip install -r api/requirements.txt
.venv/bin/uvicorn backend.main:app --reload
```

Interactive docs (OpenAPI/Swagger): http://localhost:8000/docs

## curl examples

### Ask for a recommendation

```bash
curl -s localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question": "recommend me 2 IPAs"}'
```

```json
{"answer": "1. **Sculpin** (Ballast Point) – American IPA, 7.0% ABV …"}
```

The `answer` is **Markdown** — render it, don't escape it.

### Find beers similar to another beer

```bash
curl -s localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question": "I love Pliny The Elder, anything similar?"}'
```

### Health check

```bash
curl -s localhost:8000/health
```

```json
{"status": "ok", "weaviate": true, "llm": true}
```

`weaviate`/`llm` report whether the backing services are reachable —
`status` is always `ok` if the API itself is up.

### Validation error (empty question → 422)

```bash
curl -s -w '\n%{http_code}\n' localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question": ""}'
```

Questions must be 1–2000 characters.

### CORS preflight (as a browser would)

```bash
curl -s -X OPTIONS localhost:8000/chat \
  -H 'Origin: http://localhost:5173' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type' \
  -o /dev/null -w '%{http_code}\n'
```

CORS is open (`*`) when `SOMBEER_API__ENVIRONMENT=development`; in
`production` only the origins in `SOMMEBEER_API__CORS_ORIGINS` are allowed.
