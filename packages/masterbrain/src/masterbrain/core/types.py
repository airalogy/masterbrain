"""Provider-neutral AI contracts used by Masterbrain core logic.

These types intentionally avoid importing OpenAI, DashScope, FastAPI, or any
Web-specific model. Endpoint and provider layers can translate their concrete
SDK payloads into these shapes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypedDict

ChatRole = Literal["system", "user", "assistant", "tool"]


class ChatMessage(TypedDict, total=False):
    role: ChatRole
    content: Any
    name: str
    tool_call_id: str


class ChatRequest(TypedDict, total=False):
    model: str
    messages: Sequence[Mapping[str, Any]]
    stream: bool
    tools: Sequence[Mapping[str, Any]]
    tool_choice: str | Mapping[str, Any]
    extra_body: Mapping[str, Any]
    timeout: float


@dataclass(frozen=True)
class ModelConfig:
    name: str
    enable_thinking: bool = False
    enable_search: bool = False


@dataclass(frozen=True)
class StreamTextChunk:
    content: str
    reasoning_content: str | None = None


class ChatModelProvider(Protocol):
    """Minimal async chat provider contract for core workflows."""

    name: str

    async def stream_text(self, request: ChatRequest) -> AsyncIterator[StreamTextChunk]:
        """Stream text chunks for a provider-neutral request."""
        ...

    async def complete_text(self, request: ChatRequest) -> str:
        """Return one complete text response for a provider-neutral request."""
        ...
