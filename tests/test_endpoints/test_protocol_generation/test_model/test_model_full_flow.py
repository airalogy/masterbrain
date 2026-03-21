"""
Full flow tests for Model (Protocol Generation) functionality.
Tests the complete Model pipeline from protocol_aimd input to model.py output.
"""

import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_generation.model.logic import generate_stream
from masterbrain.endpoints.protocol_generation.model.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
)
from masterbrain.endpoints.protocol_generation.model.types import (
    ModelProtocolMessage,
    SupportedModels,
)

# 获取支持的模型名称
MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus"]


@pytest.mark.asyncio
@pytest.mark.model
@pytest.mark.parametrize("model_name", MODEL_NAMES)
async def test_full_model_flow(model_name: str):
    """Test the complete Model flow from protocol_aimd to model.py generation."""

    if DEBUG:
        print(f"Testing full Model flow with model: {model_name}")

    # Create test request
    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(
            name=model_name, enable_thinking=False, enable_search=False
        ),
        protocol_aimd="""
# 金三角形纳米片合成

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}
种子溶液体积：{{var|seed_solution_volume}} mL
生长溶液体积：{{var|growth_solution_volume}} mL

## 实验步骤
{{step|seed_solution_preparation,1}} 种子溶液的合成
{{step|growth_solution_preparation,2}} 生长溶液的合成
{{step|triangle_nanostructure_synthesis,3}} 三角形金纳米片的合成
""",
    )

    # Mock the client and response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    # Create realistic model response chunks
    async def mock_model_chunks(self):
        model_chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
            "    seed_solution_volume: float = Field(default=4.75, description='种子溶液体积')\n",
            "    growth_solution_volume: float = Field(default=108.0, description='生长溶液体积')\n",
            "    hauchl4_concentration: float = Field(default=20.0, description='HAuCl4浓度')\n",
            "    ctab_concentration: float = Field(default=0.025, description='CTAB浓度')\n",
            "    reaction_temperature: float = Field(default=25.0, description='反应温度')\n",
        ]

        for chunk_content in model_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_model_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Mock client selection
    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Prepare history
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        # Verify the result
        full_model = "".join(result_chunks)
        assert len(full_model) > 0

        # Verify model structure
        assert "BaseModel" in full_model
        assert "class VarModel" in full_model or "class" in full_model
        assert "experimenter" in full_model or "UserName" in full_model

        # Verify that client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert call_kwargs["timeout"] == 1800


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_with_demo_data(demo_input_data, demo_output_data):
    """Test full flow using demo input and comparing with expected output."""

    if DEBUG:
        print("Testing full Model flow with demo data")

    # Create protocol message from demo data
    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(**demo_input_data["use_model"]),
        protocol_aimd=demo_input_data["protocol_aimd"],
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
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify result contains key elements from demo output
        assert len(full_result) > 0
        assert "BaseModel" in full_result or "VarModel" in full_result
        assert "pydantic" in full_result.lower() or "field" in full_result.lower()

        # Verify Model format elements
        expected_elements = ["class", "BaseModel", "UserName", "CurrentTime"]
        found_elements = [elem for elem in expected_elements if elem in full_result]
        assert len(found_elements) > 0, (
            f"No Model format elements found. Expected: {expected_elements}"
        )


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_with_thinking_enabled():
    """Test full flow with thinking mode enabled."""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(
            name="qwen3.5-plus", enable_thinking=True, enable_search=False
        ),
        protocol_aimd="""
# 蛋白质纯化协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}
蛋白质浓度：{{var|protein_concentration}} mg/mL

## 实验步骤
{{step|buffer_preparation,1}} 缓冲液配制
{{step|column_equilibration,2}} 柱子平衡
{{step|sample_loading,3}} 样品上样
""",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_thinking_chunks(self):
        thinking_chunks = [
            "<thinking>\n",
            "用户提供了蛋白质纯化的协议，需要生成对应的model.py。\n",
            "我需要分析协议中的变量和参数。\n",
            "</thinking>\n\n",
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
            "    protein_concentration: float = Field(description='蛋白质浓度')\n",
        ]

        for chunk_content in thinking_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_thinking_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
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
        assert "蛋白质" in full_result or "protein" in full_result.lower()


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_error_handling():
    """Test error handling in the full Model flow."""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="测试错误处理"
    )

    # Mock client that raises an exception
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API连接失败")
    )

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        with pytest.raises(Exception) as exc_info:
            result_chunks = []
            async for chunk in generate_stream(protocol_msg, history):
                result_chunks.append(chunk)

        assert "API连接失败" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_long_protocol():
    """Test full flow with very long protocol_aimd."""

    # Create a long protocol
    long_protocol = (
        """
# 详细的实验协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}
"""
        + "\n".join([f"参数{i}：{{{{var|param_{i}}}}} 单位{i}" for i in range(50)])
        + """

## 实验步骤
"""
        + "\n".join([f"{{{{step|step_{i},1}}}} 详细的实验步骤 {i}" for i in range(50)])
    )

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd=long_protocol
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_long_response(self):
        response_chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
        ]
        # Add many parameter fields
        for i in range(10):
            response_chunks.append(
                f"    param_{i}: float = Field(description='参数{i}')\n"
            )

        for chunk_content in response_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_long_response
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)
        assert len(full_result) > 0
        assert "BaseModel" in full_result
        assert "param_" in full_result


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_english_protocol():
    """Test full flow with English protocol_aimd."""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="""
# Cell Culture Protocol

## Basic Information
Experimenter: {{var|experimenter}}
Experiment Time: {{var|experiment_time}}
Cell Line: {{var|cell_line}}
Medium Volume: {{var|medium_volume}} mL

## Experimental Steps
{{step|media_preparation,1}} Culture Media Preparation
{{step|cell_seeding,2}} Cell Seeding Procedure
{{step|incubation,3}} Cell Incubation
""",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_english_chunks(self):
        english_chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
            "    cell_line: str = Field(description='Cell line name')\n",
            "    medium_volume: float = Field(description='Medium volume in mL')\n",
        ]

        for chunk_content in english_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_english_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify English model content
        assert "Cell" in full_result or "cell" in full_result
        assert "BaseModel" in full_result
        assert "cell_line" in full_result or "medium_volume" in full_result


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_stream_timeout():
    """Test full flow behavior under streaming timeout conditions."""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd="超时测试协议"
    )

    # Mock client with very slow response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def slow_chunks(self):
        await asyncio.sleep(15)  # Simulate very slow response
        chunk = AsyncMock()
        chunk.choices = [AsyncMock()]
        chunk.choices[0].delta.content = "class VarModel(BaseModel):\n    pass\n"
        yield chunk

    mock_response.__aiter__ = slow_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
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
@pytest.mark.model
async def test_full_flow_system_prompt_integration():
    """Test that system prompt is properly integrated in the full flow."""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="测试系统提示集成",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_system_chunks(self):
        chunks = [
            "from pydantic import BaseModel\n\n",
            "class VarModel(BaseModel):\n",
            "    # 基于系统提示生成的模型代码\n",
            "    pass\n",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_system_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
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


@pytest.mark.asyncio
@pytest.mark.model
async def test_full_flow_complex_aimd_structure():
    """Test full flow with complex AIMD structure including nested variables."""

    complex_protocol = """
# 复杂多步骤合成协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}
实验温度：{{var|temperature}} °C
pH值：{{var|ph_value}}

## 反应物信息
反应物A浓度：{{var|reactant_a_concentration}} M
反应物B浓度：{{var|reactant_b_concentration}} M
催化剂用量：{{var|catalyst_amount}} mg
溶剂体积：{{var|solvent_volume}} mL

## 实验步骤
{{step|prepare_reactants,1}} 准备反应物
{{step|mix_solutions,2}} 混合溶液
{{check|check_temperature,1}} 检查温度
{{step|add_catalyst,3}} 添加催化剂
{{check|monitor_ph,2}} 监控pH值
{{step|heat_reaction,4}} 加热反应
{{check|observe_color,3}} 观察颜色变化
{{step|cool_down,5}} 冷却反应
{{step|purification,6}} 产物纯化
"""

    protocol_msg = ModelProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"), protocol_aimd=complex_protocol
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_complex_chunks(self):
        complex_chunks = [
            "from pydantic import BaseModel, Field\n\n",
            "from airalogy.built_in_types import CurrentTime, UserName\n\n",
            "class VarModel(BaseModel):\n",
            "    experimenter: UserName\n",
            "    experiment_time: CurrentTime\n",
            "    temperature: float = Field(description='实验温度')\n",
            "    ph_value: float = Field(description='pH值')\n",
            "    reactant_a_concentration: float = Field(description='反应物A浓度')\n",
            "    reactant_b_concentration: float = Field(description='反应物B浓度')\n",
            "    catalyst_amount: float = Field(description='催化剂用量')\n",
            "    solvent_volume: float = Field(description='溶剂体积')\n",
        ]

        for chunk_content in complex_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_complex_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.model.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify complex model structure
        assert "BaseModel" in full_result
        assert "temperature" in full_result
        assert "concentration" in full_result
        assert "catalyst" in full_result or "catalyst_amount" in full_result
        assert "Field" in full_result
        assert "description" in full_result
