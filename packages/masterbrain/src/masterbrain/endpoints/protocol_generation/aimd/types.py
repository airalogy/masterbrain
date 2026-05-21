from typing import Literal

from pydantic import BaseModel, Field

from masterbrain.types.model import Model


class SupportedModels(BaseModel):
    """Supported model configurations"""

    name: Literal[
        "qwen3.5-flash",
        "qwen3.5-plus",
        "qwen3-max",
        "gpt-4o-mini",
    ]
    enable_thinking: bool = False
    enable_search: bool = False


DEFAULT_MODEL = SupportedModels(
    name="qwen3.5-flash",
    enable_thinking=False,
    enable_search=False,
)


class AimdProtocolMessage(BaseModel):
    use_model: SupportedModels = DEFAULT_MODEL
    instruction: str = Field(..., min_length=1)
