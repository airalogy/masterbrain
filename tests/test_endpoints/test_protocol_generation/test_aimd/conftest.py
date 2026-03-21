"""
Configuration for AIMD tests.
"""

import json
from pathlib import Path

import pytest


def pytest_configure(config):
    """Configure pytest markers for AIMD tests."""
    config.addinivalue_line(
        "markers", "aimd: mark test as an AIMD (Protocol Generation) test"
    )


@pytest.fixture(scope="session")
def aimd_test_config():
    """Test configuration for AIMD tests."""
    return {
        "timeout": 60,
        "max_retries": 3,
        "test_models": ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"],
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
def sample_instruction():
    """Sample instruction for testing."""
    return "合成金三角形纳米片的实验步骤"


@pytest.fixture
def mock_aimd_request():
    """Mock AIMD request body for testing."""
    from masterbrain.endpoints.protocol_generation.aimd.types import (
        AimdProtocolMessage,
        SupportedModels,
    )

    def _create_request(
        model_name="qwen3.5-flash",
        instruction=None,
        enable_thinking=False,
        enable_search=False,
    ):
        if instruction is None:
            instruction = "合成金三角形纳米片的实验步骤"

        return AimdProtocolMessage(
            use_model=SupportedModels(
                name=model_name,
                enable_thinking=enable_thinking,
                enable_search=enable_search,
            ),
            instruction=instruction,
        )

    return _create_request


@pytest.fixture
def sample_protocol_history():
    """Sample conversation history for protocol generation."""
    return [
        {
            "role": "system",
            "content": "You are an AI assistant specialized in experimental protocol generation.",
        }
    ]
