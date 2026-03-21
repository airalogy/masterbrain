from typing import Literal, Optional

from pydantic import BaseModel, Field


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


class ProtocolCheckInput(BaseModel):
    """Protocol check input data"""

    aimd_protocol: Optional[str] = Field(
        None, description="Original protocol file in AIMD format"
    )
    py_model: Optional[str] = Field(None, description="Original model file")
    py_assigner: Optional[str] = Field(None, description="Original assigner file")
    feedback: str = Field(
        default="", description="User feedback for improving the protocol"
    )
    target_file: str = Field(
        default="protocol", description="Target file to update based on input files"
    )
    model: SupportedModels = DEFAULT_MODEL
    check_num: int = Field(default=0, description="Check round number")
