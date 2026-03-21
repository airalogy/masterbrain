from typing import Literal

from pydantic import BaseModel, Field


class SupportedModels(BaseModel):
    """Supported model configurations"""

    name: Literal[
        "qwen3.5-flash",
        "qwen3.5-plus",
        "qwen3-max",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ]
    enable_thinking: bool = False
    enable_search: bool = False


DEFAULT_MODEL = SupportedModels(
    name="qwen3.5-flash",
    enable_thinking=False,
    enable_search=False,
)


class ProtocolDebugInput(BaseModel):
    """Protocol debug input data"""

    full_protocol: str = Field(description="Complete AIMD protocol document")
    suspect_protocol: str = Field(
        description="Protocol segment that may contain syntax errors"
    )
    model: SupportedModels = DEFAULT_MODEL


class ProtocolDebugOutput(BaseModel):
    """Protocol debug output data"""

    has_errors: bool = Field(description="Whether syntax errors were found")
    fixed_protocol: str = Field(
        description="Fixed protocol segment (empty if no errors)"
    )
    response: str = Field(description="Debugging explanation and reasoning")
