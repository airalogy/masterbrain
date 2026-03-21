"""
Tests for Field Input Full Flow

This module tests the complete field input workflow from request to response.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from masterbrain.endpoints.chat.field_input.logic.slot_service import (
    handle_slot_extraction,
)
from masterbrain.endpoints.chat.field_input.types import (
    FieldInputRequest,
    FieldInputResponse,
    ModelConfig,
    SlotOperation,
    SlotUpdateResult,
    SupportedModels,
)

# Define supported model names directly for Python 3.12 compatibility
MODEL_NAMES = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo",
    "qwen-max",
    "qwen3-max",
    "qwen3.5-plus",
    "qwen3.5-flash",
]

# Representative subset for mocked tests: 2 OpenAI + 2 Qwen
MOCK_TEST_MODELS = ["gpt-4o-mini", "gpt-4.1", "qwen3-max", "qwen3.5-flash"]


@pytest.mark.field_input
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model_name", MOCK_TEST_MODELS
)  # 2 OpenAI + 2 Qwen, all mocked
async def test_full_field_input_flow_text_input(model_name: str):
    """Test complete field input flow with text input."""
    # Create a realistic request
    request = FieldInputRequest(
        chat_id="test_chat_123",
        user_id="test_user",
        model=ModelConfig(name=model_name, temperature=0.0, max_tokens=512),
        history=[
            {
                "role": "user",
                "content": "forward_primer_volume是50；reverse_primer_volume是150。",
            }
        ],
        scenario={
            "protocol_schema": {
                "$defs": {
                    "ExperimentResult": {
                        "description": "Model for experiment result.",
                        "properties": {
                            "experiment_identifier": {
                                "title": "Experiment Identifier",
                                "type": "string",
                            },
                            "experiment_success": {
                                "title": "Experiment Success",
                                "type": "boolean",
                            },
                        },
                        "required": ["experiment_identifier", "experiment_success"],
                        "title": "ExperimentResult",
                        "type": "object",
                    }
                },
                "description": "Test Protocol Schema",
                "properties": {
                    "forward_primer_volume": {
                        "description": "Volume of forward primer",
                        "title": "Forward Primer Volume",
                        "type": "number",
                    },
                    "reverse_primer_volume": {
                        "description": "Volume of reverse primer",
                        "title": "Reverse Primer Volume",
                        "type": "number",
                    },
                    "experiment_identifier": {
                        "description": "Unique identifier for the experiment",
                        "title": "Experiment Identifier",
                        "type": "string",
                    },
                },
                "required": [
                    "forward_primer_volume",
                    "reverse_primer_volume",
                    "experiment_identifier",
                ],
                "title": "TestProtocol",
                "type": "object",
            }
        },
    )

    # Mock the SlotMemory.generate_response method
    with patch(
        "masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory"
    ) as mock_memory_class:
        mock_memory = Mock()

        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(
                required=[
                    SlotOperation(
                        operation="update",
                        rf_name="forward_primer_volume",
                        rf_value="50",
                    ),
                    SlotOperation(
                        operation="update",
                        rf_name="reverse_primer_volume",
                        rf_value="150",
                    ),
                    SlotOperation(
                        operation="update",
                        rf_name="experiment_identifier",
                        rf_value="EXP_001",
                    ),
                ]
            )

        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory

        # Mock the prompt creation
        with patch(
            "masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt"
        ) as mock_prompt:
            mock_prompt.return_value = "test prompt template"

            result = await handle_slot_extraction(request)

    # Verify the complete response structure
    assert isinstance(result, FieldInputResponse)
    assert result.chat_id == "test_chat_123"
    assert result.user_id == "test_user"
    assert result.model.name == model_name
    assert result.model.temperature == 0.0
    assert result.model.max_tokens == 512

    # Verify history structure
    assert len(result.history) == 2  # user message + assistant response
    assert result.history[0]["role"] == "user"
    assert (
        result.history[0]["content"]
        == "forward_primer_volume是50；reverse_primer_volume是150。"
    )

    # Verify assistant response with tool calls
    assistant_message = result.history[-1]
    assert assistant_message["role"] == "assistant"
    assert assistant_message["content"] is None
    assert "tool_calls" in assistant_message
    assert len(assistant_message["tool_calls"]) == 1

    # Verify tool call structure
    tool_call = assistant_message["tool_calls"][0]
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "slot_filling"
    assert "id" in tool_call
    assert tool_call["id"].startswith("id_sf_")

    # Parse and verify tool call arguments
    arguments = json.loads(tool_call["arguments"])
    assert "operations" in arguments
    assert len(arguments["operations"]) == 3

    # Verify all expected operations are present
    operation_names = [op["rf_name"] for op in arguments["operations"]]
    assert "forward_primer_volume" in operation_names
    assert "reverse_primer_volume" in operation_names
    assert "experiment_identifier" in operation_names

    # Verify operation values
    for operation in arguments["operations"]:
        assert operation["operation"] == "update"
        if operation["rf_name"] == "forward_primer_volume":
            assert operation["rf_value"] == "50"
        elif operation["rf_name"] == "reverse_primer_volume":
            assert operation["rf_value"] == "150"
        elif operation["rf_name"] == "experiment_identifier":
            assert operation["rf_value"] == "EXP_001"

    # Verify scenario preservation
    assert "protocol_schema" in result.scenario
    assert result.scenario["protocol_schema"]["title"] == "TestProtocol"


@pytest.mark.field_input
@pytest.mark.asyncio
@pytest.mark.parametrize("model_name", MOCK_TEST_MODELS)  # 2 OpenAI + 2 Qwen, all mocked
async def test_full_field_input_flow_image_input(model_name: str):
    """Test complete field input flow with image input."""
    request = FieldInputRequest(
        chat_id="test_chat_image",
        user_id="test_user",
        model=ModelConfig(name=model_name, temperature=0.0, max_tokens=1024),
        history=[
            {"role": "user", "content": "https://example.com/experiment_image.png"}
        ],
        scenario={
            "protocol_schema": {
                "properties": {
                    "cell_count": {
                        "description": "Number of cells counted",
                        "title": "Cell Count",
                        "type": "integer",
                    },
                    "cell_density": {
                        "description": "Cell density per square millimeter",
                        "title": "Cell Density",
                        "type": "number",
                    },
                },
                "required": ["cell_count", "cell_density"],
                "title": "Cell Counting Protocol",
                "type": "object",
            }
        },
    )

    # Mock the SlotMemory.generate_response method
    with patch(
        "masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory"
    ) as mock_memory_class:
        mock_memory = Mock()

        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(
                required=[
                    SlotOperation(
                        operation="update", rf_name="cell_count", rf_value="150"
                    ),
                    SlotOperation(
                        operation="update", rf_name="cell_density", rf_value="75.5"
                    ),
                ]
            )

        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory

        # Mock the prompt creation
        with patch(
            "masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt"
        ) as mock_prompt:
            mock_prompt.return_value = "test prompt template"

            result = await handle_slot_extraction(request)

    # Verify the response
    assert isinstance(result, FieldInputResponse)
    assert result.chat_id == "test_chat_image"
    assert result.model.name == model_name

    # Verify tool calls contain the expected operations
    assistant_message = result.history[-1]
    tool_call = assistant_message["tool_calls"][0]
    arguments = json.loads(tool_call["arguments"])

    operation_names = [op["rf_name"] for op in arguments["operations"]]
    assert "cell_count" in operation_names
    assert "cell_density" in operation_names


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_full_field_input_flow_empty_schema():
    """Test field input flow with empty protocol schema."""
    request = FieldInputRequest(
        chat_id="test_chat_empty",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[
            {"role": "user", "content": "This is a test message with no schema fields."}
        ],
        scenario={
            "protocol_schema": {
                "properties": {},
                "required": [],
                "title": "Empty Protocol",
                "type": "object",
            }
        },
    )

    # Mock the SlotMemory.generate_response method
    with patch(
        "masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory"
    ) as mock_memory_class:
        mock_memory = Mock()

        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(required=[])

        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory

        # Mock the prompt creation
        with patch(
            "masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt"
        ) as mock_prompt:
            mock_prompt.return_value = "test prompt template"

            result = await handle_slot_extraction(request)

    # Verify the response
    assert isinstance(result, FieldInputResponse)
    assert len(result.history) == 2

    # Verify no operations in tool calls
    assistant_message = result.history[-1]
    tool_call = assistant_message["tool_calls"][0]
    arguments = json.loads(tool_call["arguments"])
    assert len(arguments["operations"]) == 0


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_full_field_input_flow_multiple_history_messages():
    """Test field input flow with multiple conversation history messages."""
    request = FieldInputRequest(
        chat_id="test_chat_multi",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[
            {
                "role": "user",
                "content": "Hello, I want to record some experiment data.",
            },
            {
                "role": "assistant",
                "content": "I can help you record experiment data. What would you like to record?",
            },
            {"role": "user", "content": "The temperature was 37°C and the pH was 7.4."},
        ],
        scenario={
            "protocol_schema": {
                "properties": {
                    "temperature": {
                        "description": "Temperature in Celsius",
                        "title": "Temperature",
                        "type": "number",
                    },
                    "ph": {"description": "pH value", "title": "pH", "type": "number"},
                },
                "required": ["temperature", "ph"],
                "title": "Basic Experiment Protocol",
                "type": "object",
            }
        },
    )

    # Mock the SlotMemory.generate_response method
    with patch(
        "masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory"
    ) as mock_memory_class:
        mock_memory = Mock()

        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(
                required=[
                    SlotOperation(
                        operation="update", rf_name="temperature", rf_value="37"
                    ),
                    SlotOperation(operation="update", rf_name="ph", rf_value="7.4"),
                ]
            )

        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory

        # Mock the prompt creation
        with patch(
            "masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt"
        ) as mock_prompt:
            mock_prompt.return_value = "test prompt template"

            result = await handle_slot_extraction(request)

    # Verify the response
    assert isinstance(result, FieldInputResponse)
    assert len(result.history) == 4  # 3 original + 1 new assistant message

    # Verify the new assistant message contains tool calls
    assistant_message = result.history[-1]
    assert assistant_message["role"] == "assistant"
    assert "tool_calls" in assistant_message

    # Verify tool call operations
    tool_call = assistant_message["tool_calls"][0]
    arguments = json.loads(tool_call["arguments"])

    operation_names = [op["rf_name"] for op in arguments["operations"]]
    assert "temperature" in operation_names
    assert "ph" in operation_names


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_full_field_input_flow_error_handling():
    """Test field input flow error handling."""
    request = FieldInputRequest(
        chat_id="test_chat_error",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[{"role": "user", "content": "This should cause an error."}],
        scenario={
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    )

    # Mock SlotMemory to raise an exception
    with patch(
        "masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory"
    ) as mock_memory_class:
        mock_memory_class.side_effect = Exception("Simulated error in slot extraction")

        with pytest.raises(Exception, match="Simulated error in slot extraction"):
            await handle_slot_extraction(request)


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_full_field_input_flow_with_scenario_metadata():
    """Test field input flow with additional scenario metadata."""
    request = FieldInputRequest(
        chat_id="test_chat_metadata",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[{"role": "user", "content": "Record the experiment results."}],
        scenario={
            "protocol_schema": {
                "properties": {
                    "result": {
                        "description": "Experiment result",
                        "title": "Result",
                        "type": "string",
                    }
                },
                "required": ["result"],
                "title": "Simple Protocol",
                "type": "object",
            },
            "experiment_type": "PCR",
            "lab_location": "Building A, Room 101",
            "priority": "high",
        },
    )

    # Mock the SlotMemory.generate_response method
    with patch(
        "masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory"
    ) as mock_memory_class:
        mock_memory = Mock()

        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(
                required=[
                    SlotOperation(
                        operation="update",
                        rf_name="result",
                        rf_value="Successful amplification",
                    )
                ]
            )

        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory

        # Mock the prompt creation
        with patch(
            "masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt"
        ) as mock_prompt:
            mock_prompt.return_value = "test prompt template"

            result = await handle_slot_extraction(request)

    # Verify the response
    assert isinstance(result, FieldInputResponse)

    # Verify scenario metadata is preserved
    # Note: The current implementation only preserves protocol_schema
    # Additional metadata is not currently preserved in the response
    assert "protocol_schema" in result.scenario
    assert result.scenario["protocol_schema"]["title"] == "Simple Protocol"

    # Verify tool calls work correctly
    assistant_message = result.history[-1]
    tool_call = assistant_message["tool_calls"][0]
    arguments = json.loads(tool_call["arguments"])

    assert len(arguments["operations"]) == 1
    assert arguments["operations"][0]["rf_name"] == "result"
    assert arguments["operations"][0]["rf_value"] == "Successful amplification"
