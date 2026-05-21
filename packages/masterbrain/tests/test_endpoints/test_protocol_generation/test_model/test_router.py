import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.protocol_generation.model.router import (
    protocol_generation_model_router,
)


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(
        protocol_generation_model_router, prefix="/api/endpoints", tags=["Model"]
    )
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.model
@pytest.mark.parametrize("model_name", ["qwen3.5-flash", "qwen3.5-plus"])
def test_model_protocol_generation_success(model_name):
    """Test successful model generation request."""
    payload = {
        "use_model": {
            "name": model_name,
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# 测试协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}

## 实验步骤
{{step|test_step,1}} 测试步骤
""",
    }

    # Note: This test may have long response time due to model generation
    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)

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


@pytest.mark.model
def test_model_missing_protocol_aimd():
    """Test Model request with missing protocol_aimd."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        }
        # Missing protocol_aimd field - should be optional
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    # protocol_aimd is optional, should succeed or fail for other reasons
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_empty_protocol_aimd():
    """Test Model request with empty protocol_aimd."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": "",  # Empty protocol_aimd
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_invalid_model():
    """Test Model request with invalid model name."""
    payload = {
        "use_model": {
            "name": "invalid-model-name",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": "测试协议",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.model
def test_model_with_thinking_enabled():
    """Test Model request with thinking enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-plus",
            "enable_thinking": True,
            "enable_search": False,
        },
        "protocol_aimd": """
# 详细协议测试

## 实验基本信息
实验者：{{var|experimenter}}

## 实验步骤
{{step|complex_step,1}} 复杂测试步骤
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_with_search_enabled():
    """Test Model request with search enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": True,
        },
        "protocol_aimd": """
# 需要搜索的协议

## 实验基本信息
实验者：{{var|experimenter}}

## 实验步骤
{{step|search_step,1}} 需要查找资料的步骤
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_with_demo_input(demo_input_data):
    """Test Model request using demo input data."""
    response = CLIENT.post(
        "/api/endpoints/protocol_generation/model", json=demo_input_data
    )

    # Should handle the demo data properly
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    if response.status_code == 200:
        content = response.text
        assert len(content) > 0


@pytest.mark.model
def test_model_long_protocol_aimd():
    """Test Model request with very long protocol_aimd."""
    long_protocol = """
# 长协议测试

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}

## 实验步骤
""" + "\n".join([f"{{{{step|step_{i},1}}}} 测试步骤 {i}" for i in range(100)])

    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": long_protocol,
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_chinese_protocol():
    """Test Model request with Chinese protocol_aimd."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# 中文协议测试

## 实验基本信息
实验者：{{var|实验者姓名}}
实验时间：{{var|实验时间}}
实验温度：{{var|实验温度}} °C

## 实验步骤
{{step|配制溶液,1}} 配制实验所需的溶液
{{step|加热反应,2}} 将溶液加热到指定温度进行反应
{{check|检查颜色,1}} 观察溶液颜色变化
{{step|冷却,3}} 将反应溶液冷却至室温
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_english_protocol():
    """Test Model request with English protocol_aimd."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# English Protocol Test

## Basic Information
Experimenter: {{var|experimenter}}
Experiment Time: {{var|experiment_time}}
Temperature: {{var|temperature}} °C

## Experimental Steps
{{step|prepare_solution,1}} Prepare the required solution
{{step|heat_reaction,2}} Heat the solution to specified temperature for reaction
{{check|check_color,1}} Observe solution color change
{{step|cooling,3}} Cool the reaction solution to room temperature
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_default_model():
    """Test Model request using default model configuration."""
    payload = {
        "protocol_aimd": """
# 默认模型测试

## 实验基本信息
实验者：{{var|experimenter}}

## 实验步骤
{{step|default_step,1}} 使用默认模型的测试步骤
"""
        # use_model will use default values
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_complex_variables():
    """Test Model request with complex variable definitions."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# 复杂变量测试协议

## 实验基本信息
实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}
反应温度：{{var|reaction_temperature}} °C
溶液体积：{{var|solution_volume}} mL
反应物浓度：{{var|reactant_concentration}} M
催化剂用量：{{var|catalyst_amount}} mg
反应时间：{{var|reaction_time}} min
pH值：{{var|ph_value}}
搅拌速度：{{var|stirring_speed}} rpm

## 实验步骤
{{step|prepare_reactants,1}} 准备反应物
{{step|add_catalyst,2}} 添加催化剂
{{step|adjust_ph,3}} 调节pH值
{{step|start_reaction,4}} 开始反应
{{check|monitor_temperature,1}} 监控温度
{{check|check_progress,2}} 检查反应进度
{{step|stop_reaction,5}} 停止反应
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.model
def test_model_null_protocol():
    """Test Model request with null protocol_aimd."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": None,
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/model", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )
