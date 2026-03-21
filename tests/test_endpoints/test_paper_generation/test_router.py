"""Test paper generation router"""

import pytest
from fastapi.testclient import TestClient


def test_paper_generation_endpoint_without_ref(
    client: TestClient, paper_generation_input_without_ref: dict
):
    """Test paper generation endpoint without external reference search"""
    response = client.post(
        "/api/endpoints/paper_generation", json=paper_generation_input_without_ref
    )

    assert response.status_code == 200

    # Parse response
    response_data = response.json()

    # Check that the response contains the expected field
    assert "paper_markdown" in response_data

    # Verify paper structure
    paper = response_data["paper_markdown"]
    assert "# " in paper  # Has title
    assert "## Abstract" in paper
    assert "## Introduction" in paper
    assert "## Methods" in paper
    assert "## Results" in paper
    assert "## Discussion" in paper


def test_paper_generation_endpoint_with_ref(
    client: TestClient, paper_generation_input_with_ref: dict
):
    """Test paper generation endpoint with external reference search"""
    response = client.post(
        "/api/endpoints/paper_generation", json=paper_generation_input_with_ref
    )

    assert response.status_code == 200

    response_data = response.json()
    assert "paper_markdown" in response_data

    # When search is enabled, the paper might include references
    paper = response_data["paper_markdown"]
    assert "## Abstract" in paper


def test_paper_generation_with_invalid_model(client: TestClient):
    """Test paper generation with invalid model"""
    input_data = {
        "protocol_markdown_list": ["# Test Protocol"],
        "model": {
            "name": "invalid-model",
            "enable_thinking": False,
            "enable_search": False,
        },
        "enable_external_reference_search": False,
    }

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    # Should return 422 for validation error
    assert response.status_code == 422


def test_paper_generation_with_empty_protocol_list(client: TestClient):
    """Test paper generation with empty protocol list"""
    input_data = {
        "protocol_markdown_list": [],
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "enable_external_reference_search": False,
    }

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    # Should return 422 for validation error (min_items=1)
    assert response.status_code == 422


def test_paper_generation_with_multiple_protocols(
    client: TestClient, sample_protocol_markdown: str
):
    """Test paper generation with multiple protocols"""
    input_data = {
        "protocol_markdown_list": [
            sample_protocol_markdown,
            "# Protocol 2\n\nContent for protocol 2",
        ],
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "enable_external_reference_search": False,
    }

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    assert response.status_code == 200
    response_data = response.json()
    assert "paper_markdown" in response_data


def test_paper_generation_response_structure(
    client: TestClient, paper_generation_input_without_ref: dict
):
    """Test that paper generation response has correct structure"""
    response = client.post(
        "/api/endpoints/paper_generation", json=paper_generation_input_without_ref
    )

    assert response.status_code == 200
    response_data = response.json()

    # Validate response structure
    assert "paper_markdown" in response_data
    assert isinstance(response_data["paper_markdown"], str)
    assert len(response_data["paper_markdown"]) > 0


def test_paper_generation_with_different_models(
    client: TestClient, sample_protocol_markdown: str
):
    """Test paper generation with different supported models"""
    models = ["qwen3.5-flash", "qwen3.5-plus", "qwen-max", "gpt-4o-mini"]

    for model_name in models:
        input_data = {
            "protocol_markdown_list": [sample_protocol_markdown],
            "model": {
                "name": model_name,
                "enable_thinking": False,
                "enable_search": False,
            },
            "enable_external_reference_search": False,
        }

        response = client.post("/api/endpoints/paper_generation", json=input_data)
        assert response.status_code == 200, f"Failed for model: {model_name}"


def test_paper_generation_default_values(
    client: TestClient, sample_protocol_markdown: str
):
    """Test paper generation with default values"""
    # Only provide required fields
    input_data = {"protocol_markdown_list": [sample_protocol_markdown]}

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    assert response.status_code == 200
    response_data = response.json()
    assert "paper_markdown" in response_data
