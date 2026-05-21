"""Concrete model provider adapters and provider selection helpers."""

from .litellm import (
    LiteLLMOpenAICompatibleClient,
    LiteLLMProviderConfig,
    build_litellm_openai_compatible_client,
    normalize_litellm_model_name,
)
from .openai import AsyncOpenAIClient, LazyAsyncOpenAI, build_openai_client
from .qwen import build_qwen_client
from .registry import (
    AvailableModel,
    AvailableOpenAIModel,
    AvailableQwenModel,
    DEFAULT_PROVIDER_BASE_URL,
    ProviderName,
    detect_model_provider,
)

__all__ = [
    "AsyncOpenAIClient",
    "AvailableModel",
    "AvailableOpenAIModel",
    "AvailableQwenModel",
    "DEFAULT_PROVIDER_BASE_URL",
    "LazyAsyncOpenAI",
    "LiteLLMOpenAICompatibleClient",
    "LiteLLMProviderConfig",
    "ProviderName",
    "build_litellm_openai_compatible_client",
    "build_openai_client",
    "build_qwen_client",
    "detect_model_provider",
    "normalize_litellm_model_name",
]
