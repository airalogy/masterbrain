"""
Tests for Field Input Types

This module tests the data models and type validation for the field_input endpoint.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from masterbrain.endpoints.chat.field_input.types import (
    FieldInputRequest,
    FieldInputResponse,
    ModelConfig,
    SlotOperation,
    SlotUpdateResult,
    SupportedModels,
)


@pytest.mark.field_input
class TestSupportedModels:
    """Test SupportedModels Literal type."""

    def test_supported_models_values(self):
        """Test that all supported model names are valid."""
        valid_models = [
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "qwen-max",
            "qwen3.5-plus",
            "qwen3.5-flash",
        ]

        # Test that we can create ModelConfig with each valid model name
        for model_name in valid_models:
            config = ModelConfig(name=model_name)
            assert config.name == model_name


@pytest.mark.field_input
class TestModelConfig:
    """Test ModelConfig model."""

    def test_model_config_defaults(self):
        """Test ModelConfig with default values."""
        config = ModelConfig()

        assert config.name == "qwen-max"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048

    def test_model_config_custom_values(self):
        """Test ModelConfig with custom values."""
        config = ModelConfig(name="gpt-4o-mini", temperature=0.0, max_tokens=1024)

        assert config.name == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.max_tokens == 1024

    def test_model_config_invalid_model_name(self):
        """Test ModelConfig with invalid model name."""
        with pytest.raises(ValidationError):
            ModelConfig(name="invalid-model")

    def test_model_config_temperature_range(self):
        """Test ModelConfig temperature validation."""
        # Valid temperature values
        config = ModelConfig(temperature=0.0)
        assert config.temperature == 0.0

        config = ModelConfig(temperature=1.0)
        assert config.temperature == 1.0

        config = ModelConfig(temperature=0.5)
        assert config.temperature == 0.5

    def test_model_config_max_tokens_validation(self):
        """Test ModelConfig max_tokens validation."""
        # Valid max_tokens values
        config = ModelConfig(max_tokens=1)
        assert config.max_tokens == 1

        config = ModelConfig(max_tokens=4096)
        assert config.max_tokens == 4096

        # Should accept large values
        config = ModelConfig(max_tokens=100000)
        assert config.max_tokens == 100000

    def test_model_config_serialization(self):
        """Test ModelConfig serialization."""
        config = ModelConfig(name="gpt-4o-mini", temperature=0.0, max_tokens=512)

        config_dict = config.model_dump()
        assert config_dict["name"] == "gpt-4o-mini"
        assert config_dict["temperature"] == 0.0
        assert config_dict["max_tokens"] == 512


@pytest.mark.field_input
class TestSlotOperation:
    """Test SlotOperation model."""

    def test_slot_operation_defaults(self):
        """Test SlotOperation with default values."""
        operation = SlotOperation(rf_name="test_field", rf_value="test_value")

        assert operation.operation == "update"
        assert operation.rf_name == "test_field"
        assert operation.rf_value == "test_value"

    def test_slot_operation_custom_operation(self):
        """Test SlotOperation with custom operation."""
        operation = SlotOperation(
            operation="insert", rf_name="test_field", rf_value="test_value"
        )

        assert operation.operation == "insert"
        assert operation.rf_name == "test_field"
        assert operation.rf_value == "test_value"

    def test_slot_operation_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            SlotOperation(rf_name="test_field")

        with pytest.raises(ValidationError):
            SlotOperation(rf_value="test_value")

    def test_slot_operation_serialization(self):
        """Test SlotOperation serialization."""
        operation = SlotOperation(rf_name="test_field", rf_value="test_value")

        operation_dict = operation.model_dump()
        assert operation_dict["operation"] == "update"
        assert operation_dict["rf_name"] == "test_field"
        assert operation_dict["rf_value"] == "test_value"


@pytest.mark.field_input
class TestSlotUpdateResult:
    """Test SlotUpdateResult model."""

    def test_slot_update_result_empty(self):
        """Test SlotUpdateResult with empty required list."""
        result = SlotUpdateResult(required=[])

        assert len(result.required) == 0
        assert isinstance(result.required, list)

    def test_slot_update_result_with_operations(self):
        """Test SlotUpdateResult with operations."""
        operations = [
            SlotOperation(rf_name="field1", rf_value="value1"),
            SlotOperation(rf_name="field2", rf_value="value2"),
        ]

        result = SlotUpdateResult(required=operations)

        assert len(result.required) == 2
        assert result.required[0].rf_name == "field1"
        assert result.required[1].rf_name == "field2"

    def test_slot_update_result_serialization(self):
        """Test SlotUpdateResult serialization."""
        operations = [SlotOperation(rf_name="field1", rf_value="value1")]

        result = SlotUpdateResult(required=operations)
        result_dict = result.model_dump()

        assert "required" in result_dict
        assert len(result_dict["required"]) == 1
        assert result_dict["required"][0]["rf_name"] == "field1"


@pytest.mark.field_input
class TestFieldInputRequest:
    """Test FieldInputRequest model."""

    def test_field_input_request_minimal(self):
        """Test FieldInputRequest with minimal required fields."""
        request = FieldInputRequest(
            chat_id="test_chat",
            user_id="test_user",
            model=ModelConfig(name="gpt-4o-mini"),
        )

        assert request.chat_id == "test_chat"
        assert request.user_id == "test_user"
        assert request.model.name == "gpt-4o-mini"
        assert request.history == []
        assert request.scenario == {}

    def test_field_input_request_with_history(self):
        """Test FieldInputRequest with conversation history."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        request = FieldInputRequest(
            chat_id="test_chat",
            user_id="test_user",
            model=ModelConfig(name="gpt-4o-mini"),
            history=history,
        )

        assert len(request.history) == 2
        assert request.history[0]["role"] == "user"
        assert request.history[1]["role"] == "assistant"

    def test_field_input_request_with_scenario(self):
        """Test FieldInputRequest with scenario data."""
        scenario = {
            "protocol_schema": {
                "properties": {"test": {"type": "string"}},
                "required": ["test"],
            },
            "additional_config": "test_value",
        }

        request = FieldInputRequest(
            chat_id="test_chat",
            user_id="test_user",
            model=ModelConfig(name="gpt-4o-mini"),
            scenario=scenario,
        )

        assert "protocol_schema" in request.scenario
        assert "additional_config" in request.scenario
        assert request.scenario["additional_config"] == "test_value"

    def test_field_input_request_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            FieldInputRequest(
                user_id="test_user", model=ModelConfig(name="gpt-4o-mini")
            )

        with pytest.raises(ValidationError):
            FieldInputRequest(
                chat_id="test_chat", model=ModelConfig(name="gpt-4o-mini")
            )

        with pytest.raises(ValidationError):
            FieldInputRequest(chat_id="test_chat", user_id="test_user")

    def test_field_input_request_serialization(self):
        """Test FieldInputRequest serialization."""
        request = FieldInputRequest(
            chat_id="test_chat",
            user_id="test_user",
            model=ModelConfig(name="gpt-4o-mini"),
            history=[{"role": "user", "content": "test"}],
            scenario={"test": "value"},
        )

        request_dict = request.model_dump()
        assert request_dict["chat_id"] == "test_chat"
        assert request_dict["user_id"] == "test_user"
        assert request_dict["model"]["name"] == "gpt-4o-mini"
        assert len(request_dict["history"]) == 1
        assert request_dict["scenario"]["test"] == "value"


