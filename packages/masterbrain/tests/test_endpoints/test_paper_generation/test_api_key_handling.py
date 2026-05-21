"""Test API key handling in paper generation"""

import os
from unittest.mock import MagicMock, patch

import pytest

from masterbrain.endpoints.paper_generation.logic.generate_paper import generate_paper
from masterbrain.endpoints.paper_generation.types import SupportedModels


class TestAPIKeyHandling:
    """Test API key and configuration handling"""

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_error(self):
        """Test that missing API key raises appropriate error"""
        # Mock configs to have empty API keys
        with (
            patch("masterbrain.configs.DASHSCOPE_API_KEY", ""),
            patch("masterbrain.configs.OPENAI_API_KEY", ""),
        ):
            model = SupportedModels(name="qwen3.5-flash")
            protocols = ["# Test Protocol"]

            with pytest.raises(ValueError, match="API key not set for model"):
                await generate_paper(
                    protocols=protocols,
                    model=model,
                    enable_external_reference_search=False,
                )

    @pytest.mark.asyncio
    async def test_api_key_passed_to_model(self):
        """Test that API key is correctly passed to model initialization"""
        test_api_key = "test-api-key-123"
        test_base_url = "https://test.api.com"

        # Mock configs for qwen3.5-flash (uses DASHSCOPE)
        with (
            patch("masterbrain.configs.DASHSCOPE_API_KEY", test_api_key),
            patch("masterbrain.configs.DASHSCOPE_BASE_URL", test_base_url),
        ):
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
                mock_title.return_value = MagicMock(content="Test Title")
                mock_intro.return_value = MagicMock(
                    content="Introduction", references=[]
                )
                mock_methods.return_value = MagicMock(content="Methods")
                mock_results.return_value = MagicMock(content="Results")
                mock_discussion.return_value = MagicMock(content="Discussion")
                mock_abstract.return_value = MagicMock(content="Abstract")

                model = SupportedModels(name="qwen3.5-flash")
                protocols = ["# Test Protocol"]

                await generate_paper(
                    protocols=protocols,
                    model=model,
                    enable_external_reference_search=False,
                )

                # Verify that title was called (which means config was created successfully)
                mock_title.assert_called_once()

                # Check that the config passed has the correct model_kwargs
                call_args = mock_title.call_args
                config = call_args[0][1]  # Second argument is config

                assert config.writer_model_kwargs is not None
                assert config.writer_model_kwargs["api_key"] == test_api_key
                assert config.writer_model_kwargs["base_url"] == test_base_url

    @pytest.mark.asyncio
    async def test_api_key_without_base_url(self):
        """Test that API key works without base URL"""
        test_api_key = "test-api-key-456"

        # Mock configs for qwen3.5-flash (uses DASHSCOPE) without base_url
        with (
            patch("masterbrain.configs.DASHSCOPE_API_KEY", test_api_key),
            patch("masterbrain.configs.DASHSCOPE_BASE_URL", None),
        ):
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
                mock_title.return_value = MagicMock(content="Test Title")
                mock_intro.return_value = MagicMock(
                    content="Introduction", references=[]
                )
                mock_methods.return_value = MagicMock(content="Methods")
                mock_results.return_value = MagicMock(content="Results")
                mock_discussion.return_value = MagicMock(content="Discussion")
                mock_abstract.return_value = MagicMock(content="Abstract")

                model = SupportedModels(name="qwen3.5-flash")
                protocols = ["# Test Protocol"]

                await generate_paper(
                    protocols=protocols,
                    model=model,
                    enable_external_reference_search=False,
                )

                # Verify config was created
                call_args = mock_title.call_args
                config = call_args[0][1]

                assert config.writer_model_kwargs is not None
                assert config.writer_model_kwargs["api_key"] == test_api_key
                # When base_url is None, DashScope uses default URL
                # So base_url should be present with the default value
                assert "base_url" in config.writer_model_kwargs
                assert (
                    config.writer_model_kwargs["base_url"]
                    == "https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
