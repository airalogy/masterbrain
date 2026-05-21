"""LiteLLM-backed provider facade.

Masterbrain keeps LiteLLM behind this module so endpoint and workflow code can
avoid depending on LiteLLM's public API directly. The facade intentionally
preserves the small OpenAI-compatible surface used by existing endpoints:
`client.chat.completions.create(...)` and `client.audio.transcriptions.create(...)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .registry import DEFAULT_PROVIDER_BASE_URL, ProviderName

OpenAICompatibleProvider = Literal["openai", "qwen"]


def _load_litellm():
    try:
        import litellm
    except ImportError as exc:  # pragma: no cover - dependency is installed by default
        raise RuntimeError(
            "LiteLLM is required for Masterbrain model calls. "
            "Install the `litellm` dependency or reinstall Masterbrain."
        ) from exc
    return litellm


def _with_openai_prefix(model: str) -> str:
    if "/" in model:
        return model
    return f"openai/{model}"


def normalize_litellm_model_name(
    model: str,
    *,
    provider: OpenAICompatibleProvider,
    api_base: str = "",
) -> str:
    """Return the model name LiteLLM should receive for this provider."""

    if provider == "qwen":
        # Masterbrain calls Qwen through DashScope's OpenAI-compatible endpoint.
        return _with_openai_prefix(model)

    if api_base:
        # Custom OpenAI-compatible endpoints need an explicit provider prefix.
        return _with_openai_prefix(model)

    return model


@dataclass(frozen=True)
class LiteLLMProviderConfig:
    provider: OpenAICompatibleProvider
    api_key: str
    api_base: str = ""

    @property
    def resolved_api_base(self) -> str:
        if self.api_base:
            return self.api_base
        if self.provider == "qwen":
            return DEFAULT_PROVIDER_BASE_URL["qwen"]
        return ""

    def normalize_model(self, model: str) -> str:
        return normalize_litellm_model_name(
            model,
            provider=self.provider,
            api_base=self.resolved_api_base,
        )


class LiteLLMChatCompletions:
    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self._config = config

    async def create(self, **kwargs: Any) -> Any:
        payload = self._build_payload(kwargs)
        return await _load_litellm().acompletion(**payload)

    def _build_payload(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        payload = dict(kwargs)

        model = payload.get("model")
        if isinstance(model, str) and model:
            payload["model"] = self._config.normalize_model(model)

        if self._config.api_key and "api_key" not in payload:
            payload["api_key"] = self._config.api_key

        api_base = self._config.resolved_api_base
        if api_base and "api_base" not in payload:
            payload["api_base"] = api_base

        return payload


class LiteLLMChat:
    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self.completions = LiteLLMChatCompletions(config)


class LiteLLMAudioTranscriptions:
    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self._config = config

    async def create(self, **kwargs: Any) -> Any:
        payload = self._build_payload(kwargs)
        return await _load_litellm().atranscription(**payload)

    def _build_payload(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        payload = dict(kwargs)

        model = payload.get("model")
        if isinstance(model, str) and model:
            payload["model"] = self._config.normalize_model(model)

        if self._config.api_key and "api_key" not in payload:
            payload["api_key"] = self._config.api_key

        api_base = self._config.resolved_api_base
        if api_base and "api_base" not in payload:
            payload["api_base"] = api_base

        return payload


class LiteLLMAudio:
    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self.transcriptions = LiteLLMAudioTranscriptions(config)


class LiteLLMOpenAICompatibleClient:
    """Small client facade matching the OpenAI SDK paths Masterbrain uses."""

    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self.provider = config.provider
        self.chat = LiteLLMChat(config)
        self.audio = LiteLLMAudio(config)


def build_litellm_openai_compatible_client(
    *,
    provider: ProviderName,
    api_key: str,
    base_url: str = "",
) -> LiteLLMOpenAICompatibleClient:
    if provider not in {"openai", "qwen"}:
        raise ValueError(f"Unsupported LiteLLM OpenAI-compatible provider: {provider}")

    config = LiteLLMProviderConfig(
        provider=provider,
        api_key=api_key,
        api_base=base_url,
    )
    return LiteLLMOpenAICompatibleClient(config)

