"""Test protocol debug router"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from masterbrain.endpoints.protocol_debug.types import ProtocolDebugInput


def _mock_debug_client():
    """Build a mocked LLM client returning a valid structured debug result."""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = (
        '{"has_errors": true, "fixed_segment": "Fixed protocol", "reason": "Test reason"}'
    )
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_protocol_debug_endpoint(client: TestClient, sample_protocol_debug_input: dict):
    """Test protocol debug endpoint"""
    with patch(
        "masterbrain.endpoints.protocol_debug.logic.select_client",
        return_value=_mock_debug_client(),
    ):
        response = client.post(
            "/api/endpoints/protocol_debug", json=sample_protocol_debug_input
        )

    assert response.status_code == 200

    # Parse response
    response_data = response.json()

    # Check that the response contains the expected ProtocolDebugOutput fields
    assert "has_errors" in response_data
    assert "fixed_protocol" in response_data
    assert "response" in response_data


def test_protocol_debug_with_empty_suspect_protocol(client: TestClient):
    """Test protocol debug with empty suspect protocol"""
    input_data = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456",
        "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}",
        "suspect_protocol": "",
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
    }

    response = client.post("/api/endpoints/protocol_debug", json=input_data)

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["has_errors"] is False
    assert response_data["fixed_protocol"] == ""
    assert response_data["response"] == "The part to be checked is empty."


def test_protocol_debug_with_invalid_model(client: TestClient):
    """Test protocol debug with invalid model"""
    input_data = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456",
        "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}",
        "suspect_protocol": "{{step|step1,1}} First step",
        "model": {
            "name": "invalid-model",
            "enable_thinking": False,
            "enable_search": False,
        },
    }

    response = client.post("/api/endpoints/protocol_debug", json=input_data)

    # Should return 400 or 422 for invalid model
    assert response.status_code in [400, 422]


def test_protocol_debug_response_structure(
    client: TestClient, sample_protocol_debug_input: dict
):
    """Test that protocol debug response has correct structure"""
    with patch(
        "masterbrain.endpoints.protocol_debug.logic.select_client",
        return_value=_mock_debug_client(),
    ):
        response = client.post(
            "/api/endpoints/protocol_debug", json=sample_protocol_debug_input
        )

    assert response.status_code == 200

    response_data = response.json()

    # Validate response structure matches ProtocolDebugOutput
    required_fields = [
        "has_errors",
        "fixed_protocol",
        "response",
    ]

    for field in required_fields:
        assert field in response_data, f"Missing field: {field}"

    assert isinstance(response_data["has_errors"], bool)
    assert isinstance(response_data["fixed_protocol"], str)
    assert isinstance(response_data["response"], str)
