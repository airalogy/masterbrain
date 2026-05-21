"""
Full flow tests for AIMD (Protocol Generation) functionality.
Tests the complete AIMD pipeline from instruction input to protocol output.
"""

import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_generation.aimd.logic import generate_stream
from masterbrain.endpoints.protocol_generation.aimd.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
)
from masterbrain.endpoints.protocol_generation.aimd.types import (
    AimdProtocolMessage,
    SupportedModels,
)

# 获取支持的模型名称
AIMD_MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"]


@pytest.mark.asyncio
@pytest.mark.aimd
@pytest.mark.parametrize("model_name", AIMD_MODEL_NAMES)
async def test_full_aimd_flow(model_name: str):
    """Test the complete AIMD flow from request to protocol generation."""

    if DEBUG:
        print(f"Testing full AIMD flow with model: {model_name}")

    # Create test request
    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(
            name=model_name, enable_thinking=False, enable_search=False
        ),
        instruction="合成金三角形纳米片的实验步骤",
    )

    # Mock the client and response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    # Create realistic protocol response chunks
    async def mock_protocol_chunks(self):
        protocol_chunks = [
            "# 合成金三角形纳米片的实验协议\n\n",
            "**Objective:** 合成具有特定尺寸和形状的金三角形纳米片，用于光学和催化应用研究。\n\n",
            "## Basic Information\n\n",
            "Experimenter Name: {{var|experimenter_name}}\n",
            "Experiment Time: {{var|experiment_time}}\n",
            "Seed Solution Volume: {{var|seed_solution_volume}} mL\n",
            "Growth Solution Volume: {{var|growth_solution_volume}} mL\n\n",
            "## Experimental Steps\n\n",
            "{{step|seed_solution_preparation,1}} 种子溶液的合成\n\n",
            "Add 50 μL of HAuCl4 (20 mM) to 4.75 mL DI water.\n",
            "Add 100 μL of sodium citrate solution (10 mM).\n",
            "Note: Avoid storing the mixture above 35°C.\n\n",
            "{{step|growth_solution_preparation,2}} 生长溶液的合成\n\n",
            "Place 108 mL of CTAB (0.025 M) solution in a container.\n",
            "Add 1.5 mL of HAuCl4 (20 mM) to the CTAB solution.\n\n",
            "{{step|triangle_nanostructure_synthesis,3}} 三角形金纳米片的合成\n\n",
            "Mix 100 μL of seed solution with 900 μL of growth solution.\n",
            "Gently shake for 3 seconds.\n\n",
            "{{check|solution_color_check,1}} 溶液颜色检查\n\n",
            "Ensure that the solution has turned the expected color.\n",
        ]

        for chunk_content in protocol_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_protocol_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Mock client selection
    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Prepare history
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        # Verify the result
        full_protocol = "".join(result_chunks)
        assert len(full_protocol) > 0

        # Verify protocol structure
        assert "实验协议" in full_protocol or "protocol" in full_protocol.lower()
        assert (
            "{{var|" in full_protocol
            or "{{step|" in full_protocol
            or "{{check|" in full_protocol
        )
        assert (
            "金三角形纳米片" in full_protocol
            or "nanostructure" in full_protocol.lower()
        )

        # Verify that client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert call_kwargs["timeout"] == 1800


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_with_demo_data(demo_input_data, demo_output_data):
    """Test full flow using demo input and comparing with expected output."""

    if DEBUG:
        print("Testing full AIMD flow with demo data")

    # Create protocol message from demo data
    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(**demo_input_data["use_model"]),
        instruction=demo_input_data["instruction"],
    )

    # Mock client with demo output data
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_demo_chunks(self):
        # Split demo output into chunks for streaming
        lines = demo_output_data.split("\n")
        for line in lines:
            if line.strip():
                chunk = AsyncMock()
                chunk.choices = [AsyncMock()]
                chunk.choices[0].delta.content = line + "\n"
                yield chunk

    mock_response.__aiter__ = mock_demo_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify result contains key elements from demo output
        assert len(full_result) > 0
        assert "合成金三角形纳米片" in full_result
        assert "protocol" in full_result.lower() or "协议" in full_result

        # Verify AIMD format elements
        expected_elements = ["{{var|", "{{step|", "{{check|"]
        found_elements = [elem for elem in expected_elements if elem in full_result]
        assert len(found_elements) > 0, (
            f"No AIMD format elements found. Expected: {expected_elements}"
        )


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_with_thinking_enabled():
    """Test full flow with thinking mode enabled."""

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(
            name="qwen3.5-plus", enable_thinking=True, enable_search=False
        ),
        instruction="详细的蛋白质纯化实验协议",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_thinking_chunks(self):
        thinking_chunks = [
            "<thinking>\n",
            "用户要求生成蛋白质纯化的实验协议。\n",
            "我需要考虑色谱法、缓冲液配制、纯化步骤等。\n",
            "</thinking>\n\n",
            "# 蛋白质纯化实验协议\n\n",
            "**Objective:** 使用色谱法纯化目标蛋白质\n\n",
            "## Experimental Steps\n\n",
            "{{step|buffer_preparation,1}} 缓冲液配制\n\n",
            "详细步骤...\n",
        ]

        for chunk_content in thinking_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_thinking_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify thinking content is included
        assert "<thinking>" in full_result
        assert "</thinking>" in full_result
        assert "蛋白质纯化" in full_result


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_error_handling():
    """Test error handling in the full AIMD flow."""

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="测试错误处理"
    )

    # Mock client that raises an exception
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API连接失败")
    )

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        with pytest.raises(Exception) as exc_info:
            result_chunks = []
            async for chunk in generate_stream(protocol_msg, history):
                result_chunks.append(chunk)

        assert "API连接失败" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_long_instruction():
    """Test full flow with very long instruction."""

    # Create a long instruction
    long_instruction = (
        "生成一个详细的实验协议，包括以下内容："
        + "1. 实验目标和背景介绍；" * 20
        + "2. 详细的材料和试剂列表；" * 20
        + "3. 逐步的实验操作流程；" * 20
        + "4. 结果分析和质量控制方法。" * 20
    )

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction=long_instruction
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_long_response(self):
        response_chunks = [
            "# 详细实验协议\n\n",
            "基于您的详细要求，以下是完整的实验协议：\n\n",
            "## 实验目标\n\n",
            "根据提供的长指令生成相应的协议内容...\n",
        ]

        for chunk_content in response_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_long_response
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)
        assert len(full_result) > 0
        assert "详细实验协议" in full_result or "详细" in full_result


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_english_instruction():
    """Test full flow with English instruction."""

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        instruction="Generate a detailed experimental protocol for cell culture including media preparation, seeding, and maintenance procedures.",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_english_chunks(self):
        english_chunks = [
            "# Cell Culture Experimental Protocol\n\n",
            "**Objective:** Establish and maintain cell culture for research purposes\n\n",
            "## Basic Information\n\n",
            "Cell Line: {{var|cell_line}}\n",
            "Culture Medium: {{var|culture_medium}}\n\n",
            "## Experimental Steps\n\n",
            "{{step|media_preparation,1}} Culture Media Preparation\n\n",
            "Prepare the required culture medium according to specifications.\n\n",
            "{{step|cell_seeding,2}} Cell Seeding Procedure\n\n",
            "Detailed seeding protocol...\n",
        ]

        for chunk_content in english_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_english_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify English protocol content
        assert "Cell Culture" in full_result
        assert "Experimental Protocol" in full_result
        assert "{{var|" in full_result or "{{step|" in full_result


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_stream_timeout():
    """Test full flow behavior under streaming timeout conditions."""

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="超时测试协议"
    )

    # Mock client with very slow response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def slow_chunks(self):
        await asyncio.sleep(15)  # Simulate very slow response
        chunk = AsyncMock()
        chunk.choices = [AsyncMock()]
        chunk.choices[0].delta.content = "延迟的协议内容"
        yield chunk

    mock_response.__aiter__ = slow_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        # Should timeout within reasonable time
        with pytest.raises(asyncio.TimeoutError):
            result_chunks = []
            async with asyncio.timeout(10.0):
                async for chunk in generate_stream(protocol_msg, history):
                    result_chunks.append(chunk)


@pytest.mark.asyncio
@pytest.mark.aimd
async def test_full_flow_system_prompt_integration():
    """Test that system prompt is properly integrated in the full flow."""

    protocol_msg = AimdProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), instruction="测试系统提示集成"
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_system_chunks(self):
        chunks = ["# 测试协议\n\n基于系统提示生成的协议内容。"]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_system_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.aimd.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Start with system message
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]
        initial_history_length = len(history)

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        # Verify history was extended with user message
        assert len(history) > initial_history_length

        # Verify system message is still present
        system_messages = [msg for msg in history if msg.get("role") == "system"]
        assert len(system_messages) > 0
        assert SYSTEM_MESSAGE_PROMPT in system_messages[0]["content"]

        # Verify user message was added
        user_messages = [msg for msg in history if msg.get("role") == "user"]
        assert len(user_messages) > 0
        assert "测试系统提示集成" in user_messages[-1]["content"]
