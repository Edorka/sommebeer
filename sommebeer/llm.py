"""LLM factory: one chat model, three interchangeable providers."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from .config import LLMConfig


def _local_model(cfg: LLMConfig) -> BaseChatModel:
    """llama-server / Ollama — any OpenAI-compatible local endpoint."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=cfg.model,
        base_url=cfg.base_url,
        api_key=cfg.api_key or "not-needed",
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )


def _deepinfra_model(cfg: LLMConfig) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=cfg.di_model,
        base_url="https://api.deepinfra.com/v1/openai",
        api_key=cfg.di_api_key,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )


def _gcp_model(cfg: LLMConfig) -> BaseChatModel:
    from langchain_google_vertexai import ChatVertexAI

    return ChatVertexAI(
        model=cfg.gcp_model,
        project=cfg.gcp_project,
        location=cfg.gcp_location,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )


_FACTORIES = {
    "local": _local_model,
    "deepinfra": _deepinfra_model,
    "gcp": _gcp_model,
}


def get_chat_model(cfg: LLMConfig) -> BaseChatModel:
    factory = _FACTORIES.get(cfg.provider)
    if factory is None:
        raise ValueError(f"unknown provider: {cfg.provider}")
    return factory(cfg)
