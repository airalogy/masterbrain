"""Integration tests for paper generation

These tests verify the complete paper generation flow with real LLM calls.
Mark with @pytest.mark.integration to skip in CI/CD pipelines.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_paper_generation_without_search(
    client: TestClient, sample_protocol_markdown: str
):
    """Test complete paper generation without external search"""
    input_data = {
        "protocol_markdown_list": [sample_protocol_markdown],
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "enable_external_reference_search": False,
    }

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    assert response.status_code == 200

    response_data = response.json()
    paper = response_data["paper_markdown"]

    # Verify all sections are present
    assert "# " in paper
    assert "## Abstract" in paper
    assert "## Introduction" in paper
    assert "## Methods" in paper
    assert "## Results" in paper
    assert "## Discussion" in paper

    # Verify paper has substantial content
    assert len(paper) > 1000  # At least 1000 characters

    # Verify no escaped newlines in output
    assert "\\n" not in paper
    assert "\\t" not in paper


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_paper_generation_with_search(
    client: TestClient, sample_protocol_markdown: str
):
    """Test complete paper generation with external search"""
    input_data = {
        "protocol_markdown_list": [sample_protocol_markdown],
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "enable_external_reference_search": True,
    }

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    assert response.status_code == 200

    response_data = response.json()
    paper = response_data["paper_markdown"]

    # Verify all sections are present
    assert "## Abstract" in paper
    assert "## Introduction" in paper
    assert "## Methods" in paper
    assert "## Results" in paper
    assert "## Discussion" in paper

    # When search is enabled, references might be included
    # Note: This depends on whether the search finds relevant papers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_paper_generation_with_multiple_protocols(client: TestClient):
    """Test paper generation with multiple protocols"""
    protocols = [
        """# Protocol 1: Cell Culture
        
## Materials
- DMEM medium
- FBS
- Cell line: HEK293

## Procedure
1. Prepare culture medium
2. Seed cells at 1×10⁵ cells/mL
3. Incubate at 37°C for 24h

## Results
Cell viability: 95%
""",
        """# Protocol 2: Western Blot
        
## Materials  
- Protein samples
- PVDF membrane
- Antibodies

## Procedure
1. Run SDS-PAGE
2. Transfer to PVDF
3. Block and probe

## Results
Target protein detected at 50 kDa
""",
    ]

    input_data = {
        "protocol_markdown_list": protocols,
        "model": {
            "name": "qwen3.5-flash",
            "enable_thinking": False,
            "enable_search": False,
        },
        "enable_external_reference_search": False,
    }

    response = client.post("/api/endpoints/paper_generation", json=input_data)

    assert response.status_code == 200

    response_data = response.json()
    paper = response_data["paper_markdown"]

    # Verify paper structure
    assert "## Methods" in paper
    assert "## Results" in paper

    # Paper should integrate content from both protocols
    assert len(paper) > 1000
