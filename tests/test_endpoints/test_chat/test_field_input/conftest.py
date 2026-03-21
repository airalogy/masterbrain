"""
Configuration for Field Input tests.
"""

import pytest

from masterbrain.endpoints.chat.field_input.types import (
    FieldInputRequest,
    ModelConfig,
    SupportedModels,
)


def pytest_configure(config):
    """Configure pytest markers for Field Input tests."""
    config.addinivalue_line("markers", "field_input: mark test as a Field Input test")
    config.addinivalue_line(
        "markers",
        "e2e: mark test as an end-to-end test that calls real LLM APIs (requires API keys)",
    )


@pytest.fixture(scope="session")
def field_input_test_config():
    """Test configuration for Field Input tests."""
    return {
        "timeout": 60,
        "max_retries": 3,
        "test_models": ["gpt-4o-mini", "qwen3.5-flash"],
    }


@pytest.fixture
def sample_protocol_schema():
    """Sample protocol schema for testing."""
    return {
        "$defs": {
            "ExperimentResult": {
                "description": "Model for experiment result.",
                "properties": {
                    "experiment_identifier": {
                        "title": "Experiment Identifier",
                        "type": "string",
                    },
                    "experiment_success": {
                        "title": "Experiment Success",
                        "type": "boolean",
                    },
                    "result_description": {
                        "default": "",
                        "title": "Result Description",
                        "type": "string",
                    },
                },
                "required": ["experiment_identifier", "experiment_success"],
                "title": "ExperimentResult",
                "type": "object",
            }
        },
        "description": "Test Protocol Schema",
        "properties": {
            "experimenter_name": {
                "description": "The name of the experimenter",
                "title": "Experimenter Name",
                "type": "string",
            },
            "experiment_time": {
                "description": "The time of the experiment",
                "format": "date-time",
                "title": "Experiment Time",
                "type": "string",
            },
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
        "required": [
            "experimenter_name",
            "experiment_time",
            "forward_primer_volume",
            "reverse_primer_volume",
        ],
        "title": "TestProtocol",
        "type": "object",
    }


@pytest.fixture
def mock_field_input_request():
    """Mock field input request for testing."""

    def _create_request(
        chat_id="test_chat_123",
        user_id="test_user",
        model_name="gpt-4o-mini",
        history=None,
        scenario=None,
    ):
        if history is None:
            history = [
                {
                    "role": "user",
                    "content": "forward_primer_volume是50；reverse_primer_volume是150。",
                }
            ]

        if scenario is None:
            scenario = {
                "protocol_schema": {
                    "$defs": {
                        "ExperimentResult": {
                            "description": "Model for experiment result.",
                            "properties": {
                                "experiment_identifier": {
                                    "title": "Experiment Identifier",
                                    "type": "string",
                                },
                                "experiment_success": {
                                    "title": "Experiment Success",
                                    "type": "boolean",
                                },
                            },
                            "required": ["experiment_identifier", "experiment_success"],
                            "title": "ExperimentResult",
                            "type": "object",
                        }
                    },
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
            }

        return FieldInputRequest(
            chat_id=chat_id,
            user_id=user_id,
            model=ModelConfig(name=model_name),
            history=history,
            scenario=scenario,
        )

    return _create_request


@pytest.fixture
def sample_image_url():
    """Sample image URL for testing."""
    return "https://example.com/test-image.png"


@pytest.fixture
def sample_base64_image():
    """Sample base64 encoded image for testing."""
    # Minimal base64 encoded image data
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
