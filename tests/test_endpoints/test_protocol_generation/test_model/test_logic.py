import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_generation.model.logic import generate_stream
from masterbrain.endpoints.protocol_generation.model.types import (
    ModelProtocolMessage,
    SupportedModels,
)

# 获取支持的模型名称
MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus"]


@pytest.mark.asyncio
@pytest.mark.model
@pytest.mark.parametrize("model_name", MODEL_NAMES)
async def test_generate_stream_success(model_name: str):
    """Test successful model generation with mocked client."""

    if DEBUG:
        print(f"Testing Model with model: {model_name}")

    # Mock the OpenAI client and its response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    # Mock streaming response chunks
    async def mock_chunks(self):
        chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
            "    seed_solution_volume: float = 4.75\n",
            "    hauchl4_concentration: float = 20\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create test request
    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name=model_name),
        protocol_aimd="""
# 测试协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}

## 实验步骤
{{step|test_step,1}} 测试步骤
""",
    )

    history = [{"role": "system", "content": "You are an AI assistant."}]

    # Mock the select_client function
    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Collect streamed content
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Verify content was generated
        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "BaseModel" in full_content or "class" in full_content.lower()

        # Verify client was called
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert "messages" in call_kwargs


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_empty_protocol():
    """Test stream generation with minimal protocol."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = ["class VarModel(BaseModel):\n    pass\n"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="# 简单测试"
    )

    history = [{"role": "system", "content": "Test system message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_api_error():
    """Test stream generation when API fails."""

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="测试协议"
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        with pytest.raises(Exception) as exc_info:
            content_chunks = []
            async for chunk in generate_stream(protocol_msg, history):
                content_chunks.append(chunk)

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.model
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

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="测试空响应"
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        # Should handle empty response gracefully
        full_content = "".join(content_chunks)
        assert len(full_content) == 0


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_with_thinking_enabled():
    """Test stream generation with thinking enabled."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "<thinking>\n这是思考过程，分析协议结构\n</thinking>\n",
            "from pydantic import BaseModel\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: str\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(
            name="qwen3.5-plus", enable_thinking=True, enable_search=False
        ),
        protocol_aimd="详细的协议内容",
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
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
@pytest.mark.model
async def test_generate_stream_timeout():
    """Test stream generation with timeout handling."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def slow_chunks(self):
        await asyncio.sleep(10)  # Simulate slow response
        chunk = AsyncMock()
        chunk.choices = [AsyncMock()]
        chunk.choices[0].delta.content = "延迟的model代码"
        yield chunk

    mock_response.__aiter__ = slow_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="超时测试"
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Should timeout within reasonable time
        with pytest.raises(asyncio.TimeoutError):
            content_chunks = []
            async with asyncio.timeout(5.0):
                async for chunk in generate_stream(protocol_msg, history):
                    content_chunks.append(chunk)


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_with_demo_data(demo_input_data):
    """Test stream generation using demo input data."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create protocol message from demo data
    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(**demo_input_data["use_model"]),
        protocol_aimd=demo_input_data["protocol_aimd"],
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "BaseModel" in full_content or "class" in full_content


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_history_modification():
    """Test that history is properly modified during stream generation."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = ["class VarModel(BaseModel):\n    pass\n"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="测试历史修改"
    )

    initial_history = [{"role": "system", "content": "Initial system message"}]
    history = initial_history.copy()

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
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


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_complex_protocol():
    """Test stream generation with complex protocol_aimd content."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
            "    temperature: float = Field(default=25.0, description='实验温度')\n",
            "    volume: float = Field(default=10.0, description='溶液体积')\n",
            "    concentration: float = Field(default=0.1, description='浓度')\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    complex_protocol = """
# 复杂实验协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}
温度：{{var|temperature}} °C
体积：{{var|volume}} mL
浓度：{{var|concentration}} M

## 实验步骤
{{step|prepare_solution,1}} 配制溶液
{{step|heat_solution,2}} 加热溶液到指定温度
{{check|check_temperature,1}} 检查温度是否达到目标值
{{step|add_reagent,3}} 添加试剂
{{check|check_color_change,2}} 观察颜色变化
"""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd=complex_protocol
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
        assert "BaseModel" in full_content
        assert "Field" in full_content or "temperature" in full_content


@pytest.mark.asyncio
@pytest.mark.model
async def test_generate_stream_none_protocol():
    """Test stream generation with None protocol_aimd."""

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_chunks(self):
        chunks = ["class VarModel(BaseModel):\n    pass\n"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd=None
    )

    history = [{"role": "system", "content": "System message"}]

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        content_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            content_chunks.append(chunk)

        full_content = "".join(content_chunks)
        assert len(full_content) > 0
