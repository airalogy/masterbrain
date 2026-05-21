"""Qwen provider adapter.

Qwen chat and vision models are currently accessed through DashScope's
OpenAI-compatible endpoint.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from .registry import DEFAULT_PROVIDER_BASE_URL


def build_qwen_client(*, api_key: str, base_url: str = "") -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url if base_url else DEFAULT_PROVIDER_BASE_URL["qwen"],
    )
