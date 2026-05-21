"""Test configuration for the code edit endpoint."""

import pytest
from fastapi.testclient import TestClient

from masterbrain.fastapi.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_code_edit_input():
    """Sample input for code edit tests."""
    return {
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
        },
        "prompt": "Please update the selected step to collect the sample twice.",
        "files": [
            {
                "path": "protocol.aimd",
                "content": "# Protocol\n\n{{step|sample,1}} Collect sample once.\n",
                "type": "aimd",
            },
            {
                "path": "model.py",
                "content": "def build_model():\n    return 'sample'\n",
                "type": "py",
            },
        ],
        "active_file_path": "protocol.aimd",
        "selection": {
            "text": "{{step|sample,1}} Collect sample once.",
            "start_offset": 12,
            "end_offset": 50,
        },
        "chat_history": [
            {"role": "user", "content": "Make the sampling step repeatable."},
            {"role": "assistant", "content": "I can update the protocol once you confirm the exact step."},
        ],
    }
