"""
Field Input Endpoint Types

This module defines the data input/output structures for the field_input endpoint.
The field_input endpoint provides automatic slot filling functionality for experimental data.
"""

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

# Supported models for field_input endpoint
SupportedModels = Literal[
    # OpenAI text models
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo",
    # Qwen text models
    "qwen-max",
    "qwen3-max",
    "qwen3.5-plus",
    "qwen3.5-flash",
    # Qwen vision models（用于图片槽位抽取）
    "qwen-vl-plus",
    "qwen-vl-plus-latest",
    "qwen-vl-max-0201",
    "qwen3-vl-flash",
    "qwen3-vl-plus",
    "qwen-omni-turbo-latest",
]

ImageMode = Literal["one_step", "two_step"]
"""
图片槽位填充模式。

- ``one_step``：直接把 slot extraction prompt + 图片送给 VL 模型，一次调用完成识图和槽位提取。
  适合支持视觉的强模型（如 qwen-vl-plus-latest），延迟低、信息损耗少。

- ``two_step``（默认）：先用 VL 模型做 OCR 提取文本，再用文本模型做槽位抽取。
  格式遵从性更强，适合对输出格式要求严格的场景。
"""


class ModelConfig(BaseModel):
    """
    Model configuration for hub chat.
    """

    name: SupportedModels = "qwen3-max"
    """Model name."""

    temperature: float = 0.7
    """Model temperature for response randomness."""

    max_tokens: int = 2048
    """Maximum tokens for model response."""


class FieldInputRequest(BaseModel):
    """
    Input data structure for field_input endpoint.
    """

    chat_id: str
    """Chat session identifier."""

    user_id: str
    """User identifier."""

    model: ModelConfig
    """Model configuration for the chat."""

    history: List[Any] = Field(default_factory=list)
    """Chat conversation history."""

    scenario: Dict[str, Any] = Field(default_factory=dict)
    """
    Scenario configuration containing protocol schema and other settings.
    Should include 'protocol_schema' key with the schema for slot extraction.
    """

    image_mode: ImageMode = "two_step"
    """
    图片槽位填充模式（仅在输入为图片时生效）。
    ``one_step`` 直接用 VL 模型提取槽位；``two_step`` 先 OCR 再抽取（默认）。
    """


class SlotOperation(BaseModel):
    """
    Data structure for slot update operations.
    """

    operation: str = "update"
    """Operation type, typically 'update'."""

    rf_name: str
    """Field/slot name to be updated."""

    rf_value: Any
    """New value for the field/slot."""


class FieldInputResponse(BaseModel):
    """
    Output data structure for field_input endpoint.
    """

    chat_id: str
    """Chat session identifier."""

    user_id: str
    """User identifier."""

    model: ModelConfig
    """Model configuration used."""

    history: List[Any]
    """Updated chat conversation history with tool calls."""

    scenario: Dict[str, Any]
    """Updated scenario configuration."""


class SlotUpdateResult(BaseModel):
    """
    Data structure for slot update results.
    """

    required: List[SlotOperation]
    """List of slot update operations to be performed."""


__all__ = [
    "SupportedModels",
    "ImageMode",
    "ModelConfig",
    "FieldInputRequest",
    "FieldInputResponse",
    "SlotOperation",
    "SlotUpdateResult",
]
