__all__ = ["ModelProtocolMessage"]

from typing import Literal, Optional

from pydantic import BaseModel


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


class ModelProtocolMessage(BaseModel):
    use_model: SupportedModels = DEFAULT_MODEL
    protocol_aimd: Optional[str] = None
