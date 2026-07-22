"""LiteLLM-backed provider facade.

Masterbrain keeps LiteLLM behind this module so endpoint and workflow code can
avoid depending on LiteLLM's public API directly. The facade intentionally
preserves the small OpenAI-compatible surface used by existing endpoints:
`client.chat.completions.create(...)` and `client.audio.transcriptions.create(...)`.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Literal

from masterbrain.core.usage import UsageCallTracker, to_usage_mapping

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
        requested_model = kwargs.get("model")
        if not isinstance(requested_model, str) or not requested_model:
            requested_model = "unknown"
        tracker = UsageCallTracker(
            provider=self._config.provider,
            requested_model=requested_model,
            call_type="chat.completion",
        )
        payload = self._build_payload(kwargs)
        try:
            response = await _load_litellm().acompletion(**payload)
        except BaseException as exc:
            await tracker.fail(exc)
            raise

        if payload.get("stream") is True:
            try:
                return LiteLLMUsageTrackingStream(response, tracker)
            except BaseException as exc:
                await tracker.fail(exc)
                raise

        await _finish_litellm_response(tracker, response)
        return response

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

        if payload.get("stream") is True:
            stream_options = dict(payload.get("stream_options") or {})
            stream_options["include_usage"] = True
            payload["stream_options"] = stream_options

        return payload


def _response_attribute(response: Any, name: str, default: Any = None) -> Any:
    if isinstance(response, dict):
        return response.get(name, default)
    return getattr(response, name, default)


def _litellm_response_cost(response: Any) -> Any:
    hidden = _response_attribute(response, "_hidden_params")
    if isinstance(hidden, dict):
        return hidden.get("response_cost")
    return _response_attribute(response, "response_cost")


async def _finish_litellm_response(
    tracker: UsageCallTracker,
    response: Any,
) -> None:
    await tracker.succeed(
        resolved_model=_response_attribute(response, "model")
        or tracker.requested_model,
        raw_usage=_response_attribute(response, "usage"),
        provider_cost=_litellm_response_cost(response),
        provider_cost_currency="USD",
        provider_cost_source="litellm",
        source="litellm",
        provider_request_id=_response_attribute(response, "id"),
    )


class LiteLLMUsageTrackingStream:
    """Transparent async stream that records LiteLLM's final usage chunk."""

    def __init__(self, stream: Any, tracker: UsageCallTracker) -> None:
        self._stream = stream
        self._iterator = stream.__aiter__()
        self._tracker = tracker
        self._latest_usage: dict[str, Any] = {}
        self._latest_model: str | None = None
        self._latest_cost: Any = None
        self._provider_request_id: str | None = None

    def __aiter__(self) -> "LiteLLMUsageTrackingStream":
        return self

    async def __anext__(self) -> Any:
        try:
            chunk = await self._iterator.__anext__()
        except StopAsyncIteration:
            await self._finish_success()
            raise
        except BaseException as exc:
            await self._tracker.fail(exc)
            raise

        usage = to_usage_mapping(_response_attribute(chunk, "usage"))
        if usage:
            self._latest_usage = usage
        model = _response_attribute(chunk, "model")
        if isinstance(model, str) and model:
            self._latest_model = model
        response_cost = _litellm_response_cost(chunk)
        if response_cost is not None:
            self._latest_cost = response_cost
        request_id = _response_attribute(chunk, "id")
        if isinstance(request_id, str) and request_id:
            self._provider_request_id = request_id
        return chunk

    async def _finish_success(self) -> None:
        await self._tracker.succeed(
            resolved_model=self._latest_model or self._tracker.requested_model,
            raw_usage=self._latest_usage,
            provider_cost=self._latest_cost,
            provider_cost_currency="USD",
            provider_cost_source="litellm",
            source="litellm",
            provider_request_id=self._provider_request_id,
        )

    async def aclose(self) -> None:
        close = getattr(self._iterator, "aclose", None)
        if callable(close):
            result = close()
            if inspect.isawaitable(result):
                await result
        if not self._tracker.finished:
            if self._latest_usage:
                await self._finish_success()
            else:
                await self._tracker.finish(status="cancelled", source="unavailable")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


class LiteLLMChat:
    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self.completions = LiteLLMChatCompletions(config)


class LiteLLMAudioTranscriptions:
    def __init__(self, config: LiteLLMProviderConfig) -> None:
        self._config = config

    async def create(self, **kwargs: Any) -> Any:
        requested_model = kwargs.get("model")
        if not isinstance(requested_model, str) or not requested_model:
            requested_model = "unknown"
        tracker = UsageCallTracker(
            provider=self._config.provider,
            requested_model=requested_model,
            call_type="audio.transcription",
        )
        payload = self._build_payload(kwargs)
        try:
            response = await _load_litellm().atranscription(**payload)
        except BaseException as exc:
            await tracker.fail(exc)
            raise
        await _finish_litellm_response(tracker, response)
        return response

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
