"""
Full flow tests for Assigner (Protocol Generation) functionality.
Tests the complete Assigner pipeline from protocol input to assigner.py output.
"""

import asyncio
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.configs import DEBUG
from masterbrain.endpoints.protocol_generation.assigner.logic import generate_stream
from masterbrain.endpoints.protocol_generation.assigner.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
)
from masterbrain.endpoints.protocol_generation.assigner.types import (
    AssignerProtocolMessage,
    SupportedModels,
)

# Get supported model names
ASSIGNER_MODEL_NAMES = ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"]


@pytest.mark.asyncio
@pytest.mark.assigner
@pytest.mark.parametrize("model_name", ASSIGNER_MODEL_NAMES)
async def test_full_assigner_flow(model_name: str):
    """Test the complete Assigner flow from request to assigner.py generation."""

    if DEBUG:
        print(f"Testing full Assigner flow with model: {model_name}")

    # Create test request
    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(
            name=model_name, enable_thinking=False, enable_search=False
        ),
        protocol_aimd="""
# Gold Triangular Nanoplate Synthesis Protocol

## Basic Information

Experimenter: {{var|experimenter}}
Experiment Time: {{var|experiment_time}}

## Experimental Steps

{{step|prepare_growth_solution,1}} Prepare growth solution.
{{step|add_ctab,1}} Place {{var|growth_volume_ctab}} mL of CTAB solution in container.
{{step|add_haucl4,1}} Add {{var|growth_volume_haucl4}} mL HAuCl4 solution.
{{step|add_naoh,1}} Add {{var|growth_volume_naoh}} mL NaOH solution.
""",
        protocol_model="""from datetime import datetime
from pydantic import BaseModel

class VarModel(BaseModel):
    experimenter: str
    experiment_time: datetime
    growth_volume_ctab: float = 108.0
    growth_volume_haucl4: float = 1.5
    growth_volume_naoh: float = 0.6
    growth_total_volume: float
""",
    )

    # Mock the client and response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    # Create realistic assigner response chunks
    async def mock_assigner_chunks(self):
        assigner_chunks = [
            "I will generate an assigner.py file for you:\n\n",
            "```python\n",
            "from airalogy.assigner import (\n",
            "    AssignerBase,\n",
            "    AssignerResult,\n",
            "    assigner,\n",
            ")\n\n\n",
            "class Assigner(AssignerBase):\n",
            "    @assigner(\n",
            '        assigned_fields=["growth_total_volume"],\n',
            "        dependent_fields=[\n",
            '            "growth_volume_ctab",\n',
            '            "growth_volume_haucl4",\n',
            '            "growth_volume_naoh",\n',
            "        ],\n",
            '        mode="auto",\n',
            "    )\n",
            "    @staticmethod\n",
            "    def calculate_growth_total_volume(dependent_data: dict) -> AssignerResult:\n",
            '        growth_volume_ctab = dependent_data["growth_volume_ctab"]\n',
            '        growth_volume_haucl4 = dependent_data["growth_volume_haucl4"]\n',
            '        growth_volume_naoh = dependent_data["growth_volume_naoh"]\n',
            "        growth_total_volume = (\n",
            "            growth_volume_ctab + \n",
            "            growth_volume_haucl4 + \n",
            "            growth_volume_naoh\n",
            "        )\n",
            "        return AssignerResult(\n",
            "            assigned_fields={\n",
            '                "growth_total_volume": round(growth_total_volume, 2),\n',
            "            },\n",
            "        )\n",
            "```",
        ]

        for chunk_content in assigner_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_assigner_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Mock client selection
    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        # Prepare history
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        # Verify the result
        full_assigner = "".join(result_chunks)
        assert len(full_assigner) > 0

        # Verify assigner.py structure
        assert "class Assigner" in full_assigner
        assert "AssignerBase" in full_assigner
        assert "@assigner(" in full_assigner
        assert "assigned_fields" in full_assigner
        assert "dependent_fields" in full_assigner
        assert "AssignerResult" in full_assigner
        assert "growth_total_volume" in full_assigner

        # Verify that client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert call_kwargs["stream"] is True
        assert call_kwargs["timeout"] == 1800


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_full_flow_with_demo_data(demo_input_data, demo_output_data):
    """Test full flow using demo input and comparing with expected output."""

    if DEBUG:
        print("Testing full Assigner flow with demo data")

    # Create protocol message from demo data
    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(**demo_input_data["use_model"]),
        protocol_aimd=demo_input_data["protocol_aimd"],
        protocol_model=demo_input_data["protocol_model"],
    )

    # Mock client with demo output data
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_demo_chunks(self):
        # Add code block markers to demo output
        chunks = [
            "Generated assigner.py file:\n\n",
            "```python\n",
            demo_output_data,
            "```",
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_demo_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify result contains key elements from demo output
        assert len(full_result) > 0
        assert "class Assigner" in full_result
        assert "AssignerBase" in full_result
        assert "calculate_growth_total_volume" in full_result
        assert "growth_volume_ctab" in full_result
        assert "growth_volume_haucl4" in full_result


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_full_flow_with_thinking_enabled():
    """Test full flow with thinking mode enabled."""

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(
            name="qwen3.5-plus", enable_thinking=True, enable_search=False
        ),
        protocol_aimd="""
# Complex Experimental Protocol

## Experimental Steps

{{step|complex_calculation,1}} Complex calculation step.
{{var|input_value}} Input value.
{{var|calculated_result}} Calculated result.
""",
        protocol_model="""from pydantic import BaseModel

class VarModel(BaseModel):
    input_value: float
    calculated_result: float
""",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_thinking_chunks(self):
        thinking_chunks = [
            "<thinking>\n",
            "User requests generating an assigner.py file.\n",
            "I need to analyze the protocol_aimd and protocol_model content.\n",
            "Identify fields that need calculation and dependencies.\n",
            "</thinking>\n\n",
            "```python\n",
            "from airalogy.assigner import (\n",
            "    AssignerBase,\n",
            "    AssignerResult,\n",
            "    assigner,\n",
            ")\n\n",
            "class Assigner(AssignerBase):\n",
            "    @assigner(\n",
            '        assigned_fields=["calculated_result"],\n',
            '        dependent_fields=["input_value"],\n',
            '        mode="auto",\n',
            "    )\n",
            "    @staticmethod\n",
            "    def calculate_result(dependent_data: dict) -> AssignerResult:\n",
            '        input_value = dependent_data["input_value"]\n',
            "        calculated_result = input_value * 2.0\n",
            "        return AssignerResult(\n",
            "            assigned_fields={\n",
            '                "calculated_result": round(calculated_result, 2),\n',
            "            },\n",
            "        )\n",
            "```",
        ]

        for chunk_content in thinking_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_thinking_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify thinking content is filtered out but code is preserved
        assert "<thinking>" not in full_result
        assert "</thinking>" not in full_result
        assert "class Assigner" in full_result
        assert "calculate_result" in full_result


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_full_flow_error_handling():
    """Test error handling in the full Assigner flow."""

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test error handling",
        protocol_model="class VarModel(BaseModel): test_var: str",
    )

    # Mock client that raises an exception
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API connection failed")
    )

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        with pytest.raises(Exception) as exc_info:
            result_chunks = []
            async for chunk in generate_stream(protocol_msg, history):
                result_chunks.append(chunk)

        assert "API connection failed" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_full_flow_complex_protocol():
    """Test full flow with complex protocol containing multiple calculations."""

    complex_aimd = """
# Complex Nanomaterial Synthesis Protocol

## Basic Information

Experimenter: {{var|experimenter}}
Experiment Time: {{var|experiment_time}}

## Solution Preparation

{{step|prepare_solution_a,1}} Prepare solution A.
Volume: {{var|volume_a}} mL
Concentration: {{var|concentration_a}} M

{{step|prepare_solution_b,2}} Prepare solution B.
Volume: {{var|volume_b}} mL
Concentration: {{var|concentration_b}} M

{{step|calculate_total,3}} Calculate total volume and concentration.
Total Volume: {{var|total_volume}} mL
Total Concentration: {{var|total_concentration}} M

## Quality Control

{{check|verify_calculations,1}} Verify calculation results.
"""

    complex_model = """from datetime import datetime
from pydantic import BaseModel

class VarModel(BaseModel):
    experimenter: str
    experiment_time: datetime
    volume_a: float = 50.0
    concentration_a: float = 0.1
    volume_b: float = 30.0
    concentration_b: float = 0.2
    total_volume: float
    total_concentration: float
"""

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd=complex_aimd,
        protocol_model=complex_model,
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_complex_chunks(self):
        complex_chunks = [
            "```python\n",
            "from airalogy.assigner import (\n",
            "    AssignerBase,\n",
            "    AssignerResult,\n",
            "    assigner,\n",
            ")\n\n",
            "class Assigner(AssignerBase):\n",
            "    @assigner(\n",
            '        assigned_fields=["total_volume", "total_concentration"],\n',
            "        dependent_fields=[\n",
            '            "volume_a", "concentration_a",\n',
            '            "volume_b", "concentration_b"\n',
            "        ],\n",
            '        mode="auto",\n',
            "    )\n",
            "    @staticmethod\n",
            "    def calculate_totals(dependent_data: dict) -> AssignerResult:\n",
            '        volume_a = dependent_data["volume_a"]\n',
            '        concentration_a = dependent_data["concentration_a"]\n',
            '        volume_b = dependent_data["volume_b"]\n',
            '        concentration_b = dependent_data["concentration_b"]\n',
            "        \n",
            "        total_volume = volume_a + volume_b\n",
            "        total_concentration = (\n",
            "            (volume_a * concentration_a + volume_b * concentration_b) / total_volume\n",
            "        )\n",
            "        \n",
            "        return AssignerResult(\n",
            "            assigned_fields={\n",
            '                "total_volume": round(total_volume, 2),\n',
            '                "total_concentration": round(total_concentration, 4),\n',
            "            },\n",
            "        )\n",
            "```",
        ]

        for chunk_content in complex_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_complex_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify complex assigner structure
        assert "class Assigner" in full_result
        assert "calculate_totals" in full_result
        assert "total_volume" in full_result
        assert "total_concentration" in full_result
        assert len(full_result) > 0


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_full_flow_english_protocol():
    """Test full flow with English protocol."""

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="""
# Protein Purification Protocol

## Experimental Steps

{{step|prepare_buffer,1}} Prepare purification buffer.
Buffer volume: {{var|buffer_volume}} mL
Buffer concentration: {{var|buffer_concentration}} M

{{step|calculate_total,2}} Calculate total buffer requirements.
Total volume needed: {{var|total_buffer_volume}} mL
""",
        protocol_model="""from pydantic import BaseModel

class VarModel(BaseModel):
    buffer_volume: float = 100.0
    buffer_concentration: float = 0.05
    total_buffer_volume: float
""",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_english_chunks(self):
        english_chunks = [
            "```python\n",
            "from airalogy.assigner import (\n",
            "    AssignerBase,\n",
            "    AssignerResult,\n",
            "    assigner,\n",
            ")\n\n",
            "class Assigner(AssignerBase):\n",
            "    @assigner(\n",
            '        assigned_fields=["total_buffer_volume"],\n',
            '        dependent_fields=["buffer_volume"],\n',
            '        mode="auto",\n',
            "    )\n",
            "    @staticmethod\n",
            "    def calculate_total_buffer(dependent_data: dict) -> AssignerResult:\n",
            '        buffer_volume = dependent_data["buffer_volume"]\n',
            "        total_buffer_volume = buffer_volume * 1.2  # 20% extra\n",
            "        return AssignerResult(\n",
            "            assigned_fields={\n",
            '                "total_buffer_volume": round(total_buffer_volume, 2),\n',
            "            },\n",
            "        )\n",
            "```",
        ]

        for chunk_content in english_chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_english_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
        return_value=mock_client,
    ):
        history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

        result_chunks = []
        async for chunk in generate_stream(protocol_msg, history):
            result_chunks.append(chunk)

        full_result = "".join(result_chunks)

        # Verify English protocol content
        assert "class Assigner" in full_result
        assert "calculate_total_buffer" in full_result
        assert "buffer_volume" in full_result


