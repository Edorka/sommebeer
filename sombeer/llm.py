"""LLM factory: one chat model, three interchangeable providers."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from .config import LLMConfig


def get_chat_model(cfg: LLMConfig) -> BaseChatModel:
    if cfg.provider == "local":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=cfg.model,
            base_url=cfg.base_url,
            api_key=cfg.api_key or "not-needed",
            temperature=cfg.temperature,
        )

    if cfg.provider == "deepinfra":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=cfg.di_model,
            base_url="https://api.deepinfra.com/v1/openai",
            api_key=cfg.di_api_key,
            temperature=cfg.temperature,
        )

    if cfg.provider == "gcp":
        from langchain_google_vertexai import ChatVertexAI

        return ChatVertexAI(
            model=cfg.gcp_model,
            project=cfg.gcp_project,
            location=cfg.gcp_location,
            temperature=cfg.temperature,
        )

    raise ValueError(f"unknown provider: {cfg.provider}")
