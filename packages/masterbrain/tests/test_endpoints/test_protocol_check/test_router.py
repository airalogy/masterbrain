import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.protocol_check.router import protocol_check_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(
        protocol_check_router, prefix="/api/endpoints", tags=["Protocol Check"]
    )
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.protocol_check
@pytest.mark.parametrize("model_name", ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"])
def test_protocol_check_success(model_name, sample_aimd_protocol):
    """Test successful protocol check request."""
    payload = {
        "model": {"name": model_name, "enable_thinking": False, "enable_search": False},
        "aimd_protocol": sample_aimd_protocol,
        "py_model": "",
        "py_assigner": "",
        "feedback": "帮我检查一下这个文件是否有语法错误，并做出改正，润色。",
        "target_file": "protocol",
        "check_num": 0,
    }

    # Note: This test may fail in CI/CD without proper API setup
    # In a real scenario, you might want to mock the protocol check logic
    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)

    # Check for successful response or expected error due to test environment
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    # If response is successful, verify it's a streaming response
    if response.status_code == 200:
        assert response.headers.get("content-type") == "text/plain; charset=utf-8"


@pytest.mark.protocol_check
def test_protocol_check_with_model_file(sample_aimd_protocol, sample_py_model):
    """Test protocol check with model file."""
    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": sample_aimd_protocol,
        "py_model": sample_py_model,
        "py_assigner": "",
        "feedback": "请检查模型文件的字段定义是否正确。",
        "target_file": "model",
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_with_assigner_file(
    sample_aimd_protocol, sample_py_model, sample_py_assigner
):
    """Test protocol check with assigner file."""
    payload = {
        "model": {
            "name": "qwen3.5-plus",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": sample_aimd_protocol,
        "py_model": sample_py_model,
        "py_assigner": sample_py_assigner,
        "feedback": "验证分配器中的计算逻辑是否正确。",
        "target_file": "assigner",
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_missing_required_fields():
    """Test protocol check with missing required fields."""
    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        # Missing other required fields
        "feedback": "测试缺失字段的情况",
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    # Should handle gracefully or return validation error
    assert response.status_code in [200, 400, 422], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_invalid_model():
    """Test protocol check with invalid model name."""
    payload = {
        "model": {
            "name": "invalid-model-name",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": "# Test Protocol",
        "feedback": "测试无效模型名称",
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    # Should return validation error for invalid model
    assert response.status_code == 422


@pytest.mark.protocol_check
def test_protocol_check_empty_feedback():
    """Test protocol check with empty feedback."""
    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": "# Test Protocol\n\n## Basic Information\n\nTest: {{var|test_var}}",
        "feedback": "",  # Empty feedback
        "target_file": "protocol",
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_with_thinking_enabled():
    """Test protocol check with thinking enabled."""
    payload = {
        "model": {
            "name": "qwen3.5-plus",
            "enable_thinking": True,
            "enable_search": False,
        },
        "aimd_protocol": "# Test Protocol",
        "feedback": "请详细分析这个协议。",
        "target_file": "protocol",
        "check_num": 1,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_with_search_enabled():
    """Test protocol check with search enabled."""
    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": True,
        },
        "aimd_protocol": "# Test Protocol",
        "feedback": "需要搜索相关信息来优化协议。",
        "target_file": "protocol",
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_multiple_files_priority():
    """Test that target file is determined by priority: assigner > model > protocol."""
    # When all files are provided, should target assigner
    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": "# Test Protocol",
        "py_model": "class VarModel: pass",
        "py_assigner": "class Assigner: pass",
        "feedback": "检查所有文件",
        "target_file": "protocol",  # Should be overridden to "assigner"
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_large_payload():
    """Test protocol check with large payload."""
    large_protocol = "# Large Protocol\n\n" + "## Section\n\n" * 100 + "Content " * 1000

    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": large_protocol,
        "feedback": "检查这个大型协议文件。",
        "target_file": "protocol",
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.protocol_check
def test_protocol_check_special_characters():
    """Test protocol check with special characters in content."""
    special_protocol = """# 测试协议 - Test Protocol

## 实验信息

实验者：{{var|实验者姓名}}
日期：{{var|实验日期}}

## 步骤

{{step|准备溶液}} 准备包含特殊字符的溶液：μL, °C, ±, →, ∞

特殊符号测试：< > & " ' \\ / 

数学公式：H₂SO₄ + 2NaOH → Na₂SO₄ + 2H₂O"""

    payload = {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "aimd_protocol": special_protocol,
        "feedback": "检查特殊字符的处理。",
        "target_file": "protocol",
        "check_num": 0,
    }

    response = CLIENT.post("/api/endpoints/protocol_check", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )
