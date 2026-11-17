"""Pydantic settings: every endpoint and provider is configurable via env/.env."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    """One of three providers, each with its own knobs."""

    provider: Literal["local", "deepinfra", "gcp"] = "local"
    temperature: float = 0.3

    # local (llama-server / Ollama, OpenAI-compatible)
    model: str = "/opt/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    base_url: str = "http://127.0.0.1:11434/v1"
    api_key: str | None = "not-needed"

    # deepinfra
    di_model: str = "Qwen/Qwen2.5-72B-Instruct"
    di_api_key: str | None = None

    # gcp (vertex ai)
    gcp_model: str = "gemini-2.0-flash"
    gcp_project: str | None = None
    gcp_location: str = "us-central1"

    @field_validator("di_api_key")
    @classmethod
    def _di_needs_key(cls, v, info):
        if info.data.get("provider") == "deepinfra" and not v:
            raise ValueError("SOMBEER_LLM__DI_API_KEY is required when PROVIDER=deepinfra")
        return v

    @field_validator("gcp_project")
    @classmethod
    def _gcp_needs_project(cls, v, info):
        if info.data.get("provider") == "gcp" and not v:
            raise ValueError("SOMBEER_LLM__GCP_PROJECT is required when PROVIDER=gcp")
        return v


class WeaviateConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051
    collection: str = "Beer"
    limit: int = 5
    distance_cutoff: float = 0.45  # cosine similarity cutoff (1 - distance)


class PhoenixConfig(BaseModel):
    enabled: bool = True
    endpoint: str = "http://localhost:6006"
    api_key: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SOMBEER_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    weaviate: WeaviateConfig = Field(default_factory=WeaviateConfig)
    phoenix: PhoenixConfig = Field(default_factory=PhoenixConfig)


def get_settings() -> Settings:
    return Settings()
