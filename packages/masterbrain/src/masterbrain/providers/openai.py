"""OpenAI-compatible provider adapter."""

from __future__ import annotations

from collections.abc import Callable

from openai import AsyncOpenAI


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
