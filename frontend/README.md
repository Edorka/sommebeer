# frontend

The UI for sommebeer — will talk to the HTTP API in [`../api/`](../api/).

## Stack

- [Lit](https://lit.dev) web components — all styling is embedded per-component
  (`static styles`) and scoped by the Shadow DOM; the only dependency.
- `src/markdown.js` — ~1 KB Markdown renderer that emits Lit template parts
  (never raw HTML), so no sanitizer dependency.
- Build/dev: Vite. Bundle: ~10 KB gzip total.

## Develop

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

`npm run dev` starts Vite on port 5173 and proxies `/chat` and `/health` to the
API on `http://localhost:8000` — so start the API first:

```bash
uvicorn api.main:app --reload
```

No CORS surface: the pages call relative URLs and only Vite talks to the API.

## Build

```bash
cd frontend
npm run build        # outputs dist/ (~10 KB gzip)
npm run preview      # serve dist/ at :4173 (same /chat + /health proxy in dev only)
```

The output is two static-ish files (`dist/index.html` + one JS bundle). Serve it
from any static file server or reverse-proxy `/chat`/`/health` to the API.

## Structure

```
index.html                      mounts <sommebeer-chat>
src/index.js                    component import
src/components/sommebeer-chat.js  whole UI; styles embedded (`static styles`)
src/components/md-block.js        Markdown answer display; own styles
src/markdown.js                  tiny safe Markdown → Lit template parts
```

## API contract (v1)

The UI speaks exactly two endpoints, defined in [`../api/README.md`](../api/README.md):

- `POST /chat` → `{"question": …}` → `{"answer": "<markdown>"}`
- `GET /health` → `{"status": "ok", "weaviate": true, "llm": true}`

## Notes

- Each request is single-shot: no conversation memory server-side.
- Interactive API docs (OpenAPI/Swagger): `http://localhost:8000/docs`
- CORS: open (`*`) when `SOMMEBEER_API__ENVIRONMENT=development`; in
  `production` only the origins in `SOMMEBEER_API__CORS_ORIGINS` are allowed.
