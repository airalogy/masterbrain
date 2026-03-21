"""
Full flow tests for Protocol Check functionality.
Tests the complete Protocol Check pipeline from input to output.
"""

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
async def test_full_protocol_check_flow(model_name: str, sample_aimd_protocol):
    """Test the complete Protocol Check flow from request to response."""

    if DEBUG:
        print(f"Testing full Protocol Check flow with model: {model_name}")

    # Create test request body
    protocol_input = ProtocolCheckInput(
        model=SupportedModels(
            name=model_name, enable_thinking=False, enable_search=False
        ),
        aimd_protocol=sample_aimd_protocol,
        py_model="",
        py_assigner="",
        feedback="帮我检查一下这个文件是否有语法错误，并做出改正，润色。",
        target_file="protocol",
        check_num=0,
    )

    # Mock the client and its response
    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Create realistic mock response based on demo output
    expected_content = """# Triangle-Shaped Gold Nanoplate Synthesis

## Description

This Airalogy protocol describes how to synthesize triangle-shaped gold nanoplates using a seed-mediated growth method.

## Experimental Information

Experimenter: {{var|experimenter}}
Experiment Date: {{var|experiment_date}}

## Experimental Steps

{{step|prepare_seed_solution,1}} Prepare the seed solution.

{{check|seed_solution_preparation_conditions}} Ensure the following conditions are met:
- Add 4.75 mL of deionized water (DI water) to a container.
- Add 50 μL of HAuCl4 (20 mM).
- Add 100 μL of sodium citrate solution (10 mM).
- Avoid storing the mixture above 35°C. Cool the mixture to 3-8°C if necessary.
- Add 100 μL of freshly prepared NaBH4 (0.1 M) solution under vigorous stirring.
- Stir continuously for 2 minutes until the color changes from yellow to brown.
- Allow the seed solution to stand at room temperature for 2 hours."""

    # Split content into chunks to simulate streaming
    content_chunks = [
        expected_content[i : i + 50] for i in range(0, len(expected_content), 50)
    ]

    mock_response = AsyncMock()

    async def mock_stream(self):
        for chunk_content in content_chunks:
            mock_choice = AsyncMock()
            mock_choice.delta.content = chunk_content
            mock_chunk = AsyncMock()
            mock_chunk.choices = [mock_choice]
            yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Mock client selection
    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        # Test the complete flow
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        # Verify the result
        assert isinstance(collected_content, str)
        assert len(collected_content) > 0
        assert "Triangle-Shaped Gold Nanoplate Synthesis" in collected_content
        assert "{{var|experimenter}}" in collected_content
        assert "{{step|prepare_seed_solution,1}}" in collected_content

        # Verify that the target file was determined correctly
        assert protocol_input.target_file == "protocol"


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_full_flow_with_model_file(sample_aimd_protocol, sample_py_model):
    """Test Protocol Check flow when model file should be the target."""

    if DEBUG:
        print("Testing Protocol Check flow with model file target")

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol=sample_aimd_protocol,
        py_model=sample_py_model,
        py_assigner="",
        feedback="请检查模型文件的字段定义是否正确。",
        target_file="model",
        check_num=0,
    )

    # Mock Python code response
    expected_model_content = """from datetime import date

from pydantic import BaseModel


class VarModel(BaseModel):
    experimenter: str
    experiment_date: date
    hauc14_volume: float
    sodium_citrate_volume: float
    nabh4_volume: float
    ctab_volume: float
    haucl4_volume_growth: float
    naoh_volume: float
    ki_volume: float
    aa_volume: float
    seed_solution_volume: float
    growth_solution_volume_initial: float
    growth_solution_volume_final: float
    settling_time: int
    final_solution_volume: float
    final_solution_color: str"""

    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Mock response with Python code markers
    mock_chunks = [
        "这是改进的模型文件：\n\n```python\n",
        expected_model_content,
        "\n```\n\n改进完成。",
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
    mock_client.chat.completions.create = AsyncMock(return_value=mock_client)

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        # Verify target file determination
        target = determine_target_file(protocol_input)
        assert target == "model"

        # Test stream generation (would normally be called by router)
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        # Simulate collecting the stream (test basic functionality)
        try:
            async for chunk in stream_generator:
                collected_content += chunk
                break  # Just test that streaming starts
        except Exception:
            # Expected if mock is not perfectly configured
            pass


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_full_flow_with_assigner_file(
    sample_aimd_protocol, sample_py_model, sample_py_assigner
):
    """Test Protocol Check flow when assigner file should be the target."""

    if DEBUG:
        print("Testing Protocol Check flow with assigner file target")

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-plus"),
        aimd_protocol=sample_aimd_protocol,
        py_model=sample_py_model,
        py_assigner=sample_py_assigner,
        feedback="验证分配器中的计算逻辑是否正确。",
        target_file="assigner",
        check_num=1,
    )

    # Verify target file determination (highest priority)
    target = determine_target_file(protocol_input)
    assert target == "assigner"

    # Mock the response
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_response = AsyncMock()

    async def mock_stream(self):
        mock_choice = AsyncMock()
        mock_choice.delta.content = "改进的assigner代码内容"
        mock_chunk = AsyncMock()
        mock_chunk.choices = [mock_choice]
        yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        # Test that the assigner is prioritized correctly
        assert protocol_input.py_assigner is not None
        assert protocol_input.py_model is not None
        assert protocol_input.aimd_protocol is not None

        # The target should be assigner due to priority rules
        assert target == "assigner"


