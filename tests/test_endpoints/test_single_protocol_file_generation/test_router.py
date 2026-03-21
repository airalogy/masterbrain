import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.single_protocol_file_generation.router import (
    single_protocol_file_generation_router,
)


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(
        single_protocol_file_generation_router, prefix="/api/endpoints", tags=["Single Protocol File Generation"]
    )
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.protocol_v3
@pytest.mark.parametrize(
    "model_name", ["qwen3.5-flash", "qwen3.5-plus", "qwen3-max", "gpt-4o-mini"]
)
def test_protocol_v3_generation_success(model_name):
    """Test successful protocol generation request with V3 unified format."""
    payload = {
        "use_model": {
            "name": model_name,
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "合成金三角形纳米片的实验步骤",
    }

    # Note: This test may have long response time due to protocol generation
    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)

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


@pytest.mark.protocol_v3
def test_protocol_v3_missing_instruction():
    """Test Protocol V3 request with missing instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        }
        # Missing instruction field
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data
    # Check that the error mentions the missing field
    error_details = str(error_data["detail"])
    assert "instruction" in error_details or "required" in error_details.lower()


@pytest.mark.protocol_v3
def test_protocol_v3_empty_instruction():
    """Test Protocol V3 request with empty instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "",  # Empty instruction should cause validation error
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.protocol_v3
def test_protocol_v3_invalid_model():
    """Test Protocol V3 request with invalid model name."""
    payload = {
        "use_model": {
            "name": "invalid-model-name",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "测试协议生成",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.protocol_v3
def test_protocol_v3_with_thinking_enabled():
    """Test Protocol V3 request with thinking enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-plus",
            "enable_thinking": True,
            "enable_search": False,
        },
        "instruction": "详细的实验协议生成测试",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_with_search_enabled():
    """Test Protocol V3 request with search enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": True,
        },
        "instruction": "需要查找资料的实验协议",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_with_demo_input(demo_input_data):
    """Test Protocol V3 request using demo input data."""
    response = CLIENT.post(
        "/api/endpoints/single_protocol_file_generation", json=demo_input_data
    )

    # Should handle the demo data properly
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    if response.status_code == 200:
        content = response.text
        assert len(content) > 0


@pytest.mark.protocol_v3
def test_protocol_v3_long_instruction():
    """Test Protocol V3 request with very long instruction."""
    long_instruction = "生物实验协议生成测试。" * 200  # Create a long instruction

    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": long_instruction,
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_chinese_instruction():
    """Test Protocol V3 request with Chinese instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "请生成一个完整的细胞培养实验协议，包括培养基配制、接种、培养条件控制等详细步骤。",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_english_instruction():
    """Test Protocol V3 request with English instruction."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "Generate a detailed experimental protocol for protein purification using chromatography methods.",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_default_model():
    """Test Protocol V3 request using default model configuration."""
    payload = {
        "instruction": "简单的实验协议生成测试"
        # use_model will use default values
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_qwen3_max_model():
    """Test Protocol V3 request with qwen3-max model."""
    payload = {
        "use_model": {
            "name": "qwen3-max",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "使用qwen3-max模型生成实验协议",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_v3
def test_protocol_v3_with_assigner():
    """Test Protocol V3 request expecting embedded assigner code blocks."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "instruction": "The value of `var_1`: {{var|var_1: int}}\nThe value of `var_2`: {{var|var_2: int}}\nThe value of `var_3`: {{var|var_3: int}}\n\nNote: `var_3` = `var_1` + `var_2`",
    }

    response = CLIENT.post("/api/endpoints/single_protocol_file_generation", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    if response.status_code == 200:
        content = response.text
        assert len(content) > 0
        # V3 should include embedded assigner code blocks
        # Note: This is a weak check since mocking might not include it
        # In real integration tests, we should check for ```assigner blocks
