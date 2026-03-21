"""
Configuration for Model tests.
"""

import json
from pathlib import Path

import pytest


def pytest_configure(config):
    """Configure pytest markers for Model tests."""
    config.addinivalue_line(
        "markers", "model: mark test as a Model (Protocol Generation) test"
    )


@pytest.fixture(scope="session")
def model_test_config():
    """Test configuration for Model tests."""
    return {
        "timeout": 60,
        "max_retries": 3,
        "test_models": ["qwen3.5-flash", "qwen3.5-plus"],
    }


@pytest.fixture
def demo_input_data():
    """Load demo input data from demo_input.json."""
    demo_file = Path(__file__).parent / "demo_input.json"
    with open(demo_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def demo_output_data():
    """Load demo output data from demo_output.txt."""
    demo_file = Path(__file__).parent / "demo_output.txt"
    with open(demo_file, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_protocol_aimd():
    """Sample protocol_aimd content for testing."""
    return """
# 金三角形纳米片合成

## 说明

本 Airalogy 协议描述了如何合成金三角形纳米片。

## 实验基本信息

实验者：{{var|experimenter}}
实验时间：{{var|experiment_time}}

## 实验步骤

{{step|prepare_seed_solution,1}} 配制种子溶液。
{{step|add_water_to_seed,1}} 向4.75 mL去离子水中加入50 μL的HAuCl4（20 mM）。
{{check|check_seed_temp,1}} 注意：避免将混合物储存在高于35℃的环境中。
"""


@pytest.fixture
def mock_model_request():
    """Mock Model request body for testing."""
    from masterbrain.endpoints.protocol_generation.model.types import (
        ModelProtocolMessage,
        SupportedModels,
    )

    def _create_request(
        model_name="qwen3.5-flash",
        protocol_aimd=None,
        enable_thinking=False,
        enable_search=False,
    ):
        if protocol_aimd is None:
            protocol_aimd = """
# 测试协议

## 实验基本信息
实验者：{{var|experimenter}}

## 实验步骤
{{step|test_step,1}} 测试步骤
"""

        return ModelProtocolMessage(
            use_model=SupportedModels(
                name=model_name,
                enable_thinking=enable_thinking,
                enable_search=enable_search,
            ),
            protocol_aimd=protocol_aimd,
        )

    return _create_request


@pytest.fixture
def sample_model_history():
    """Sample conversation history for model generation."""
    return [
        {
            "role": "system",
            "content": "You are an AI assistant specialized in converting protocol.aimd to model.py format.",
        }
    ]


@pytest.fixture
def expected_model_output():
    """Expected model.py output structure for validation."""
    return """from pydantic import BaseModel, Field

from airalogy.built_in_types import CurrentTime, UserName


class VarModel(BaseModel):
    experimenter: UserName
    experiment_time: CurrentTime
    # Additional fields based on protocol
"""
