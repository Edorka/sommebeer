"""Pydantic settings: every endpoint and provider is configurable via env/.env."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    """One of three providers, each with its own knobs."""

    provider: Literal["local", "deepinfra", "gcp"] = "local"
    temperature: float = 0.3
    max_tokens: int = 1024  # explicit: DeepInfra defaults missing max_tokens to full context

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

    @model_validator(mode="after")
    def _provider_requirements(self):
        if self.provider == "deepinfra" and not self.di_api_key:
            raise ValueError(
                "SOMMEBEER_LLM__DI_API_KEY is required when PROVIDER=deepinfra")
        if self.provider == "gcp" and not self.gcp_project:
            raise ValueError(
                "SOMMEBEER_LLM__GCP_PROJECT is required when PROVIDER=gcp")
        return self


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


class ApiConfig(BaseModel):
    """HTTP deliverable settings — CORS is open only outside production."""

    environment: Literal["development", "production"] = "development"
    cors_origins: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SOMMEBEER_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    weaviate: WeaviateConfig = Field(default_factory=WeaviateConfig)
    phoenix: PhoenixConfig = Field(default_factory=PhoenixConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)


def get_settings() -> Settings:
    return Settings()
