"""
Tests for Slot Service

This module tests the core business logic for slot extraction and filling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from masterbrain.endpoints.chat.field_input.logic.slot_service import (
    generate_unique_id,
    load_schema,
    extract_required_keys,
    format_update_info,
    is_base64_image,
    is_image_url,
    get_vision_model_for,
    SlotMemory,
    handle_slot_extraction
)
from masterbrain.endpoints.chat.field_input.types import (
    FieldInputRequest,
    FieldInputResponse,
    ModelConfig,
    SlotOperation,
    SlotUpdateResult
)


@pytest.mark.field_input
def test_generate_unique_id():
    """Test that generate_unique_id returns unique strings."""
    id1 = generate_unique_id()
    id2 = generate_unique_id()
    
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert id1 != id2
    assert len(id1) > 0
    assert len(id2) > 0


@pytest.mark.field_input
def test_load_schema_from_dict():
    """Test loading schema from a dictionary."""
    schema_dict = {
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }
    
    result = load_schema(schema_dict)
    assert result == schema_dict


@pytest.mark.field_input
@patch('builtins.open')
def test_load_schema_from_file(mock_open):
    """Test loading schema from a file."""
    mock_file = Mock()
    mock_file.read.return_value = '{"properties": {"test": {"type": "string"}}}'
    mock_open.return_value.__enter__.return_value = mock_file
    
    result = load_schema("test_schema.json")
    
    assert result == {"properties": {"test": {"type": "string"}}}
    mock_open.assert_called_once_with("test_schema.json", "r")


@pytest.mark.field_input
def test_extract_required_keys():
    """Test extracting required keys from schema."""
    schema_data = {
        "required": ["field1", "field2"],
        "properties": {
            "field1": {"description": "First field", "title": "Field 1"},
            "field2": {"title": "Field 2"},
            "field3": {"description": "Third field"}
        }
    }
    
    result = extract_required_keys(schema_data)
    expected = [
        ("field1", "First field"),
        ("field2", "Field 2")
    ]
    
    assert result == expected


@pytest.mark.field_input
def test_extract_required_keys_no_required():
    """Test extracting required keys when no required fields exist."""
    schema_data = {
        "properties": {
            "field1": {"description": "First field"}
        }
    }
    
    result = extract_required_keys(schema_data)
    assert result == []


@pytest.mark.field_input
def test_format_update_info():
    """Test formatting update information into SlotUpdateResult."""
    update_info_list = [
        {
            "slot_name": "field1",
            "new_value": "value1",
            "old_value": "old_value1"
        },
        {
            "slot_name": "field2",
            "new_value": "value2",
            "old_value": "old_value2"
        },
        {
            "slot_name": "null",
            "new_value": "value3",
            "old_value": "old_value3"
        },
        {
            "slot_name": "field4",
            "new_value": "null",
            "old_value": "old_value4"
        }
    ]
    
    result = format_update_info(update_info_list)
    
    assert isinstance(result, SlotUpdateResult)
    assert len(result.required) == 2
    
    # Check that only valid operations are included
    operation_names = [op.rf_name for op in result.required]
    assert "field1" in operation_names
    assert "field2" in operation_names
    assert "null" not in operation_names
    assert "field4" not in operation_names


@pytest.mark.field_input
def test_format_update_info_no_valid_updates():
    """Test formatting update info when no valid updates exist."""
    update_info_list = [
        {
            "slot_name": "null",
            "new_value": "value1",
            "old_value": "old_value1"
        },
        {
            "slot_name": "field2",
            "new_value": "null",
            "old_value": "old_value2"
        }
    ]
    
    result = format_update_info(update_info_list)
    assert len(result.required) == 0


@pytest.mark.field_input
def test_is_base64_image():
    """Test base64 image detection."""
    # Valid base64 image
    assert is_base64_image("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
    
    # Invalid base64 image
    assert not is_base64_image("https://example.com/image.png")
    assert not is_base64_image("data:text/plain;base64,SGVsbG8=")
    assert not is_base64_image(None)
    assert not is_base64_image("")


@pytest.mark.field_input
def test_is_image_url():
    """Test image URL detection."""
    # Valid image URLs
    assert is_image_url("https://example.com/image.jpg")
    assert is_image_url("https://example.com/image.png")
    assert is_image_url("https://example.com/image.gif")
    assert is_image_url("http://example.com/image.webp")
    
    # Invalid image URLs
    assert not is_image_url("https://example.com/document.pdf")
    assert not is_image_url("https://example.com/data.txt")
    assert not is_image_url("ftp://example.com/image.jpg")
    assert not is_image_url(None)
    assert not is_image_url("")


@pytest.mark.field_input
class TestSlotMemory:
    """Test SlotMemory class functionality."""
    
    def test_slot_memory_initialization(self):
        """Test SlotMemory initialization."""
        key_description_list = [("field1", "First field"), ("field2", "Second field")]
        memory = SlotMemory(key_description_list)
        
        assert memory.key_description_list == key_description_list
        # current_slots is initialized with "null" values for each key
        assert memory.current_slots == {"field1": "null", "field2": "null"}
        assert memory.current_update_info_list == [{"slot_name": None, "old_value": None, "new_value": None}]
        assert memory.chat_history == []
        assert memory.current_datetime is not None
        assert memory.inform_check == False
    
    def test_parse_update_info(self):
        """Test parsing update information from text."""
        memory = SlotMemory([("field1", "First field")])
        
        # Test valid update info
        update_text = """
        UPDATE field1 "" value1
        """
        result = memory.parse_update_info(update_text)
        
        assert len(result) == 1
        assert result[0]["slot_name"] == "field1"
        assert result[0]["new_value"] == "value1"
    
    def test_parse_update_info_invalid_json(self):
        """Test parsing update info with invalid JSON."""
        memory = SlotMemory([("field1", "First field")])
        
        result = memory.parse_update_info("invalid json")
        # Should return default update dict when no valid UPDATE lines found
        assert result == [{"slot_name": None, "old_value": None, "new_value": None}]
    
    def test_parse_update_info_empty(self):
        """Test parsing empty update info."""
        memory = SlotMemory([("field1", "First field")])
        
        result = memory.parse_update_info("")
        # Should return default update dict when empty
        assert result == [{"slot_name": None, "old_value": None, "new_value": None}]
        
        result = memory.parse_update_info(None)
        # Should return default update dict when None
        assert result == [{"slot_name": None, "old_value": None, "new_value": None}]


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_handle_slot_extraction_success():
    """Test successful slot extraction."""
    # Create a mock request
    request = FieldInputRequest(
        chat_id="test_chat",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[
            {
                "role": "user",
                "content": "forward_primer_volume是50；reverse_primer_volume是150。"
            }
        ],
        scenario={
            "protocol_schema": {
                "properties": {
                    "forward_primer_volume": {
                        "description": "Volume of forward primer",
                        "title": "Forward Primer Volume",
                        "type": "number"
                    },
                    "reverse_primer_volume": {
                        "description": "Volume of reverse primer",
                        "title": "Reverse Primer Volume",
                        "type": "number"
                    }
                },
                "required": ["forward_primer_volume", "reverse_primer_volume"],
                "title": "TestProtocol",
                "type": "object"
            }
        }
    )
    
    # Mock the SlotMemory.generate_response method
    with patch('masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory') as mock_memory_class:
        mock_memory = Mock()
        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(
                required=[
                    SlotOperation(
                        operation="update",
                        rf_name="forward_primer_volume",
                        rf_value="50"
                    ),
                    SlotOperation(
                        operation="update",
                        rf_name="reverse_primer_volume",
                        rf_value="150"
                    )
                ]
            )
        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory
        
        # Mock the prompt creation
        with patch('masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt') as mock_prompt:
            mock_prompt.return_value = "test prompt template"
            
            result = await handle_slot_extraction(request)
    
    # Verify the complete response structure
    assert isinstance(result, FieldInputResponse)
    assert result.chat_id == "test_chat"
    assert result.user_id == "test_user"
    assert result.model.name == "gpt-4o-mini"
    assert len(result.history) == 2  # user message + assistant response
    
    # Verify the assistant response contains tool calls
    assistant_message = result.history[-1]
    assert assistant_message["role"] == "assistant"
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
    assert len(arguments["operations"]) == 2
    
    # Verify all expected operations are present
    operation_names = [op["rf_name"] for op in arguments["operations"]]
    assert "forward_primer_volume" in operation_names
    assert "reverse_primer_volume" in operation_names
    
    # Verify operation values
    for operation in arguments["operations"]:
        assert operation["operation"] == "update"
        if operation["rf_name"] == "forward_primer_volume":
            assert operation["rf_value"] == "50"
        elif operation["rf_name"] == "reverse_primer_volume":
            assert operation["rf_value"] == "150"


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_handle_slot_extraction_empty_schema():
    """Test slot extraction with empty schema."""
    request = FieldInputRequest(
        chat_id="test_chat",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[
            {
                "role": "user",
                "content": "test content"
            }
        ],
        scenario={
            "protocol_schema": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    )
    
    with patch('masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory') as mock_memory_class:
        mock_memory = Mock()
        # Make generate_response return an awaitable object
        async def mock_generate_response(*args, **kwargs):
            return SlotUpdateResult(required=[])
        mock_memory.generate_response = mock_generate_response
        mock_memory_class.return_value = mock_memory
        
        with patch('masterbrain.endpoints.chat.field_input.logic.slot_service.create_slot_extraction_prompt') as mock_prompt:
            mock_prompt.return_value = "test prompt template"
            
            result = await handle_slot_extraction(request)
    
    assert isinstance(result, FieldInputResponse)
    assert len(result.history) == 2
    
    # Verify no operations in tool calls
    assistant_message = result.history[-1]
    tool_call = assistant_message["tool_calls"][0]
    arguments = json.loads(tool_call["arguments"])
    assert len(arguments["operations"]) == 0


@pytest.mark.field_input
@pytest.mark.asyncio
async def test_handle_slot_extraction_error_handling():
    """Test slot extraction error handling."""
    request = FieldInputRequest(
        chat_id="test_chat",
        user_id="test_user",
        model=ModelConfig(name="gpt-4o-mini"),
        history=[
            {
                "role": "user",
                "content": "test content"
            }
        ],
        scenario={
            "protocol_schema": {
                "properties": {},
                "required": [],
                "type": "object"
            }
        }
    )
    
    # Mock SlotMemory to raise an exception
    with patch('masterbrain.endpoints.chat.field_input.logic.slot_service.SlotMemory') as mock_memory_class:
        mock_memory_class.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            await handle_slot_extraction(request)


# ---------------------------------------------------------------------------
# Tests for get_vision_model_for
# ---------------------------------------------------------------------------

@pytest.mark.field_input
class TestGetVisionModelFor:
    """Tests for the get_vision_model_for() routing function."""

    def test_qwen_vl_model_returned_as_is(self):
        """Already-vision-capable Qwen VL models should be returned unchanged."""
        for model in ["qwen-vl-plus", "qwen-vl-plus-latest", "qwen3-vl-flash", "qwen3-vl-plus"]:
            result = get_vision_model_for(model)
            assert result == model, f"Expected {model} to be returned as-is, got {result}"

    def test_openai_vl_model_returned_as_is(self):
        """Already-vision-capable OpenAI models should be returned unchanged."""
        for model in ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]:
            result = get_vision_model_for(model)
            assert result == model, f"Expected {model} to be returned as-is, got {result}"

    def test_qwen_text_model_falls_back_to_vl(self):
        """Non-vision Qwen text models should fall back to DEFAULT_QWEN_VL_MODEL."""
        from masterbrain.configs import DEFAULT_QWEN_VL_MODEL
        for model in ["qwen3-max", "qwen-max", "qwen3.5-flash", "qwen3.5-plus"]:
            result = get_vision_model_for(model)
            assert result == DEFAULT_QWEN_VL_MODEL, (
                f"Expected qwen text model '{model}' to fall back to '{DEFAULT_QWEN_VL_MODEL}', got '{result}'"
            )

    def test_openai_text_model_falls_back_to_gpt4o_mini(self):
        """Non-vision OpenAI models (like gpt-3.5-turbo) should fall back to gpt-4o-mini."""
        result = get_vision_model_for("gpt-3.5-turbo")
        assert result == "gpt-4o-mini", (
            f"Expected 'gpt-3.5-turbo' to fall back to 'gpt-4o-mini', got '{result}'"
        )

    def test_unknown_model_falls_back_to_gpt4o_mini(self):
        """Unknown models should fall back to gpt-4o-mini."""
        result = get_vision_model_for("some-unknown-model")
        assert result == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Tests for format_update_info with non-string values
# ---------------------------------------------------------------------------

@pytest.mark.field_input
class TestFormatUpdateInfoRobustness:
    """Tests for format_update_info robustness with various value types."""

    def test_integer_new_value_does_not_crash(self):
        """Integer new_value should not raise AttributeError."""
        update_info_list = [
            {"slot_name": "forward_primer_volume", "old_value": "null", "new_value": 50},
        ]
        result = format_update_info(update_info_list)
        assert len(result.required) == 1
        assert result.required[0].rf_name == "forward_primer_volume"
        assert result.required[0].rf_value == "50"

    def test_float_new_value_does_not_crash(self):
        """Float new_value should not raise AttributeError."""
        update_info_list = [
            {"slot_name": "ph", "old_value": "null", "new_value": 7.4},
        ]
        result = format_update_info(update_info_list)
        assert len(result.required) == 1
        assert result.required[0].rf_value == "7.4"

    def test_none_new_value_is_skipped(self):
        """None new_value should be treated as null and skipped."""
        update_info_list = [
            {"slot_name": "field1", "old_value": "null", "new_value": None},
        ]
        result = format_update_info(update_info_list)
        assert len(result.required) == 0

    def test_none_slot_name_is_skipped(self):
        """None slot_name should be skipped."""
        update_info_list = [
            {"slot_name": None, "old_value": "null", "new_value": "some_value"},
        ]
        result = format_update_info(update_info_list)
        assert len(result.required) == 0

    def test_mixed_valid_and_invalid_entries(self):
        """Valid entries should be included; invalid ones skipped."""
        update_info_list = [
            {"slot_name": "field1", "old_value": "null", "new_value": 42},      # valid (int)
            {"slot_name": None, "old_value": "null", "new_value": "val"},        # skip (None name)
            {"slot_name": "field3", "old_value": "null", "new_value": None},     # skip (None value)
            {"slot_name": "field4", "old_value": "null", "new_value": "result"}, # valid (str)
        ]
        result = format_update_info(update_info_list)
        assert len(result.required) == 2
        names = {op.rf_name for op in result.required}
        assert names == {"field1", "field4"}

