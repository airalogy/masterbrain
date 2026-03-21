"""
配置类
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class SearchAPI(Enum):
    """Search API types"""

    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    LINKUP = "linkup"
    DUCKDUCKGO = "duckduckgo"
    GOOGLESEARCH = "googlesearch"
    LLM_BUILTIN = "llm_builtin"


@dataclass(kw_only=True)
class Configuration:
    """Configuration for paper generation and search."""

    # Search configuration
    search_api: SearchAPI = SearchAPI.TAVILY
    search_api_config: Optional[Dict[str, Any]] = field(
        default_factory=lambda: {
            "max_results": 2,
            "topic": "general",
            "include_images": True,
            "include_image_descriptions": True,
        }
    )

    # Model configuration
    number_of_queries: int = 3
    max_search_depth: int = 1
    writer_provider: str = "openai"  # for langchain call
    writer_model: str = "qwen3.5-flash"
    writer_model_kwargs: Optional[Dict[str, Any]] = None
