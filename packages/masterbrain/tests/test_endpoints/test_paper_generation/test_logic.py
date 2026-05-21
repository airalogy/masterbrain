"""Test paper generation logic"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from masterbrain.endpoints.paper_generation.logic.generate_paper import (
    clean_markdown,
    generate_paper,
)
from masterbrain.endpoints.paper_generation.types import SupportedModels


class TestCleanMarkdown:
    """Test clean_markdown function"""

    def test_clean_escaped_newlines(self):
        """Test cleaning escaped newlines"""
        input_text = "Line 1\\nLine 2\\nLine 3"
        expected = "Line 1\nLine 2\nLine 3"
        assert clean_markdown(input_text) == expected

    def test_clean_escaped_tabs(self):
        """Test cleaning escaped tabs"""
        input_text = "Column1\\tColumn2\\tColumn3"
        expected = "Column1\tColumn2\tColumn3"
        assert clean_markdown(input_text) == expected

    def test_clean_mixed_escapes(self):
        """Test cleaning mixed escape characters"""
        input_text = "Header\\n\\tIndented line\\n\\tAnother indented"
        expected = "Header\n\tIndented line\n\tAnother indented"
        assert clean_markdown(input_text) == expected

    def test_no_escapes(self):
        """Test text without escape characters"""
        input_text = "Normal text without escapes"
        assert clean_markdown(input_text) == input_text


class TestGeneratePaper:
    """Test generate_paper function"""

    @pytest.mark.asyncio
    async def test_generate_paper_without_search(self, sample_protocol_markdown):
        """Test paper generation without external reference search"""
        # Mock all generation functions
        with (
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_title"
            ) as mock_title,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_introduction"
            ) as mock_intro,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_methods"
            ) as mock_methods,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_results"
            ) as mock_results,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_discussion"
            ) as mock_discussion,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_abstract"
            ) as mock_abstract,
        ):
            # Setup mock returns
            mock_title.return_value = MagicMock(content="Test Paper Title")
            mock_intro.return_value = MagicMock(
                content="Test introduction", references=[]
            )
            mock_methods.return_value = MagicMock(content="Test methods")
            mock_results.return_value = MagicMock(content="Test results")
            mock_discussion.return_value = MagicMock(content="Test discussion")
            mock_abstract.return_value = MagicMock(content="Test abstract")

            # Generate paper
            model = SupportedModels(name="qwen3.5-flash")
            result = await generate_paper(
                protocols=[sample_protocol_markdown],
                model=model,
                enable_external_reference_search=False,
            )

            # Assertions
            assert "Test Paper Title" in result
            assert "Test introduction" in result
            assert "Test methods" in result
            assert "Test results" in result
            assert "Test discussion" in result
            assert "Test abstract" in result

            # Verify introduction was called with correct search parameter
            mock_intro.assert_called_once()
            call_args = mock_intro.call_args
            assert call_args[0][3] is False  # enable_external_reference_search

    @pytest.mark.asyncio
    async def test_generate_paper_with_search(self, sample_protocol_markdown):
        """Test paper generation with external reference search"""
        with (
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_title"
            ) as mock_title,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_introduction"
            ) as mock_intro,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_methods"
            ) as mock_methods,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_results"
            ) as mock_results,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_discussion"
            ) as mock_discussion,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_abstract"
            ) as mock_abstract,
        ):
            # Setup mock returns with references
            mock_ref = MagicMock()
            mock_ref.citation = "Smith et al., 2023"
            mock_ref.title = "Test Paper"
            mock_ref.source = "Nature"

            mock_title.return_value = MagicMock(content="Test Paper Title")
            mock_intro.return_value = MagicMock(
                content="Test introduction", references=[mock_ref]
            )
            mock_methods.return_value = MagicMock(content="Test methods")
            mock_results.return_value = MagicMock(content="Test results")
            mock_discussion.return_value = MagicMock(content="Test discussion")
            mock_abstract.return_value = MagicMock(content="Test abstract")

            # Generate paper
            model = SupportedModels(name="qwen3.5-flash")
            result = await generate_paper(
                protocols=[sample_protocol_markdown],
                model=model,
                enable_external_reference_search=True,
            )

            # Assertions
            assert "Test Paper Title" in result
            assert "## References" in result
            assert "Smith et al., 2023" in result

            # Verify introduction was called with search enabled
            mock_intro.assert_called_once()
            call_args = mock_intro.call_args
            assert call_args[0][3] is True  # enable_external_reference_search

    @pytest.mark.asyncio
    async def test_generate_paper_multiple_protocols(self):
        """Test paper generation with multiple protocols"""
        protocols = ["# Protocol 1\n\nContent 1", "# Protocol 2\n\nContent 2"]

        with (
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_title"
            ) as mock_title,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_introduction"
            ) as mock_intro,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_methods"
            ) as mock_methods,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_results"
            ) as mock_results,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_discussion"
            ) as mock_discussion,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_abstract"
            ) as mock_abstract,
        ):
            # Setup mocks
            mock_title.return_value = MagicMock(content="Multi-Protocol Paper")
            mock_intro.return_value = MagicMock(content="Introduction", references=[])
            mock_methods.return_value = MagicMock(content="Methods")
            mock_results.return_value = MagicMock(content="Results")
            mock_discussion.return_value = MagicMock(content="Discussion")
            mock_abstract.return_value = MagicMock(content="Abstract")

            # Generate paper
            model = SupportedModels(name="qwen3.5-flash")
            result = await generate_paper(
                protocols=protocols, model=model, enable_external_reference_search=False
            )

            assert "Multi-Protocol Paper" in result

    @pytest.mark.asyncio
    async def test_generate_paper_with_output_file(
        self, sample_protocol_markdown, tmp_path
    ):
        """Test paper generation with output file"""
        output_file = tmp_path / "test_paper.md"

        with (
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_title"
            ) as mock_title,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_introduction"
            ) as mock_intro,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_methods"
            ) as mock_methods,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_results"
            ) as mock_results,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_discussion"
            ) as mock_discussion,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_abstract"
            ) as mock_abstract,
        ):
            # Setup mocks
            mock_title.return_value = MagicMock(content="Test Paper")
            mock_intro.return_value = MagicMock(content="Introduction", references=[])
            mock_methods.return_value = MagicMock(content="Methods")
            mock_results.return_value = MagicMock(content="Results")
            mock_discussion.return_value = MagicMock(content="Discussion")
            mock_abstract.return_value = MagicMock(content="Abstract")

            # Generate paper with output file
            model = SupportedModels(name="qwen3.5-flash")
            await generate_paper(
                protocols=[sample_protocol_markdown],
                model=model,
                enable_external_reference_search=False,
                output_file=str(output_file),
            )

            # Verify file was created
            assert output_file.exists()
            content = output_file.read_text(encoding="utf-8")
            assert "Test Paper" in content

    @pytest.mark.asyncio
    async def test_generate_paper_cleans_escaped_characters(
        self, sample_protocol_markdown
    ):
        """Test that generated paper cleans escaped characters"""
        with (
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_title"
            ) as mock_title,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_introduction"
            ) as mock_intro,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_methods"
            ) as mock_methods,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_results"
            ) as mock_results,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_discussion"
            ) as mock_discussion,
            patch(
                "masterbrain.endpoints.paper_generation.logic.generate_paper.generate_abstract"
            ) as mock_abstract,
        ):
            # Setup mocks with escaped characters
            mock_title.return_value = MagicMock(content="Test\\nTitle")
            mock_intro.return_value = MagicMock(
                content="Introduction\\nWith\\nNewlines", references=[]
            )
            mock_methods.return_value = MagicMock(content="Methods\\n\\tIndented")
            mock_results.return_value = MagicMock(content="Results\\nData")
            mock_discussion.return_value = MagicMock(content="Discussion\\nText")
            mock_abstract.return_value = MagicMock(content="Abstract\\nSummary")

            # Generate paper
            model = SupportedModels(name="qwen3.5-flash")
            result = await generate_paper(
                protocols=[sample_protocol_markdown],
                model=model,
                enable_external_reference_search=False,
            )

            # Verify escaped characters are cleaned
            assert "Test\nTitle" in result
            assert "Introduction\nWith\nNewlines" in result
            assert "Methods\n\tIndented" in result
            assert "\\n" not in result  # No escaped newlines should remain
