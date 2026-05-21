"""Test paper generation types"""

import pytest
from pydantic import ValidationError

from masterbrain.endpoints.paper_generation.types import (
    DEFAULT_MODEL,
    PaperGenerationInput,
    PaperGenerationOutput,
    SupportedModels,
)


class TestSupportedModels:
    """Test SupportedModels class"""

    def test_valid_model_names(self):
        """Test valid model names"""
        valid_names = [
            "qwen3.5-flash",
            "qwen3.5-plus",
            "qwen-max",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4o",
            "gpt-4o-mini",
        ]

        for name in valid_names:
            model = SupportedModels(name=name)
            assert model.name == name
            assert model.enable_thinking is False
            assert model.enable_search is False

    def test_invalid_model_name(self):
        """Test invalid model name"""
        with pytest.raises(ValidationError):
            SupportedModels(name="invalid-model")

    def test_model_with_options(self):
        """Test model with thinking and search enabled"""
        model = SupportedModels(
            name="qwen3.5-flash", enable_thinking=True, enable_search=True
        )
        assert model.enable_thinking is True
        assert model.enable_search is True

    def test_default_model(self):
        """Test default model configuration"""
        assert DEFAULT_MODEL.name == "qwen3.5-flash"
        assert DEFAULT_MODEL.enable_thinking is False
        assert DEFAULT_MODEL.enable_search is False


class TestPaperGenerationInput:
    """Test PaperGenerationInput class"""

    def test_valid_input(self):
        """Test valid paper generation input"""
        input_data = PaperGenerationInput(
            protocol_markdown_list=["# Test Protocol\n\nSome content"],
            model=SupportedModels(name="qwen3.5-flash"),
            enable_external_reference_search=True,
        )

        assert len(input_data.protocol_markdown_list) == 1
        assert input_data.model.name == "qwen3.5-flash"
        assert input_data.enable_external_reference_search is True

    def test_default_values(self):
        """Test default values"""
        input_data = PaperGenerationInput(protocol_markdown_list=["# Test Protocol"])

        assert input_data.model.name == "qwen3.5-flash"
        assert input_data.enable_external_reference_search is False

    def test_empty_protocol_list(self):
        """Test empty protocol list validation"""
        with pytest.raises(ValidationError):
            PaperGenerationInput(protocol_markdown_list=[])

    def test_multiple_protocols(self):
        """Test multiple protocols"""
        input_data = PaperGenerationInput(
            protocol_markdown_list=["# Protocol 1", "# Protocol 2", "# Protocol 3"]
        )

        assert len(input_data.protocol_markdown_list) == 3

    def test_with_external_reference_search(self):
        """Test with external reference search enabled"""
        input_data = PaperGenerationInput(
            protocol_markdown_list=["# Test"], enable_external_reference_search=True
        )

        assert input_data.enable_external_reference_search is True


class TestPaperGenerationOutput:
    """Test PaperGenerationOutput class"""

    def test_valid_output(self):
        """Test valid paper generation output"""
        output = PaperGenerationOutput(
            paper_markdown="# Test Paper\n\n## Abstract\n\nSome content"
        )

        assert output.paper_markdown.startswith("# Test Paper")

    def test_empty_output(self):
        """Test empty output"""
        output = PaperGenerationOutput(paper_markdown="")
        assert output.paper_markdown == ""
