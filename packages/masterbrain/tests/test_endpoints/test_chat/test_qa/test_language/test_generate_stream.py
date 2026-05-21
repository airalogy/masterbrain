import asyncio
from typing import get_args

import pytest
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from masterbrain.configs import DEBUG
from masterbrain.endpoints.chat.qa.language.logic import generate_stream
from masterbrain.endpoints.chat.qa.language.types import ChatInput, SupportedModels

# discover allowed names from the pydantic model's Literal annotation
MODEL_NAMES = list(get_args(SupportedModels.__annotations__["name"]))


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("name", MODEL_NAMES)
@pytest.mark.parametrize("enable_thinking", [False, True])
@pytest.mark.parametrize("enable_search", [False, True])
async def test_generate_stream(name: str, enable_thinking: bool, enable_search: bool):
    """Call generate_stream and verify streamed text contains <think> tags when enabled."""

    # build via parse_obj to avoid static type-checker complaints about Literal
    model = SupportedModels.model_validate(
        {
            "name": name,
            "enable_thinking": enable_thinking,
            "enable_search": enable_search,
        }
    )

    if DEBUG:
        print(f"Testing model: {model.model_dump()}")

    user_msg = ChatCompletionUserMessageParam(
        {
            "role": "user",
            "content": "Who are you? Please search for Airalogy and then answer what Airalogy is.",
        }
    )

    chat_input = ChatInput(model=model, messages=[user_msg])

    async def consume_all_delta():
        chunks: list[str] = []
        async for chunk in generate_stream(chat_input):
            assert isinstance(chunk, str)
            chunks.append(chunk)
        return "".join(chunks)

    text = await asyncio.wait_for(consume_all_delta(), timeout=60)

    assert isinstance(text, str)
    assert text.strip() != ""

    if enable_thinking:
        assert "<think>" in text
        assert "</think>" in text
        assert text.index("<think>") < text.index("</think>")
        assert text.count("<think>") == text.count("</think>")
    else:
        assert "<think>" not in text
        assert "</think>" not in text
