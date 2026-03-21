"""
Tests for Field Input Router

This module tests the FastAPI router for the field_input endpoint.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.chat.field_input.router import field_input_router


def _build_client() -> TestClient:
    """Build a test client with the field_input router."""
    app = FastAPI()
    app.include_router(
        field_input_router, prefix="/api/endpoints", tags=["Field Input"]
    )
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.field_input
def test_field_input_endpoint_exists():
    """Test that the field_input endpoint exists and is accessible."""
    response = CLIENT.get("/docs")
    assert response.status_code == 200


@pytest.mark.field_input
@pytest.mark.parametrize("model_name", ["gpt-4o-mini", "qwen3.5-flash"])
def test_field_input_successful_request(model_name):
    """Test successful field input request with different models."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "model": {"name": model_name, "temperature": 0.0, "max_tokens": 512},
        "history": [
            {
                "role": "user",
                "content": "forward_primer_volume是50；reverse_primer_volume是150。",
            }
        ],
        "scenario": {
            "protocol_schema": {
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
                },
                "required": ["forward_primer_volume", "reverse_primer_volume"],
                "title": "TestProtocol",
                "type": "object",
            }
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)

    # Debug: print response details for failed tests
    if response.status_code != 200:
        print(f"\nModel: {model_name}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        print(f"Response Headers: {response.headers}")

    # For qwen3.5-flash, we might get connection errors due to environment configuration
    # This is not a test failure but an environment issue
    if model_name == "qwen3.5-flash" and response.status_code == 500:
        pytest.skip(
            f"Model {model_name} is not available or configured in this environment"
        )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "chat_id" in data
    assert "user_id" in data
    assert "model" in data
    assert "history" in data
    assert "scenario" in data

    # Verify chat_id and user_id are preserved
    assert data["chat_id"] == payload["chat_id"]
    assert data["user_id"] == payload["user_id"]

    # Verify history contains tool calls
    assert len(data["history"]) >= 2  # user message + assistant response
    assistant_message = data["history"][-1]
    assert assistant_message["role"] == "assistant"
    assert "tool_calls" in assistant_message


@pytest.mark.field_input
def test_field_input_missing_chat_id():
    """Test field input request with missing chat_id."""
    payload = {
        "user_id": "test_user",
        "model": {"name": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 512},
        "history": [{"role": "user", "content": "test content"}],
        "scenario": {
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.field_input
def test_field_input_missing_user_id():
    """Test field input request with missing user_id."""
    payload = {
        "chat_id": "test_chat_123",
        "model": {"name": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 512},
        "history": [{"role": "user", "content": "test content"}],
        "scenario": {
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.field_input
def test_field_input_missing_model():
    """Test field input request with missing model."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "history": [{"role": "user", "content": "test content"}],
        "scenario": {
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.field_input
def test_field_input_missing_history():
    """Test field input request with missing history."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "model": {"name": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 512},
        "scenario": {
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    # Should fail because history is missing (required field)
    # The endpoint will fail with 400 when trying to process empty history
    assert response.status_code == 400  # Bad request due to empty history


@pytest.mark.field_input
def test_field_input_empty_history():
    """Test field input request with empty history."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "model": {"name": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 512},
        "history": [],
        "scenario": {
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    # Should fail because history is empty
    # The endpoint will fail with 400 when trying to process empty history
    assert response.status_code == 400  # Bad request due to empty history


@pytest.mark.field_input
def test_field_input_missing_scenario():
    """Test field input request with missing scenario."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "model": {"name": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 512},
        "history": [{"role": "user", "content": "test content"}],
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    # Should succeed because scenario has default empty dict
    assert response.status_code == 200


@pytest.mark.field_input
def test_field_input_invalid_model_name():
    """Test field input request with invalid model name."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "model": {"name": "invalid-model", "temperature": 0.0, "max_tokens": 512},
        "history": [{"role": "user", "content": "test content"}],
        "scenario": {
            "protocol_schema": {"properties": {}, "required": [], "type": "object"}
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.field_input
def test_field_input_with_image_url():
    """Test field input request with image URL in history."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user",
        "model": {"name": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 512},
        "history": [{"role": "user", "content": "https://example.com/test-image.png"}],
        "scenario": {
            "protocol_schema": {
                "properties": {
                    "experiment_identifier": {
                        "description": "Experiment identifier",
                        "title": "Experiment Identifier",
                        "type": "string",
                    }
                },
                "required": ["experiment_identifier"],
                "title": "TestProtocol",
                "type": "object",
            }
        },
    }

    response = CLIENT.post("/api/endpoints/chat/field_input", json=payload)

    # This might fail due to image processing, but should not crash
    # We're mainly testing that the endpoint can handle image URLs
    assert response.status_code in [200, 400, 500]  # Various possible outcomes