@pytest.mark.field_input
class TestFieldInputResponse:
    """Test FieldInputResponse model."""

    def test_field_input_response_creation(self):
        """Test FieldInputResponse creation."""
        model_config = ModelConfig(name="gpt-4o-mini")
        history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": None, "tool_calls": []},
        ]
        scenario = {"protocol_schema": {}}

        response = FieldInputResponse(
            chat_id="test_chat",
            user_id="test_user",
            model=model_config,
            history=history,
            scenario=scenario,
        )

        assert response.chat_id == "test_chat"
        assert response.user_id == "test_user"
        assert response.model.name == "gpt-4o-mini"
        assert len(response.history) == 2
        assert "protocol_schema" in response.scenario

    def test_field_input_response_required_fields(self):
        """Test that required fields are enforced."""
        model_config = ModelConfig(name="gpt-4o-mini")

        with pytest.raises(ValidationError):
            FieldInputResponse(
                user_id="test_user", model=model_config, history=[], scenario={}
            )

        with pytest.raises(ValidationError):
            FieldInputResponse(
                chat_id="test_chat", model=model_config, history=[], scenario={}
            )

        with pytest.raises(ValidationError):
            FieldInputResponse(
                chat_id="test_chat", user_id="test_user", history=[], scenario={}
            )

    def test_field_input_response_serialization(self):
        """Test FieldInputResponse serialization."""
        model_config = ModelConfig(name="gpt-4o-mini")
        history = [{"role": "user", "content": "test"}]
        scenario = {"protocol_schema": {}}

        response = FieldInputResponse(
            chat_id="test_chat",
            user_id="test_user",
            model=model_config,
            history=history,
            scenario=scenario,
        )

        response_dict = response.model_dump()
        assert response_dict["chat_id"] == "test_chat"
        assert response_dict["user_id"] == "test_user"
        assert response_dict["model"]["name"] == "gpt-4o-mini"
        assert len(response_dict["history"]) == 1
        assert "protocol_schema" in response_dict["scenario"]


@pytest.mark.field_input
class TestModelValidation:
    """Test model validation scenarios."""

    def test_complex_nested_scenario(self):
        """Test validation with complex nested scenario data."""
        complex_scenario = {
            "protocol_schema": {
                "$defs": {
                    "NestedObject": {
                        "type": "object",
                        "properties": {"nested_field": {"type": "string"}},
                    }
                },
                "properties": {"main_field": {"$ref": "#/$defs/NestedObject"}},
            },
            "metadata": {"version": "1.0", "tags": ["test", "validation"]},
        }

        request = FieldInputRequest(
            chat_id="test_chat",
            user_id="test_user",
            model=ModelConfig(name="gpt-4o-mini"),
            scenario=complex_scenario,
        )

        assert request.scenario["metadata"]["version"] == "1.0"
        assert "NestedObject" in request.scenario["protocol_schema"]["$defs"]

    def test_history_with_various_content_types(self):
        """Test validation with various content types in history."""
        history = [
            {"role": "user", "content": "Simple text message"},
            {"role": "assistant", "content": None, "tool_calls": []},
            {"role": "user", "content": "https://example.com/image.png"},
            {"role": "system", "content": "System instruction"},
        ]

        request = FieldInputRequest(
            chat_id="test_chat",
            user_id="test_user",
            model=ModelConfig(name="gpt-4o-mini"),
            history=history,
        )

        assert len(request.history) == 4
        assert request.history[0]["role"] == "user"
        assert request.history[1]["role"] == "assistant"
        assert request.history[2]["role"] == "user"
        assert request.history[3]["role"] == "system"
