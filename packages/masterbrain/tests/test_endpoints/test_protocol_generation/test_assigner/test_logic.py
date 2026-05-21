import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_generation.assigner.logic import generate_stream
from masterbrain.endpoints.protocol_generation.assigner.types import (
    AssignerProtocolMessage,
    SupportedModels,
)

# Get supported model names
ASSIGNER_MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"]


@pytest.mark.asyncio
@pytest.mark.assigner
@pytest.mark.parametrize("model_name", ASSIGNER_MODEL_NAMES)
async def test_generate_stream_success(model_name: str):
    """Test successful assigner generation with mocked client."""

    if DEBUG:
        print(f"Testing Assigner model: {model_name}")

    # Mock the OpenAI client and its response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    # Mock streaming response chunks with code block markers
    async def mock_chunks(self):
        chunks = [
            "I will generate an assigner.py file for you:\n\n",
            "```python\n",
            "from airalogy.assigner import (\n",
            "    AssignerBase,\n",
            "    AssignerResult,\n",
            "    assigner,\n",
            ")\n\n\n",
            "class Assigner(AssignerBase):\n",
            "    @assigner(\n",
            '        assigned_fields=["total_volume"],\n',
            '        dependent_fields=["volume_a", "volume_b"],\n',
            '        mode="auto",\n',
            "    )\n",
            "    @staticmethod\n",
            "    def calculate_total_volume(dependent_data: dict) -> AssignerResult:\n",
            '        volume_a = dependent_data["volume_a"]\n',
            '        volume_b = dependent_data["volume_b"]\n',
            "        total_volume = volume_a + volume_b\n",
            "        return AssignerResult(\n",
            "            assigned_fields={\n",
            '                "total_volume": round(total_volume, 2),\n',
            "            },\n",
            "        )\n",
            "```",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create test request
    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name=model_name),
        protocol_aimd="# Test Protocol\n{{var|volume_a}}\n{{var|volume_b}}",
        protocol_model="class VarModel(BaseModel):\n    volume_a: float\n    volume_b: float",
    )

    history = [{"role": "system", "content": "You are an AI assistant."}]

    # Mock the select_client function
    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Collect streamed content
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Verify content was generated
        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "class Assigner" in full_content
        assert "AssignerBase" in full_content
        assert "def calculate_" in full_content

        # Verify client was called
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert "messages" in call_kwargs


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_code_block_filtering():
    """Test stream generation with code block marker filtering."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks_with_markers(self):
        chunks = [
            "This is prefix text that should be filtered out\n",
            "```python\n",  # Start marker - should be filtered
            "# This is the required code content\n",
            "from airalogy.assigner import AssignerBase\n",
            "class Assigner(AssignerBase):\n",
            "    pass\n",
            "```",  # End marker - should stop here
            "This is suffix text that should be filtered out",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks_with_markers
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "Test system message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)

        # Should contain the code content but not the markers or surrounding text
        assert "# This is the required code content" in full_content
        assert "class Assigner(AssignerBase):" in full_content
        assert "```python" not in full_content
        assert "```" not in full_content
        assert "prefix text" not in full_content
        assert "suffix text" not in full_content


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_no_markers_fallback():
    """Test stream generation fallback when no code markers are found."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks_no_markers(self):
        # No markers, should fall back to streaming all content after max_tokens_wait
        chunks = [
            "from airalogy.assigner import AssignerBase\n",
            "class Assigner(AssignerBase):\n",
            "    pass\n",
        ] * 5  # Repeat to exceed max_tokens_wait
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks_no_markers
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "Test system message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "AssignerBase" in full_content


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_api_error():
    """Test stream generation when API fails."""

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        with pytest.raises(Exception) as exc_info:
            content_chunks = []
            async for chunk in generate_stream(protocol_msg, history):
                content_chunks.append(chunk)

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.assigner
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

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Should handle empty response gracefully
        full_content = "".join(content_chunks)
        assert len(full_content) == 0


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_with_thinking_enabled():
    """Test stream generation with thinking enabled."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "<thinking>\nThis requires generating an assigner file\n</thinking>\n",
            "```python\n",
            "from airalogy.assigner import AssignerBase\n",
            "class Assigner(AssignerBase):\n",
            "    pass\n",
            "```",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(
            name="qwen3.5-plus", enable_thinking=True, enable_search=False
        ),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        # Should contain only the code content, not the thinking
        assert "AssignerBase" in full_content
        assert "<thinking>" not in full_content


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_timeout():
    """Test stream generation with timeout handling."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def slow_chunks(self):
        await asyncio.sleep(10)  # Simulate slow response
        chunk = AsyncMock()
        chunk.choices = [AsyncMock()]
        chunk.choices[0].delta.content = "class Assigner(AssignerBase): pass"
        yield chunk

    mock_response.__aiter__ = slow_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Should timeout within reasonable time
        with pytest.raises(asyncio.TimeoutError):
            content_chunks = []
            async with asyncio.timeout(5.0):
                async for chunk in generate_stream(protocol_msg, history):
                    content_chunks.append(chunk)


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_with_demo_data(demo_input_data):
    """Test stream generation using demo input data."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "```python\n",
            "from airalogy.assigner import AssignerBase\n",
            "# Generated from demo data\n",
            "class Assigner(AssignerBase):\n",
            "    pass\n",
            "```",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create protocol message from demo data
    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(**demo_input_data["use_model"]),
        protocol_aimd=demo_input_data["protocol_aimd"],
        protocol_model=demo_input_data["protocol_model"],
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "AssignerBase" in full_content


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_history_modification():
    """Test that history is properly modified during stream generation."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = ["```python\nclass Assigner: pass\n```"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    initial_history = [{"role": "system", "content": "Initial system message"}]
    history = initial_history.copy()

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
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
        # User message should contain the protocol content
        assert "Test Protocol" in user_messages[-1]["content"]


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_generate_stream_partial_code_blocks():
    """Test handling of partial code block markers in streaming."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_partial_chunks(self):
        # Simulate code markers being split across chunks
        chunks = [
            "Here is the code:\n",
            "```py",
            "thon\n",  # Complete the start marker
            "class Assigner:\n",
            "    pass\n```",  # End marker in same chunk as last content
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_partial_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test Protocol",
        protocol_model="class VarModel(BaseModel): pass",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        # Should extract the code content properly
        assert "class Assigner:" in full_content
        assert "pass" in full_content
        # Should not contain the markers
        assert "```python" not in full_content
        assert "```" not in full_content
