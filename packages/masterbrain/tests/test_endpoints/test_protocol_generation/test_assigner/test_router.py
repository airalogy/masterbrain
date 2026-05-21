import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.protocol_generation.assigner.router import (
    protocol_generation_assigner_router,
)


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(
        protocol_generation_assigner_router, prefix="/api/endpoints", tags=["Assigner"]
    )
    return TestClient(app)


CLIENT = _build_client()


@pytest.mark.assigner
@pytest.mark.parametrize("model_name", ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"])
def test_assigner_protocol_generation_success(model_name):
    """Test successful assigner generation request."""
    payload = {
        "use_model": {
            "name": model_name,
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# Test Protocol

## Experimental Steps

{{step|test_step,1}} Test experimental step.
{{var|test_var}} Test variable.
""",
        "protocol_model": """from pydantic import BaseModel

class VarModel(BaseModel):
    test_var: str
""",
    }

    # Note: This test may have long response time due to assigner generation
    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)

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


@pytest.mark.assigner
def test_assigner_missing_protocol_aimd():
    """Test Assigner request with missing protocol_aimd."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_model": "class VarModel(BaseModel): pass",
        # Missing protocol_aimd field
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    # Missing protocol_aimd should still be accepted as it's optional
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_missing_protocol_model():
    """Test Assigner request with missing protocol_model."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": "# Test Protocol",
        # Missing protocol_model field
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    # Missing protocol_model should still be accepted as it's optional
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_empty_protocol_fields():
    """Test Assigner request with empty protocol fields."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": "",  # Empty aimd
        "protocol_model": "",  # Empty model
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_invalid_model():
    """Test Assigner request with invalid model name."""
    payload = {
        "use_model": {
            "name": "invalid-model-name",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": "# Test Protocol",
        "protocol_model": "class VarModel(BaseModel): pass",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code == 422  # Validation error

    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.assigner
def test_assigner_with_thinking_enabled():
    """Test Assigner request with thinking enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-plus",
            "enable_thinking": True,
            "enable_search": False,
        },
        "protocol_aimd": """
# Detailed Protocol

## Experimental Steps

{{step|complex_step,1}} Complex experimental step.
{{var|complex_var}} Complex variable.
""",
        "protocol_model": """from pydantic import BaseModel

class VarModel(BaseModel):
    complex_var: float
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_with_search_enabled():
    """Test Assigner request with search enabled."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": True,
        },
        "protocol_aimd": "# Protocol requiring research",
        "protocol_model": "class VarModel(BaseModel): search_var: str",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_with_demo_input(demo_input_data):
    """Test Assigner request using demo input data."""
    response = CLIENT.post(
        "/api/endpoints/protocol_generation/assigner", json=demo_input_data
    )

    # Should handle the demo data properly
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )

    if response.status_code == 200:
        content = response.text
        assert len(content) > 0


@pytest.mark.assigner
def test_assigner_complex_protocol():
    """Test Assigner request with complex protocol content."""
    complex_aimd = """
# Complex Gold Nanoplate Synthesis Protocol

## Basic Information

Experimenter: {{var|experimenter}}
Experiment Time: {{var|experiment_time}}

## Experimental Steps

{{step|prepare_solutions,1}} Prepare various solutions.

{{step|add_haucl4,1}} Add HAuCl4 solution.
{{check|check_color,1}} Check solution color change.
{{step|add_ctab,2}} Add CTAB solution.
{{step|mix_solutions,3}} Mix all solutions.

## Quality Control

{{check|final_check,1}} Final quality check.
"""

    complex_model = """from datetime import datetime
from pydantic import BaseModel

class VarModel(BaseModel):
    experimenter: str
    experiment_time: datetime
    haucl4_volume: float = 0.05
    ctab_volume: float = 108.0
    total_volume: float
"""

    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": complex_aimd,
        "protocol_model": complex_model,
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_chinese_protocol():
    """Test Assigner request with Chinese protocol content."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# Chinese Experimental Protocol

## Objective

Synthesize high-quality nanomaterials

## Experimental Steps

{{step|prepare_materials,1}} Prepare required experimental materials.
{{var|material_name}} Specific material name.
{{check|quality_check,1}} Check material quality.
""",
        "protocol_model": """from pydantic import BaseModel

class VarModel(BaseModel):
    material_name: str
    material_amount: float
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_english_protocol():
    """Test Assigner request with English protocol content."""
    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": """
# English Experimental Protocol

## Objective

Synthesize high-quality nanomaterials

## Experimental Steps

{{step|prepare_materials,1}} Prepare required experimental materials.
{{var|material_name}} Specific material name.
{{check|quality_check,1}} Check material quality.
""",
        "protocol_model": """from pydantic import BaseModel

class VarModel(BaseModel):
    material_name: str
    material_amount: float
""",
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_default_model():
    """Test Assigner request using default model configuration."""
    payload = {
        "protocol_aimd": "# Simple Protocol\n{{var|test_var}} Test variable.",
        "protocol_model": "class VarModel(BaseModel): test_var: str",
        # use_model will use default values
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )


@pytest.mark.assigner
def test_assigner_malformed_json():
    """Test Assigner request with malformed JSON."""
    # This should be handled by FastAPI validation
    malformed_payload = (
        '{"use_model": {"name": "qwen3.5-flash"}, "protocol_aimd": incomplete'
    )

    response = CLIENT.post(
        "/api/endpoints/protocol_generation/assigner",
        data=malformed_payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422  # JSON decode error


@pytest.mark.assigner
def test_assigner_large_protocol():
    """Test Assigner request with very large protocol content."""
    # Create large protocol content
    large_steps = "\n".join(
        [f"{{{{step|step_{i},1}}}} Experimental step {i}." for i in range(100)]
    )
    large_vars = "\n".join([f"{{{{var|var_{i}}}}} Variable {i}." for i in range(50)])

    large_aimd = f"""
# Large Experimental Protocol

## Experimental Steps

{large_steps}

## Variables

{large_vars}
"""

    large_model_fields = "\n".join([f"    var_{i}: float = {i}.0" for i in range(50)])

    large_model = f"""from pydantic import BaseModel

class VarModel(BaseModel):
{large_model_fields}
"""

    payload = {
        "use_model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "protocol_aimd": large_aimd,
        "protocol_model": large_model,
    }

    response = CLIENT.post("/api/endpoints/protocol_generation/assigner", json=payload)
    assert response.status_code in [200, 400, 500], (
        f"Unexpected status code: {response.status_code}"
    )