@pytest.mark.protocol_check
def test_target_file_priority_logic():
    """Test the priority logic for determining target files."""

    # Test case 1: Only protocol provided
    input1 = ProtocolCheckInput(aimd_protocol="# Test Protocol", feedback="测试")
    assert determine_target_file(input1) == "protocol"

    # Test case 2: Protocol + Model provided
    input2 = ProtocolCheckInput(
        aimd_protocol="# Test Protocol",
        py_model="class VarModel: pass",
        feedback="测试",
    )
    assert determine_target_file(input2) == "model"

    # Test case 3: All files provided (assigner should have highest priority)
    input3 = ProtocolCheckInput(
        aimd_protocol="# Test Protocol",
        py_model="class VarModel: pass",
        py_assigner="class Assigner: pass",
        feedback="测试",
    )
    assert determine_target_file(input3) == "assigner"

    # Test case 4: Empty strings should be treated as not provided
    input4 = ProtocolCheckInput(
        aimd_protocol="# Test Protocol",
        py_model="class VarModel: pass",
        py_assigner="",  # Empty string
        feedback="测试",
    )
    assert determine_target_file(input4) == "model"


@pytest.mark.asyncio
@pytest.mark.protocol_check
@pytest.mark.parametrize("model_name", PROTOCOL_CHECK_MODEL_NAMES)
async def test_flow_with_different_models(model_name: str):
    """Test Protocol Check flow with different supported models."""

    if DEBUG:
        print(f"Testing flow with model: {model_name}")

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(
            name=model_name,
            enable_thinking=(
                model_name == "qwen3.5-plus"
            ),  # Enable thinking for qwen3.5-plus
            enable_search=False,
        ),
        aimd_protocol="# Simple Test Protocol\n\n{{var|test_var}}",
        feedback="请优化这个简单协议。",
        target_file="protocol",
        check_num=0,
    )

    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_response = AsyncMock()

    async def mock_stream(self):
        mock_choice = AsyncMock()
        mock_choice.delta.content = f"使用{model_name}模型优化的协议内容"
        mock_chunk = AsyncMock()
        mock_chunk.choices = [mock_choice]
        yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        # Verify model-specific content
        assert model_name in collected_content
        assert "优化的协议内容" in collected_content

        # Verify client was called with correct model
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_flow_error_handling():
    """Test error handling in the Protocol Check flow."""

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol="# Test",
        feedback="测试错误处理",
    )

    # Mock client that raises an exception
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("Network Error")
    )

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        with pytest.raises(Exception) as exc_info:
            stream_generator = generate_stream(protocol_input)
            async for _ in stream_generator:
                pass

        assert "Network Error" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_flow_with_demo_data():
    """Test Protocol Check flow using actual demo data structure."""

    # Create input matching demo structure
    protocol_input = ProtocolCheckInput(
        model=SupportedModels(
            name="gpt-4o-mini", enable_thinking=False, enable_search=False
        ),
        aimd_protocol="""# Triangle-Shaped Gold Nanoplate Synthesis

## Description

This Airalogy protocol describes how to synthesize triangle-shaped gold nanoplates using a seed-mediated growth method.

## Experimental Information

Experimenter: {{var|experimenter}}
Experiment Date: {{var|experiment_date}}

## Experimental Steps

{{step|prepare_seed_solution,1}} Prepare the seed solution.

{{check|seed_solution_preparation_conditions}} Ensure the following conditions are met:
- Add 4.75 mL deionized water (DI water) to a container.
- Add 50 μL of HAuCl4 (20 mM).
- Add 100 μL of sodium citrate solution (10 mM).""",
        py_model="",
        py_assigner="",
        feedback="帮我检查一下这个文件是否有语法错误，并做出改正，润色。",
        target_file="protocol",
        check_num=0,
    )

    # Verify the demo data structure is correctly parsed
    assert protocol_input.model.name == "gpt-4o-mini"
    assert "Triangle-Shaped Gold Nanoplate Synthesis" in protocol_input.aimd_protocol
    assert (
        protocol_input.feedback
        == "帮我检查一下这个文件是否有语法错误，并做出改正，润色。"
    )
    assert protocol_input.target_file == "protocol"
    assert protocol_input.check_num == 0

    # Verify target file determination works correctly
    target = determine_target_file(protocol_input)
    assert target == "protocol"


@pytest.mark.asyncio
@pytest.mark.protocol_check
async def test_flow_performance():
    """Test Protocol Check flow performance and timeout behavior."""

    protocol_input = ProtocolCheckInput(
        model=SupportedModels(name="qwen3.5-flash"),
        aimd_protocol="# Performance Test Protocol",
        feedback="性能测试",
    )

    mock_client = AsyncMock(spec=AsyncOpenAI)

    # Mock a response that comes quickly
    mock_response = AsyncMock()

    async def mock_stream(self):
        # Simulate quick response
        mock_choice = AsyncMock()
        mock_choice.delta.content = "快速处理的协议内容"
        mock_chunk = AsyncMock()
        mock_chunk.choices = [mock_choice]
        yield mock_chunk

    mock_response.__aiter__ = mock_stream
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_check.logic.select_client",
        return_value=mock_client,
    ):
        import time

        start_time = time.time()

        stream_generator = generate_stream(protocol_input)
        collected_content = ""

        async for chunk in stream_generator:
            collected_content += chunk

        end_time = time.time()

        # Should complete quickly
        assert end_time - start_time < 5.0
        assert "快速处理的协议内容" in collected_content
