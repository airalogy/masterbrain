"""OpenAI-compatible provider adapter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI

from masterbrain.core.usage import UsageCallTracker

from .registry import DEFAULT_PROVIDER_BASE_URL, ProviderName


class OpenAICompatibleEmbeddings:
    """Metered embeddings with exact dimensions and one upstream attempt.

    Unlike chat, embeddings use the SDK directly: some LiteLLM versions reject
    Qwen dimensions and replace zero retries with a default. Keep that transport
    detail inside Masterbrain, without patching dependencies or global settings.
    """

    def __init__(self, *, provider: ProviderName, api_key: str, base_url: str = ""):
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url or DEFAULT_PROVIDER_BASE_URL[provider]

    async def create(self, **kwargs: Any) -> Any:
        model = kwargs.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An embedding model is required")
        tracker = UsageCallTracker(
            provider=self._provider,
            requested_model=model,
            call_type="embedding",
        )
        try:
            async with AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                max_retries=0,
            ) as client:
                response = await client.embeddings.create(**kwargs)
        except BaseException as exc:
            await tracker.fail(exc)
            raise
        await tracker.succeed(
            resolved_model=getattr(response, "model", None) or model,
            raw_usage=getattr(response, "usage", None),
            source="provider",
            provider_request_id=getattr(response, "_request_id", None),
        )
        return response


class LazyAsyncOpenAI:
    """Instantiate an OpenAI-compatible client only when it is first used."""

    def __init__(self, factory: Callable[[], AsyncOpenAI]) -> None:
        self._factory = factory
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = self._factory()
        return self._client

    def __getattr__(self, name: str):
        return getattr(self._get_client(), name)


AsyncOpenAIClient = AsyncOpenAI | LazyAsyncOpenAI


def build_openai_client(*, api_key: str, base_url: str = "") -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url if base_url else None,
    )
