import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_generation.aimd.logic import generate_stream
from masterbrain.endpoints.protocol_generation.aimd.types import (
    AimdProtocolMessage,
    SupportedModels,
)

# 获取支持的模型名称
AIMD_MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"]


@pytest.mark.asyncio
@pytest.mark.aimd
@pytest.mark.parametrize("model_name", AIMD_MODEL_NAMES)
async def test_generate_stream_success(model_name: str):
    """Test successful protocol generation with mocked client."""

    if DEBUG:
        print(f"Testing AIMD model: {model_name}")

    # Mock the OpenAI client and its response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    # Mock streaming response chunks
    async def mock_chunks(self):
        chunks = [
            "# 合成金三角形纳米片的实验协议\n\n",
            "**Objective:** 合成具有特定尺寸和形状的金三角形纳米片。\n\n",
            "## Basic Information\n\n",
            "实验者姓名: {{var|experimenter_name}}\n",
            "实验时间: {{var|experiment_time}}\n\n",
            "## Experimental Steps\n\n",
            "{{step|seed_solution_preparation,1}} 种子溶液的合成\n\n",
            "详细步骤内容...\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create test request
    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name=model_name),
        instruction="合成金三角形纳米片的实验步骤",
    )

    history = [{"role": "system", "content": "You are an AI assistant."}]

    # Mock the select_client function
    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Collect streamed content
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Verify content was generated
        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "实验协议" in full_content or "experimental" in full_content.lower()

        # Verify client was called
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert "messages" in call_kwargs


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_empty_instruction():
    """Test stream generation with minimal instruction."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = ["简短的协议回复。"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="简单测试"
    )

    history = [{"role": "system", "content": "Test system message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_api_error():
    """Test stream generation when API fails."""

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="测试协议生成"
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        with pytest.raises(Exception) as exc_info:
            content_chunks = []
            async for chunk in generate_stream(protocol_msg, history):
                content_chunks.append(chunk)

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_empty_response():
    """Test handling of empty response from model."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_empty_chunks(self):
        # No chunks yielded
        return
        yield  # unreachable

    mock_response.__aiter__ = mock_empty_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="测试空响应"
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Should handle empty response gracefully
        full_content = "".join(content_chunks)
        assert len(full_content) == 0


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_with_thinking_enabled():
    """Test stream generation with thinking enabled."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "<thinking>\n这是思考过程\n</thinking>\n",
            "# 实验协议\n\n",
            "详细的协议内容...\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(
            name="qwen3.5-plus", enable_thinking=True, enable_search=False
        ),
        instruction="详细的实验协议",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        # Should contain thinking content
        assert "thinking" in full_content or "思考" in full_content


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_timeout():
    """Test stream generation with timeout handling."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def slow_chunks(self):
        await asyncio.sleep(10)  # Simulate slow response
        chunk = AsyncMock()
        chunk.choices = [AsyncMock()]
        chunk.choices[0].delta.content = "延迟的回复"
        yield chunk

    mock_response.__aiter__ = slow_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="超时测试"
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Should timeout within reasonable time
        with pytest.raises(asyncio.TimeoutError):
            content_chunks = []
            async with asyncio.timeout(5.0):
                async for chunk in generate_stream(protocol_msg, history):
                    content_chunks.append(chunk)


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_with_demo_data(demo_input_data):
    """Test stream generation using demo input data."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "# 合成金三角形纳米片的实验协议\n\n",
            "基于提供的指令生成的协议内容...\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create protocol message from demo data
    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(**demo_input_data["use_model"]),
        instruction=demo_input_data["instruction"],
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "金三角形纳米片" in full_content or "protocol" in full_content.lower()


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_generate_stream_history_modification():
    """Test that history is properly modified during stream generation."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = ["测试协议内容"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="测试历史修改"
    )

    initial_history = [{"role": "system", "content": "Initial system message"}]
    history = initial_history.copy()

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Verify history was modified (user message should be added)
        assert len(history) > len(initial_history)

        # Check that user message was added
        user_messages = [msg for msg in history if msg.get("role") == "user"]
        assert len(user_messages) > 0
        assert "测试历史修改" in user_messages[-1]["content"]
