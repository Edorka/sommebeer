# frontend

The UI for sommebeer — will talk to the HTTP API in [`../api/`](../api/).

## API contract (v1)

### `POST /chat`

Request:

```json
{"question": "recommend me 2 IPAs"}
```

Response — `answer` is **Markdown** (bold names, numbered lists), ready to render:

```json
{"answer": "Sure! Here are **Sculpin** … and **60 Minute IPA** …"}
```

### `GET /health`

```json
{"status": "ok", "weaviate": true, "llm": true}
```

## Notes

- Each request is single-shot: no conversation memory server-side.
- Interactive API docs (OpenAPI/Swagger): `http://localhost:8000/docs`
- CORS: open (`*`) when `SOMMEBEER_API__ENVIRONMENT=development`; in
  `production` only the origins in `SOMMEBEER_API__CORS_ORIGINS` are allowed.
