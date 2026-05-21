"""Integration tests for protocol debug module"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


FIXTURE_DIR = Path(__file__).resolve().parent


class TestProtocolDebugIntegration:
    """Integration tests for protocol debug functionality"""

    @patch("masterbrain.endpoints.protocol_debug.logic.select_client")
    def test_full_protocol_debug_flow(self, mock_select_client, client: TestClient):
        """Test complete protocol debug flow"""
        # Mock the LLM client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"has_errors": true, "fixed_segment": "Fixed protocol", "reason": "Test reason"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_select_client.return_value = mock_client

        # Load test data
        with open(
            FIXTURE_DIR / "demo_protocol_debug_input.json",
            "r",
        ) as f:
            input_data = json.load(f)

        # Make request
        response = client.post("/api/endpoints/protocol_debug", json=input_data)

        # Verify response
        assert response.status_code == 200
        response_data = response.json()

        # Check required fields
        required_fields = ["has_errors", "fixed_protocol", "response"]
        for field in required_fields:
            assert field in response_data, f"Missing field: {field}"

        # Verify output fields are populated
        assert response_data["has_errors"] is True
        assert response_data["fixed_protocol"] == "Fixed protocol"
        assert response_data["response"] == "Test reason"

    @patch("masterbrain.endpoints.protocol_debug.logic.select_client")
    def test_protocol_debug_with_different_models(
        self, mock_select_client, client: TestClient
    ):
        """Test protocol debug with different model configurations"""
        # Mock the LLM client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"has_errors": true, "fixed_segment": "Fixed protocol", "reason": "Test reason"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_select_client.return_value = mock_client

        base_input = {
            "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}",
            "suspect_protocol": "{{step|step1,1}} First step",
        }

        # Test different models
        models_to_test = [
            {"name": "qwen3.5-flash", "enable_thinking": False, "enable_search": False},
            {
                "name": "qwen3.5-flash",
                "enable_thinking": True,
                "enable_search": False,
            },
            {"name": "qwen3.5-plus", "enable_thinking": False, "enable_search": True},
            {"name": "gpt-4o-mini", "enable_thinking": True, "enable_search": True},
        ]

        for model_config in models_to_test:
            input_data = {**base_input, "model": model_config}

            response = client.post("/api/endpoints/protocol_debug", json=input_data)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["has_errors"] is True
            assert response_data["fixed_protocol"] == "Fixed protocol"
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == model_config["name"]
            assert call_kwargs["extra_body"] == {
                "enable_thinking": model_config["enable_thinking"],
                "enable_search": model_config["enable_search"],
            }

    def test_protocol_debug_error_handling(self, client: TestClient):
        """Test error handling in protocol debug"""
        # Test with invalid model
        invalid_input = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "full_protocol": "# Test Protocol",
            "suspect_protocol": "{{step|step1,1}} First step",
            "model": {
                "name": "invalid-model",
                "enable_thinking": False,
                "enable_search": False,
            },
        }

        response = client.post("/api/endpoints/protocol_debug", json=invalid_input)
        # Should return validation error
        assert response.status_code in [400, 422]

        # Test with missing required fields
        incomplete_input = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            # Missing full_protocol and suspect_protocol
        }

        response = client.post("/api/endpoints/protocol_debug", json=incomplete_input)
        assert response.status_code in [400, 422]

    @patch("masterbrain.endpoints.protocol_debug.logic.select_client")
    def test_protocol_debug_edge_cases(self, mock_select_client, client: TestClient):
        """Test edge cases in protocol debug"""
        # Mock the LLM client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"has_errors": true, "fixed_segment": "Fixed protocol", "reason": "Test reason"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_select_client.return_value = mock_client

        # Test with very long protocol
        long_protocol = "# " + "A" * 10000  # Very long protocol
        input_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "full_protocol": long_protocol,
            "suspect_protocol": "{{step|step1,1}} First step",
            "model": {
                "name": "qwen3.5-flash",
                "enable_thinking": False,
                "enable_search": False,
            },
        }

        response = client.post("/api/endpoints/protocol_debug", json=input_data)
        # Should handle long input gracefully
        assert response.status_code in [200, 413]  # 413 for payload too large

        # Test with special characters in protocol
        special_chars_protocol = "# Test Protocol\n\n{{var|test_var}} {{step|step1,1}} {{check|check1}}\n\n特殊字符: 中文测试 🚀\n\n"
        input_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "full_protocol": special_chars_protocol,
            "suspect_protocol": "{{step|step1,1}} First step",
            "model": {
                "name": "qwen3.5-flash",
                "enable_thinking": False,
                "enable_search": False,
            },
        }

        response = client.post("/api/endpoints/protocol_debug", json=input_data)
        assert response.status_code == 200

    @patch("masterbrain.endpoints.protocol_debug.logic.select_client")
    def test_protocol_debug_response_consistency(
        self, mock_select_client, client: TestClient
    ):
        """Test that protocol debug responses are consistent"""
        # Mock the LLM client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[
            0
        ].message.content = '{"has_errors": true, "fixed_segment": "Fixed protocol", "reason": "Test reason"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_select_client.return_value = mock_client

        input_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}",
            "suspect_protocol": "{{step|step1,1}} First step",
            "model": {
                "name": "qwen3.5-flash",
                "enable_thinking": False,
                "enable_search": False,
            },
        }

        # Make multiple requests to check consistency
        responses = []
        for _ in range(3):
            response = client.post("/api/endpoints/protocol_debug", json=input_data)
            assert response.status_code == 200
            responses.append(response.json())

        # Check that all responses have the same structure
        for response in responses:
            assert "has_errors" in response
            assert "fixed_protocol" in response
            assert "response" in response
            assert set(response) == {"has_errors", "fixed_protocol", "response"}
            assert response["has_errors"] is True
