"""Phoenix (Arize) OTel tracing setup — local by default, configurable."""

from __future__ import annotations

from .config import PhoenixConfig


def _connect_phoenix(cfg: PhoenixConfig):
    import phoenix.otel
    from openinference.instrumentation.langchain import LangChainInstrumentor

    headers = (("authorization", f"Bearer {cfg.api_key}"),) if cfg.api_key else ()
    tracer_provider = phoenix.otel.register(
        endpoint=f"{cfg.endpoint}/v1/traces",
        headers=headers,
    )
    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider, skip_dep_check=True)
    return tracer_provider


def setup_tracing(cfg: PhoenixConfig):
    """Register Phoenix as OTel tracer provider and instrument LangChain.

    Returns the tracer provider, or None when disabled/unavailable.
    Fails soft: a down Phoenix server must never break the agent.
    """
    if not cfg.enabled:
        return None
    try:
        return _connect_phoenix(cfg)
    except Exception as exc:  # noqa: BLE001
        print(f"[sommebeer] Phoenix tracing disabled: {exc}")
        return None
