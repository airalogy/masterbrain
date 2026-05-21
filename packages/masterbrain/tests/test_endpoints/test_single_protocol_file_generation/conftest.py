"""
Configuration for Protocol Generation V3 tests.
"""

import json
from pathlib import Path

import pytest


def pytest_configure(config):
    """Configure pytest markers for Protocol Generation V3 tests."""
    config.addinivalue_line(
        "markers", "protocol_v3: mark test as a Protocol Generation V3 test"
    )


@pytest.fixture(scope="session")
def protocol_v3_test_config():
    """Test configuration for Protocol Generation V3 tests."""
    return {
        "timeout": 60,
        "max_retries": 3,
        "test_models": ["qwen3.5-flash", "qwen3.5-plus", "qwen3-max", "gpt-4o-mini"],
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
    if demo_file.exists():
        with open(demo_file, "r", encoding="utf-8") as f:
            return f.read()
    return None


@pytest.fixture
def sample_instruction():
    """Sample instruction for testing."""
    return "合成金三角形纳米片的实验步骤"


@pytest.fixture
def mock_protocol_v3_request():
    """Mock Protocol V3 request body for testing."""
    from masterbrain.endpoints.single_protocol_file_generation.types import (
        ProtocolMessage,
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

        return ProtocolMessage(
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
