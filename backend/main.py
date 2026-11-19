"""HTTP API for the beer tender — thin wiring, all logic in the core package.

Run from the repo root:
    uvicorn backend.main:app --reload
"""

from __future__ import annotations

import socket
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sommebeer.config import get_settings
from sommebeer.graph import build_graph
from sommebeer.llm import get_chat_model
from sommebeer.retriever import BeerRetriever, connect
from sommebeer.tracing import setup_tracing


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """The tender's reply — the answer is Markdown."""

    answer: str


def _build_graph():
    """Assemble the core graph once, at startup."""
    settings = get_settings()
    client = connect(settings.weaviate)
    retriever = BeerRetriever(settings.weaviate, client)
    chat_model = get_chat_model(settings.llm)
    return build_graph(chat_model, retriever)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if getattr(app.state, "graph", None) is None:
        app.state.graph = _build_graph()
    yield


def _cors_origins(settings) -> list[str]:
    """Open in development; only the configured origins in production."""
    if settings.api.environment == "development":
        return ["*"]
    return settings.api.cors_origins


def _register_cors(app: FastAPI, settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(settings),
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _instrument_http(app: FastAPI, tracer_provider) -> None:
    """HTTP spans for every request, shown alongside LLM/retriever spans."""
    if tracer_provider is None:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    except ImportError as exc:  # noqa: BLE001 — optional dep, fail soft
        print(f"[sommebeer] FastAPI HTTP tracing disabled: {exc}")


def _llm_reachable(settings) -> bool:
    """TCP reachability of the configured provider — provider-aware: the
    local provider's URL lives in llm.base_url, while deepinfra/gcp have
    their own endpoints."""
    llm = settings.llm
    if llm.provider == "deepinfra":
        endpoint = urlparse("https://api.deepinfra.com/v1/openai")
    elif llm.provider == "gcp":
        return True  # no cheap socket probe for Vertex; trust the SDK path
    else:
        endpoint = urlparse(llm.base_url)
    try:
        with socket.create_connection((endpoint.hostname, endpoint.port or 443),
                                      timeout=2):
            return True
    except OSError:
        return False


def _weaviate_ready(settings) -> bool:
    try:
        client = connect(settings.weaviate)
        try:
            return client.is_ready()
        finally:
            client.close()
    except Exception:  # noqa: BLE001 — health must never raise
        return False


def _health_status(app: FastAPI) -> dict:
    settings = app.state.settings
    return {"status": "ok", "weaviate": _weaviate_ready(settings),
            "llm": _llm_reachable(settings)}


def _register_routes(app: FastAPI) -> None:
    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        state = app.state.graph.invoke(
            {"question": request.question}, config={"recursion_limit": 10})
        return ChatResponse(answer=state["answer"])

    @app.get("/health")
    def health() -> dict:
        return _health_status(app)


def create_app() -> FastAPI:
    settings = get_settings()
    tracer_provider = setup_tracing(settings.phoenix)
    app = FastAPI(title="sommebeer", lifespan=_lifespan)
    app.state.settings = settings
    _register_cors(app, settings)
    _instrument_http(app, tracer_provider)
    _register_routes(app)
    return app


app = create_app()
