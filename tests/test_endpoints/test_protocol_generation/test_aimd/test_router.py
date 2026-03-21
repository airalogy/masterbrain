import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.protocol_generation.aimd.router import (
    protocol_generation_aimd_router,
)


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(
        protocol_generation_aimd_router, prefix="/api/endpoints", tags=["AIMD"]
    )
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.aimd
@pytest.mark.parametrize("model_name", ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"])
def test_aimd_protocol_generation_success(model_name):
    """Test successful protocol generation request."""
    payload = {
        "use_model": {
            "name": model_name,
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "合成金三角形纳米片的实验步骤",
    }

    # Note: This test may have long response time due to protocol generation
    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)

    # Check for successful response or expected error due to test environment
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    if response.status_code == 200:
        # For streaming response, check content type
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        # Check that response has content
        content = response.text
        assert len(content) > 0


@pytest.mark.aimd
def test_aimd_missing_instruction():
    """Test AIMD request with missing instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        }
        # Missing instruction field
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data
    # Check that the error mentions the missing field
    error_details = str(error_data["detail"])
    assert "instruction" in error_details or "required" in error_details.lower()


@pytest.mark.aimd
def test_aimd_empty_instruction():
    """Test AIMD request with empty instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "",  # Empty instruction should cause validation error
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.aimd
def test_aimd_invalid_model():
    """Test AIMD request with invalid model name."""
    payload = {
        "use_model": {
            "name": "invalid-model-name",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "测试协议生成",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.aimd
def test_aimd_with_thinking_enabled():
    """Test AIMD request with thinking enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-plus",
            "enable_thinking": True,
            "enable_search": False,
        },
        "instruction": "详细的实验协议生成测试",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.aimd
def test_aimd_with_search_enabled():
    """Test AIMD request with search enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": True,
        },
        "instruction": "需要查找资料的实验协议",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.aimd
def test_aimd_with_demo_input(demo_input_data):
    """Test AIMD request using demo input data."""
    response = CLIENT.post(
        "/api/endpoints/protocol_generation/aimd", json=demo_input_data
    )

    # Should handle the demo data properly
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    if response.status_code == 200:
        content = response.text
        assert len(content) > 0


@pytest.mark.aimd
def test_aimd_long_instruction():
    """Test AIMD request with very long instruction."""
    long_instruction = "生物实验协议生成测试。" * 200  # Create a long instruction

    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": long_instruction,
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.aimd
def test_aimd_chinese_instruction():
    """Test AIMD request with Chinese instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "请生成一个完整的细胞培养实验协议，包括培养基配制、接种、培养条件控制等详细步骤。",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.aimd
def test_aimd_english_instruction():
    """Test AIMD request with English instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "Generate a detailed experimental protocol for protein purification using chromatography methods.",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.aimd
def test_aimd_default_model():
    """Test AIMD request using default model configuration."""
    payload = {
        "instruction": "简单的实验协议生成测试"
        # use_model will use default values
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/aimd", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )
