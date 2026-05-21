"""Provider registry and model-to-provider detection.

This module has no SDK imports. It is safe for core code and tests that only
need to reason about supported model families.
"""

from __future__ import annotations

from typing import Literal, get_args

ProviderName = Literal["openai", "qwen"]

AvailableOpenAIModel = Literal[
    "gpt-3.5-turbo",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o1-mini",
    "o1-preview",
    "o1-preview-2024-09-12",
    "whisper-large-v3-turbo",
    "gpt-4o-transcribe",
]

AvailableQwenModel = Literal[
    "qwen-long",
    "qwen3-max",
    "qwen3.5-plus",
    "qwen3.5-plus-latest",
    "qwen3.5-flash",
    "qvq-72b-preview",
    "qwq-32b-preview",
    "qwen-vl-plus",
    "qwen-vl-plus-latest",
    "qwen-vl-max-0201",
    "qwen3-vl-flash",
    "qwen3-vl-plus",
    "qwen-omni-turbo-latest",
    "qwq-plus-latest",
    "qwen-2-72b",
    "qwen-max",
    "qwen3-asr-flash",
]

AvailableModel = Literal[AvailableOpenAIModel, AvailableQwenModel]

DEFAULT_PROVIDER_BASE_URL: dict[ProviderName, str] = {
    "openai": "https://api.openai.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


def detect_model_provider(model_name: str) -> ProviderName:
    """Infer the upstream provider for a supported model name."""

    if model_name in get_args(AvailableOpenAIModel) or model_name.startswith(("gpt-", "o1-")):
        return "openai"
    if model_name in get_args(AvailableQwenModel) or model_name.startswith(
        ("qwen", "qwq", "qvq")
    ):
        return "qwen"
    raise ValueError(f"Unsupported model provider for model `{model_name}`")
