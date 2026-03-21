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


class PaperGenerationInput(BaseModel):
    """Paper generation input data"""

    protocol_markdown_list: list[str] = Field(
        ..., description="Complete AIMD protocol markdown format text list", min_items=1
    )
    model: SupportedModels = DEFAULT_MODEL
    enable_external_reference_search: bool = Field(
        False,
        description="Whether to use external search engine to retrieve references when generating the paper",
    )
    "If using reference search, need to obtain the TAVILY_API_KEY from https://www.tavily.com/ and fill it in the .env file."


class PaperGenerationOutput(BaseModel):
    """Paper generation output data"""

    paper_markdown: str = Field(description="Generated paper")
