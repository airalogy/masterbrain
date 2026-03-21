from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

SupportedVisionModels = Literal[
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-vision-preview",
    "qwen-vl-plus",
    "qwen-vl-plus-latest",
    "qwen-vl-max-0201",
    "qwen3-vl-flash",
    "qwen3-vl-plus",
    "qwen-vl-max",
    "qwen3.5-flash",
    "qwen3.5-plus",
]


class VisionRequestBody(BaseModel):
    chat_id: str
    user_id: str
    model: SupportedVisionModels = "qwen-vl-plus"
    history: List[Any] = Field(default_factory=list)
    scenario: Dict[str, Any] = Field(default_factory=dict)
