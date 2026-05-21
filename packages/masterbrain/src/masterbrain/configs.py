"""
Configuration file for `masterbrain`.
"""

import os
from pathlib import Path

# from enum import Enum

from dotenv import load_dotenv

from masterbrain.providers import (
    AvailableModel,
    AvailableOpenAIModel,
    AvailableQwenModel,
    LiteLLMOpenAICompatibleClient,
    build_litellm_openai_compatible_client,
    detect_model_provider,
)

API_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = API_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)


# MARK: OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "")


DEFAULT_MODEL = "qwen3.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

DEFAULT_QWEN_TEXT_MODEL = "qwen3.5-flash"
DEFAULT_QWEN_VL_MODEL = "qwen-vl-plus-latest"

DEFAULT_MAX_TOKENS = 512
"""
Notes
-----
The max_tokens only determines the maximum number of tokens to generate. It does not mean that a smaller number of max_tokens will generate a shorter response.
"""
DEFAULT_TEMPERATURE = 0


# MARK: Clients

OPENAI_CLIENT: LiteLLMOpenAICompatibleClient = build_litellm_openai_compatible_client(
    provider="openai",
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)
DASHSCOPE_CLIENT: LiteLLMOpenAICompatibleClient = build_litellm_openai_compatible_client(
    provider="qwen",
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
)


def select_client(model: AvailableModel) -> LiteLLMOpenAICompatibleClient:
    """
    Select the client based on the model.

    Parameters
    ----------
    model : AvailableModel
        The model to use.

    Returns
    -------
    None
    """
    try:
        provider = detect_model_provider(model)
    except ValueError:
        return OPENAI_CLIENT

    if provider == "openai":
        return OPENAI_CLIENT
    return DASHSCOPE_CLIENT


# MARK: Debugging
DEBUG = os.environ.get("DEBUG", "False").lower().strip() in ["true", "1"]