@pytest.mark.asyncio
@pytest.mark.assigner
async def test_full_flow_stream_timeout():
    """Test full flow behavior under streaming timeout conditions."""

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Timeout test protocol",
        protocol_model="class VarModel(BaseModel): test_var: str",
    )

    # Mock client with very slow response
    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def slow_chunks(self):
        await asyncio.sleep(15)  # Simulate very slow response
        chunk = AsyncMock()
        chunk.choices = [AsyncMock()]
        chunk.choices[0].delta.content = "```python\nclass Assigner: pass\n```"
        yield chunk

    mock_response.__aiter__ = slow_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
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
@pytest.mark.assigner
async def test_full_flow_system_prompt_integration():
    """Test that system prompt is properly integrated in the full flow."""

    protocol_msg = AssignerProtocolMessage(
        use_model=SupportedModels(name="qwen3.5-flash"),
        protocol_aimd="# Test system prompt integration",
        protocol_model="class VarModel(BaseModel): test_var: str",
    )

    mock_client = AsyncMock()
    mock_response = AsyncMock()

    async def mock_system_chunks(self):
        chunks = [
            "```python\n# Assigner generated based on system prompt\nclass Assigner: pass\n```"
        ]
        for chunk_content in chunks:
            chunk = AsyncMock()
            chunk.choices = [AsyncMock()]
            chunk.choices[0].delta.content = chunk_content
            yield chunk

    mock_response.__aiter__ = mock_system_chunks
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch(
        "masterbrain.endpoints.protocol_generation.assigner.logic.stream_generator.select_client",
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

        # Verify user message was added with protocol content
        user_messages = [msg for msg in history if msg.get("role") == "user"]
        assert len(user_messages) > 0
        assert "Test system prompt integration" in user_messages[-1]["content"]
