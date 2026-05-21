"""Test configuration for protocol debug module"""

import pytest
from fastapi.testclient import TestClient

from masterbrain.fastapi.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_protocol_debug_input():
    """Sample input for protocol debug testing"""
    return {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456",
        "full_protocol": "# Test Protocol\n\nExperimenter: {{var|experimenter}}\nDate: {{var|date}}\n\n{{step|step1,1}} First step\n{{step|step2,2}} Second step\n{{check|check1}} Check point",
        "suspect_protocol": "{{step|step1,1}} First step\n{{step|step2,2}} Second step",
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
    }
