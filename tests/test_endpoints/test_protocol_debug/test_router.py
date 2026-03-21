"""Test protocol debug router"""

import json

import pytest
from fastapi.testclient import TestClient

from masterbrain.endpoints.protocol_debug.types import ProtocolDebugInput


def test_protocol_debug_endpoint(client: TestClient, sample_protocol_debug_input: dict):
    """Test protocol debug endpoint"""
    response = client.post(
        "/api/endpoints/protocol_debug", json=sample_protocol_debug_input
    )

    assert response.status_code == 200

    # Parse response
    response_data = response.json()

    # Check that the response contains the expected fields
    assert "fixed_protocol" in response_data
    assert "response" in response_data
    assert "chat_id" in response_data
    assert "user_id" in response_data
    assert "full_protocol" in response_data
    assert "suspect_protocol" in response_data
    assert "model" in response_data


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
    assert response_data["fixed_protocol"] == ""
    assert response_data["response"] == "The part to be fixed is empty."


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
    response = client.post(
        "/api/endpoints/protocol_debug", json=sample_protocol_debug_input
    )

    assert response.status_code == 200

    response_data = response.json()

    # Validate response structure
    required_fields = [
        "chat_id",
        "user_id",
        "full_protocol",
        "suspect_protocol",
        "model",
        "fixed_protocol",
        "response",
    ]

    for field in required_fields:
        assert field in response_data, f"Missing field: {field}"

    # Check model structure
    model = response_data["model"]
    assert "name" in model
    assert "enable_thinking" in model
    assert "enable_search" in model
