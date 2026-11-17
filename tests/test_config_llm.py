"""Tests for config validation and the LLM provider factory."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from sommebeer.config import LLMConfig, get_settings
from sommebeer.llm import get_chat_model


class TestLLMConfigValidation:
    def test_local_is_the_default(self):
        cfg = LLMConfig()
        assert cfg.provider == "local"
        assert cfg.api_key == "not-needed"

    def test_invalid_provider_rejected(self):
        with pytest.raises(ValidationError):
            LLMConfig(provider="skynet")

    def test_deepinfra_requires_api_key(self):
        with pytest.raises(ValidationError):
            LLMConfig(provider="deepinfra")

    def test_deepinfra_with_key_ok(self):
        cfg = LLMConfig(provider="deepinfra", di_api_key="secret")
        assert cfg.di_model.startswith("Qwen/")

    def test_gcp_requires_project(self):
        with pytest.raises(ValidationError):
            LLMConfig(provider="gcp")

    def test_gcp_with_project_ok(self):
        cfg = LLMConfig(provider="gcp", gcp_project="my-project")
        assert cfg.gcp_model == "gemini-2.0-flash"


class TestEnvLoading:
    def test_env_prefix_is_sommebeer(self, monkeypatch):
        monkeypatch.setenv("SOMMEBEER_LLM__PROVIDER", "local")
        monkeypatch.setenv("SOMMEBEER_LLM__TEMPERATURE", "0.1")
        settings = get_settings()
        assert settings.llm.provider == "local"
        assert settings.llm.temperature == 0.1

    def test_weaviate_defaults(self):
        settings = get_settings()
        assert settings.weaviate.host == "localhost"
        assert settings.weaviate.port == 8080
        assert settings.weaviate.collection == "Beer"


class TestFactory:
    @staticmethod
    def _base_url(llm) -> str:
        return str(getattr(llm, "openai_api_base", None) or getattr(llm, "base_url"))

    def test_local_uses_llama_server(self):
        llm = get_chat_model(LLMConfig())
        assert "127.0.0.1:11434" in self._base_url(llm)

    def test_deepinfra_uses_deepinfra_endpoint(self):
        llm = get_chat_model(LLMConfig(provider="deepinfra", di_api_key="x"))
        assert "deepinfra" in self._base_url(llm)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            get_chat_model(SimpleNamespace(provider="skynet"))  # noqa
