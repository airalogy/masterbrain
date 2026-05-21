"""Test protocol debug types"""

import pytest
from pydantic import ValidationError

from masterbrain.endpoints.protocol_debug.types import (
    DEFAULT_MODEL,
    ProtocolDebugInput,
    SupportedModels,
)


class TestSupportedModels:
    """Test SupportedModels class"""

    def test_valid_model_names(self):
        """Test valid model names"""
        valid_names = [
            "qwen3.5-flash",
            "qwen3.5-plus",
            "gpt-4o-mini",
        ]

        for name in valid_names:
            model = SupportedModels(name=name)
            assert model.name == name
            assert model.enable_thinking is False
            assert model.enable_search is False

    def test_invalid_model_name(self):
        """Test invalid model name raises error"""
        with pytest.raises(ValidationError):
            SupportedModels(name="invalid-model")

    def test_model_with_options(self):
        """Test model with thinking and search enabled"""
        model = SupportedModels(
            name="qwen3.5-flash", enable_thinking=True, enable_search=True
        )
        assert model.enable_thinking is True
        assert model.enable_search is True

    def test_default_model(self):
        """Test default model configuration"""
        assert DEFAULT_MODEL.name == "qwen3.5-flash"
        assert DEFAULT_MODEL.enable_thinking is False
        assert DEFAULT_MODEL.enable_search is False


class TestProtocolDebugInput:
    """Test ProtocolDebugInput class"""

    def test_valid_input(self):
        """Test valid input data"""
        input_data = {
            "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}",
            "suspect_protocol": "{{step|step1,1}} First step",
        }

        debug_input = ProtocolDebugInput(**input_data)
        assert debug_input.full_protocol == input_data["full_protocol"]
        assert debug_input.suspect_protocol == input_data["suspect_protocol"]
        assert debug_input.chat_id is None
        assert debug_input.user_id is None
        assert debug_input.model == DEFAULT_MODEL
        assert debug_input.fixed_protocol is None
        assert debug_input.response is None

    def test_input_with_all_fields(self):
        """Test input with all fields populated"""
        input_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}",
            "suspect_protocol": "{{step|step1,1}} First step",
            "model": {
                "name": "gpt-4o-mini",
                "enable_thinking": True,
                "enable_search": False,
            },
            "fixed_protocol": "Fixed protocol",
            "response": "Debug response",
        }

        debug_input = ProtocolDebugInput(**input_data)
        assert debug_input.chat_id == "test_chat_123"
        assert debug_input.user_id == "test_user_456"
        assert debug_input.model.name == "gpt-4o-mini"
        assert debug_input.model.enable_thinking is True
        assert debug_input.model.enable_search is False
        assert debug_input.fixed_protocol == "Fixed protocol"
        assert debug_input.response == "Debug response"

    def test_missing_required_fields(self):
        """Test that missing required fields raise error"""
        # Missing full_protocol
        with pytest.raises(ValidationError):
            ProtocolDebugInput(suspect_protocol="test")

        # Missing suspect_protocol
        with pytest.raises(ValidationError):
            ProtocolDebugInput(full_protocol="test")

    def test_empty_strings(self):
        """Test that empty strings are allowed"""
        input_data = {
            "full_protocol": "",
            "suspect_protocol": "",
        }

        debug_input = ProtocolDebugInput(**input_data)
        assert debug_input.full_protocol == ""
        assert debug_input.suspect_protocol == ""

    def test_custom_model_configuration(self):
        """Test custom model configuration"""
        input_data = {
            "full_protocol": "test",
            "suspect_protocol": "test",
            "model": {
                "name": "qwen3.5-plus",
                "enable_thinking": True,
                "enable_search": True,
            },
        }

        debug_input = ProtocolDebugInput(**input_data)
        assert debug_input.model.name == "qwen3.5-plus"
        assert debug_input.model.enable_thinking is True
        assert debug_input.model.enable_search is True
