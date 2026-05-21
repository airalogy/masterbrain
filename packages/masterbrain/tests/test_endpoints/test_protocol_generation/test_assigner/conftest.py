"""
Configuration for Assigner tests.
"""

import json
from pathlib import Path

import pytest


def pytest_configure(config):
    """Configure pytest markers for Assigner tests."""
    config.addinivalue_line(
        "markers", "assigner: mark test as an Assigner (Protocol Generation) test"
    )


@pytest.fixture(scope="session")
def assigner_test_config():
    """Test configuration for Assigner tests."""
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
def sample_protocol_aimd():
    """Sample protocol AIMD content for testing."""
    return """
# Gold Triangular Nanoplate Synthesis

## Description

This Airalogy protocol describes how to synthesize gold triangular nanoplates, including preparation of seed and growth solutions and final nanoplate synthesis.

## Basic Information

Experimenter: {{var|experimenter}}
Experiment Time: {{var|experiment_time}}

## Experimental Steps

{{step|prepare_seed_solution,1}} Prepare seed solution.

{{step|add_water_to_seed,1}} Add 50 μL of HAuCl4 (20 mM) to 4.75 mL deionized water (DI water).
{{step|add_citrate_to_seed,1}} Add 100 μL of sodium citrate solution (10 mM).
{{check|check_seed_temp,1}} Note: Avoid storing the mixture above 35°C.

{{step|prepare_growth_solution,1}} Prepare growth solution.
{{step|add_ctab_to_growth,1}} Place 108 mL of CTAB (0.025 M) solution in a container.
{{step|add_hauchl4_to_growth,1}} Add 1.5 mL HAuCl4 (20 mM) to the CTAB solution.
"""


@pytest.fixture
def sample_protocol_model():
    """Sample protocol model content for testing."""
    return """from datetime import datetime, time

from pydantic import BaseModel


class VarModel(BaseModel):
    experimenter: str
    experiment_time: datetime
    seed_volume_haucl4: float = 0.05
    seed_volume_citrate: float = 0.1
    growth_volume_ctab: float = 108.0
    growth_volume_haucl4: float = 0.15
"""


@pytest.fixture
def mock_assigner_request():
    """Mock Assigner request body for testing."""
    from masterbrain.endpoints.protocol_generation.assigner.types import (
        AssignerProtocolMessage,
        SupportedModels,
    )

    def _create_request(
        model_name="qwen3.5-flash",
        protocol_aimd=None,
        protocol_model=None,
        enable_thinking=False,
        enable_search=False,
    ):
        if protocol_aimd is None:
            protocol_aimd = """
# Test Protocol

## Experimental Steps

{{step|test_step,1}} Test experimental step.
{{var|test_var}} Test variable.
"""

        if protocol_model is None:
            protocol_model = """from pydantic import BaseModel

class VarModel(BaseModel):
    test_var: str
"""

        return AssignerProtocolMessage(
            use_model=SupportedModels(
                name=model_name,
                enable_thinking=enable_thinking,
                enable_search=enable_search,
            ),
            protocol_aimd=protocol_aimd,
            protocol_model=protocol_model,
        )

    return _create_request


@pytest.fixture
def sample_assigner_history():
    """Sample conversation history for assigner generation."""
    return [
        {
            "role": "system",
            "content": "You are an AI assistant specialized in generating executable assigner.py files.",
        }
    ]
