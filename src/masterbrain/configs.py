"""
Configuration file for `masterbrain`.
"""

import os

# from enum import Enum
from typing import Literal, get_args

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(override=True)


# MARK: OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "")


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

OPENAI_CLIENT = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
)

DASHSCOPE_CLIENT = AsyncOpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL
    if DASHSCOPE_BASE_URL
    else "https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def select_client(model: AvailableModel) -> AsyncOpenAI:
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
    if model in get_args(AvailableOpenAIModel):
        return OPENAI_CLIENT
    elif model in get_args(AvailableQwenModel):
        return DASHSCOPE_CLIENT
    else:
        return OPENAI_CLIENT


# MARK: Debugging
DEBUG = os.environ.get("DEBUG", "False").lower().strip() in ["true", "1"]
