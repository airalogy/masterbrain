"""Test protocol debug logic"""

from unittest.mock import AsyncMock, patch

import pytest

from masterbrain.endpoints.protocol_debug.logic import generate_debug_result
from masterbrain.endpoints.protocol_debug.types import (
    ProtocolDebugInput,
    SupportedModels,
)


class TestGenerateDebugResult:
    """Test generate_debug_result function"""

    @pytest.mark.asyncio
    async def test_generate_debug_result_success(self):
        """Test successful debug result generation"""
        # Mock input
        input_data = ProtocolDebugInput(
            chat_id="test_chat_123",
            user_id="test_user_456",
            full_protocol="# Test Protocol\n\nExperimenter: {{var|experimenter}}",
            suspect_protocol="{{step|step1,1}} First step",
            model=SupportedModels(
                name="qwen3.5-flash", enable_thinking=False, enable_search=False
            ),
        )

        # Mock response
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"has_errors": true, "fixed_segment": "Fixed protocol", "reason": "Test reason"}'

        # Mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch(
            "masterbrain.endpoints.protocol_debug.logic.select_client",
            return_value=mock_client,
        ):
            result = await generate_debug_result(input_data)

            assert result.has_errors is True
            assert result.fixed_protocol == "Fixed protocol"
            assert result.response == "Test reason"

    @pytest.mark.asyncio
    async def test_generate_debug_result_empty_suspect(self):
        """Test debug result with empty suspect protocol"""
        input_data = ProtocolDebugInput(
            full_protocol="# Test Protocol",
            suspect_protocol="",
            model=SupportedModels(name="qwen3.5-flash"),
        )

        result = await generate_debug_result(input_data)

        assert result.has_errors is False
        assert result.fixed_protocol == ""
        assert result.response == "The part to be checked is empty."

    @pytest.mark.asyncio
    async def test_generate_debug_result_invalid_json_response(self):
        """Test debug result with invalid JSON response"""
        input_data = ProtocolDebugInput(
            full_protocol="# Test Protocol",
            suspect_protocol="{{step|step1,1}} First step",
            model=SupportedModels(name="qwen3.5-flash"),
        )

        # Mock response with invalid JSON
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "invalid json"

        # Mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch(
            "masterbrain.endpoints.protocol_debug.logic.select_client",
            return_value=mock_client,
        ):
            # Invalid JSON is handled gracefully (no exception raised).
            result = await generate_debug_result(input_data)

            assert result.has_errors is False
            assert result.fixed_protocol == ""
            assert result.response.startswith("Failed to parse LLM response")

    @pytest.mark.asyncio
    async def test_generate_debug_result_missing_fields(self):
        """Test debug result with missing response fields"""
        input_data = ProtocolDebugInput(
            full_protocol="# Test Protocol",
            suspect_protocol="{{step|step1,1}} First step",
            model=SupportedModels(name="qwen3.5-flash"),
        )

        # Mock response with missing fields
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = '{"other_field": "value"}'

        # Mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch(
            "masterbrain.endpoints.protocol_debug.logic.select_client",
            return_value=mock_client,
        ):
            result = await generate_debug_result(input_data)

            assert result.has_errors is False
            assert result.fixed_protocol == ""
            assert result.response == ""

    @pytest.mark.asyncio
    async def test_generate_debug_result_with_thinking_and_search(self):
        """Test debug result with thinking and search enabled"""
        input_data = ProtocolDebugInput(
            full_protocol="# Test Protocol",
            suspect_protocol="{{step|step1,1}} First step",
            model=SupportedModels(
                name="qwen3.5-flash", enable_thinking=True, enable_search=True
            ),
        )

        # Mock response
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"fixed_segment": "Fixed protocol", "reason_and_basis_for_fix": "Test reason"}'

        # Mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch(
            "masterbrain.endpoints.protocol_debug.logic.select_client",
            return_value=mock_client,
        ):
            await generate_debug_result(input_data)

            # Verify that the client was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args

            # Check extra_body parameters
            assert call_args[1]["extra_body"]["enable_thinking"] is True
            assert call_args[1]["extra_body"]["enable_search"] is True

    @pytest.mark.asyncio
    async def test_generate_debug_result_timeout_setting(self):
        """Test that timeout is set correctly"""
        input_data = ProtocolDebugInput(
            full_protocol="# Test Protocol",
            suspect_protocol="{{step|step1,1}} First step",
            model=SupportedModels(name="qwen3.5-flash"),
        )

        # Mock response
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"fixed_segment": "Fixed protocol", "reason_and_basis_for_fix": "Test reason"}'

        # Mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch(
            "masterbrain.endpoints.protocol_debug.logic.select_client",
            return_value=mock_client,
        ):
            await generate_debug_result(input_data)

            # Verify timeout is set to 1800 seconds
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["timeout"] == 1800
