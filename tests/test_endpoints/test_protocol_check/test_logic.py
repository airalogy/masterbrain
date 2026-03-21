import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncOpenAI

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_check.logic import (
    determine_target_file,
    generate_stream,
)
from masterbrain.endpoints.protocol_check.types import (
    ProtocolCheckInput,
    SupportedModels,
)

# discover allowed model names from the pydantic model's Literal annotation
PROTOCOL_CHECK_MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"]


@pytest.mark.asyncio
@pytest.mark.protocol_check
@pytest.mark.parametrize("model_name", PROTOCOL_CHECK_MODEL_NAMES)
async def test_generate_stream_success(model_name: str, sample_aimd_protocol):
    """Test successful protocol check stream generation with mocked client."""

    if DEBUG:
        print(f"Testing Protocol Check model: {model_name}")

    # Mock the client and its response
    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Create mock streaming response
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.delta.content = "改进后的协议内容"
    mock_chunk = AsyncMock()
    mock_chunk.choices = [mock_choice]

    # Make the response async iterable
    async def mock_stream(self):
        yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create test input
    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name=model_name),
        aimd_protocol=sample_aimd_protocol,
        feedback="请优化这个协议。",
    )

    # Mock client selection
    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        # Collect streaming results
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        # Verify results
        assert collected_content != ""
        assert "改进后的协议内容" in collected_content

        # Verify client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert "messages" in call_kwargs


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_generate_stream_with_markdown_markers(sample_aimd_protocol):
    """Test stream generation with markdown code block markers."""

    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Mock response with markdown markers
    mock_chunks = [
        "这是一个改进的协议：\n\n```aimd\n",
        "# 改进的协议\n\n",
        "## 描述\n\n",
        "这是改进后的内容。\n",
        "```\n\n完成。",
    ]

    mock_response = AsyncMock()

    async def mock_stream(self):
        for content in mock_chunks:
            mock_choice = AsyncMock()
            mock_choice.delta.content = content
            mock_chunk = AsyncMock()
            mock_chunk.choices = [mock_choice]
            yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol=sample_aimd_protocol,
        feedback="请优化协议。",
    )

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        # Should extract content between ```aimd and ```
        assert "# 改进的协议" in collected_content
        assert "## 描述" in collected_content
        assert "这是改进后的内容。" in collected_content
        # Should not include markdown markers
        assert "```aimd" not in collected_content
        assert "```" not in collected_content


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_generate_stream_python_code(sample_py_model):
    """Test stream generation for Python model files."""

    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Mock response with Python code markers
    mock_chunks = [
        "这是改进的模型：\n\n```python\n",
        "from pydantic import BaseModel\n\n",
        "class VarModel(BaseModel):\n",
        "    test_field: str\n",
        "```\n",
    ]

    mock_response = AsyncMock()

    async def mock_stream(self):
        for content in mock_chunks:
            mock_choice = AsyncMock()
            mock_choice.delta.content = content
            mock_chunk = AsyncMock()
            mock_chunk.choices = [mock_choice]
            yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        py_model=sample_py_model,
        feedback="请优化模型。",
    )

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        # Should extract Python code content
        assert "from pydantic import BaseModel" in collected_content
        assert "class VarModel(BaseModel):" in collected_content
        assert "test_field: str" in collected_content


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_generate_stream_no_markers():
    """Test stream generation when no markdown markers are found."""

    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Mock response without any markers (fallback behavior)
    mock_chunks = ["这是", "直接的", "响应内容", "没有", "代码块", "标记"]

    mock_response = AsyncMock()

    async def mock_stream(self):
        for content in mock_chunks:
            mock_choice = AsyncMock()
            mock_choice.delta.content = content
            mock_chunk = AsyncMock()
            mock_chunk.choices = [mock_choice]
            yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol="# Test",
        feedback="测试。",
    )

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        # Should include all content when no markers found
        expected_content = "这是直接的响应内容没有代码块标记"
        assert collected_content == expected_content


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_generate_stream_api_error():
    """Test stream generation when API fails."""

    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol="# Test",
        feedback="测试。",
    )

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        with pytest.raises(Exception) as exc_info:
            stream_generator = generate_stream(protocol_input)
            async for _ in stream_generator:
                pass

        assert "API Error" in str(exc_info.value)


@pytest.mark.protocol_check
def test_determine_target_file_protocol_only():
    """Test target file determination with protocol only."""

    protocol_input = ProtocolCheckInput(
        aimd_protocol="# Test Protocol", feedback="测试"
    )

    target = determine_target_file(protocol_input)
    assert target == "protocol"


@pytest.mark.protocol_check
def test_determine_target_file_with_model():
    """Test target file determination with protocol and model."""

    protocol_input = ProtocolCheckInput(
        aimd_protocol="# Test Protocol",
        py_model="class VarModel: pass",
        feedback="测试",
    )

    target = determine_target_file(protocol_input)
    assert target == "model"


@pytest.mark.protocol_check
def test_determine_target_file_with_assigner():
    """Test target file determination with all files (should prioritize assigner)."""

    protocol_input = ProtocolCheckInput(
        aimd_protocol="# Test Protocol",
        py_model="class VarModel: pass",
        py_assigner="class Assigner: pass",
        feedback="测试",
    )

    target = determine_target_file(protocol_input)
    assert target == "assigner"


@pytest.mark.protocol_check
def test_determine_target_file_empty_files():
    """Test target file determination with empty/None files."""

    protocol_input = ProtocolCheckInput(
        aimd_protocol=None, py_model="", py_assigner=None, feedback="测试"
    )

    target = determine_target_file(protocol_input)
    assert target == "protocol"  # default fallback


@pytest.mark.protocol_check
def test_determine_target_file_model_priority():
    """Test that model takes priority over protocol when both exist."""

    protocol_input = ProtocolCheckInput(
        aimd_protocol="# Test Protocol",
        py_model="class VarModel: pass",
        py_assigner="",  # empty string, should be ignored
        feedback="测试",
    )

    target = determine_target_file(protocol_input)
    assert target == "model"


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_generate_stream_with_timeout():
    """Test stream generation with timeout to ensure it doesn't hang."""

    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Mock a quick response
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.delta.content = "快速响应"
    mock_chunk = AsyncMock()
    mock_chunk.choices = [mock_choice]

    async def mock_stream(self):
        yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol="# Test",
        feedback="测试",
    )

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        # Run with a timeout to ensure it completes quickly
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        try:
            async for chunk in stream_generator:
                collected_content += chunk
        except asyncio.TimeoutError:
            pytest.fail("Stream generation timed out")

        assert "快速响应" in collected_content
