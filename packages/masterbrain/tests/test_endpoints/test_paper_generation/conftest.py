"""Test configuration for paper generation module"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from masterbrain.fastapi.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_data_dir():
    """Get test data directory path"""
    return Path(__file__).parent


@pytest.fixture
def sample_protocol_markdown(test_data_dir):
    """Load sample protocol markdown"""
    protocol_file = test_data_dir / "example_input_protocol.md"
    with open(protocol_file, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def paper_generation_input_with_ref(test_data_dir):
    """Load paper generation input with external reference search enabled"""
    input_file = test_data_dir / "test_input_with_ref.json"
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def paper_generation_input_without_ref(test_data_dir):
    """Load paper generation input without external reference search"""
    input_file = test_data_dir / "test_input_without_ref.json"
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def expected_output_paper(test_data_dir):
    """Load expected output paper"""
    output_file = test_data_dir / "example_output_paper.md"
    with open(output_file, "r", encoding="utf-8") as f:
        return f.read()

