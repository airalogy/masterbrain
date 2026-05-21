"""
Full flow tests for Vision (Image Recognition) functionality.
Tests the complete Vision pipeline from image input to text output.
"""

import asyncio
import base64
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncOpenAI

from masterbrain.configs import DEBUG
from masterbrain.endpoints.chat.qa.vision.router import handle_vision_request, parse_request_data
from masterbrain.endpoints.chat.qa.vision.types import VisionRequestBody, SupportedVisionModels

# discover allowed model names from the pydantic model's Literal annotation
VISION_MODEL_NAMES = list(get_args(SupportedVisionModels))

# Sample base64 encoded image data (1x1 pixel PNG)
SAMPLE_IMAGE_BASE64 = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
).decode('utf-8')


@pytest.mark.asyncio
@pytest.mark.vision
@pytest.mark.parametrize("model_name", VISION_MODEL_NAMES)
async def test_full_vision_flow(model_name: str):
    """Test the complete Vision flow from request to response."""
    
    if DEBUG:
        print(f"Testing full Vision flow with model: {model_name}")
    
    # Create test request body
    request_body = VisionRequestBody(
        chat_id="test_chat_123",
        user_id="test_user_456",
        model=model_name,
        history=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What do you see in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                        }
                    }
                ]
            }
        ],
        scenario={}
    )
    
    # Mock the OpenAI client and its response
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "I can see a small transparent image with minimal visual content."
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    # Mock client selection
    with patch("masterbrain.endpoints.chat.qa.vision.router.select_client", return_value=mock_client):
        
        result = await asyncio.wait_for(
            handle_vision_request(request_body),
            timeout=30
        )
        
        # Verify the result
        assert isinstance(result, VisionRequestBody)
        assert result.chat_id == "test_chat_123"
        assert result.user_id == "test_user_456"
        assert result.model == model_name
        
        # Verify that the recognized text was added to history
        assert len(result.history) == 2  # original + assistant response
        
        # Find the assistant response in history
        assistant_responses = [msg for msg in result.history if msg.get("role") == "assistant"]
        assert len(assistant_responses) == 1
        assert "small transparent image" in assistant_responses[0]["content"]


@pytest.mark.asyncio
@pytest.mark.vision
async def test_parse_request_data():
    """Test the request data parsing function."""
    
    request_body = VisionRequestBody(
        chat_id="test_chat_789",
        user_id="test_user_101",
        model="gpt-4o",
        history=[{"role": "user", "content": "test"}],
        scenario={"protocol_schema": {"type": "test"}}
    )
    
    chat_id, user_id, model, history, protocol_schema = parse_request_data(request_body)
    
    assert chat_id == "test_chat_789"
    assert user_id == "test_user_101"
    assert model == "gpt-4o"
    assert len(history) == 1
    assert protocol_schema == {"type": "test"}


@pytest.mark.asyncio
@pytest.mark.vision
async def test_parse_request_data_defaults():
    """Test request data parsing with default values."""
    
    request_body = VisionRequestBody(
        chat_id="test_chat_default",
        user_id="test_user_default"
        # model, history, and scenario will use defaults
    )
    
    chat_id, user_id, model, history, protocol_schema = parse_request_data(request_body)
    
    assert chat_id == "test_chat_default"
    assert user_id == "test_user_default"
    assert model == "qwen-vl-plus"  # default model
    assert history == []  # default empty list
    assert protocol_schema is None  # default empty scenario


@pytest.mark.asyncio
@pytest.mark.vision
@pytest.mark.parametrize("model_name", VISION_MODEL_NAMES)
async def test_vision_flow_with_multiple_messages(model_name: str):
    """Test Vision flow with multiple messages in history."""
    
    if DEBUG:
        print(f"Testing multiple messages with model: {model_name}")
    
    request_body = VisionRequestBody(
        chat_id="test_chat_multi",
        user_id="test_user_multi",
        model=model_name,
        history=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "First image"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                        }
                    }
                ]
            },
            {
                "role": "assistant",
                "content": "Previous vision analysis result"
            },
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": "Now analyze this new image"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                        }
                    }
                ]
            }
        ],
        scenario={}
    )
    
    # Mock the OpenAI client
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "Latest vision analysis result."
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    with patch("masterbrain.endpoints.chat.qa.vision.router.select_client", return_value=mock_client):
        
        result = await asyncio.wait_for(
            handle_vision_request(request_body),
            timeout=30
        )
        
        # Verify that the new vision analysis was added
        assert len(result.history) == 4  # original 3 + 1 new assistant response
        assert result.history[-1]["role"] == "assistant"
        assert result.history[-1]["content"] == "Latest vision analysis result."


@pytest.mark.asyncio
@pytest.mark.vision
async def test_vision_flow_error_handling():
    """Test error handling in the Vision flow."""
    
    # Test with missing content
    request_body = VisionRequestBody(
        chat_id="test_error",
        user_id="test_user_error",
        model="gpt-4o",
        history=[
            {
                "role": "user"
                # Missing content field
            }
        ],
        scenario={}
    )
    
    with pytest.raises(Exception) as exc_info:
        await handle_vision_request(request_body)
    
    assert "No content in last message" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.vision
async def test_vision_flow_empty_history():
    """Test Vision flow with empty conversation history."""
    
    request_body = VisionRequestBody(
        chat_id="test_empty",
        user_id="test_user_empty",
        model="gpt-4o",
        history=[],  # Empty history
        scenario={}
    )
    
    with pytest.raises(Exception) as exc_info:
        await handle_vision_request(request_body)
    
    assert "No conversation history provided" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.vision
async def test_vision_flow_text_cleaning():
    """Test that recognized text is properly cleaned."""
    
    request_body = VisionRequestBody(
        chat_id="test_cleaning",
        user_id="test_user_cleaning", 
        model="gpt-4o",
        history=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                        }
                    }
                ]
            }
        ],
        scenario={}
    )
    
    # Mock response with markdown and newlines that should be cleaned
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "```\nThis is a test\nwith newlines\n```"
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    with patch("masterbrain.endpoints.chat.qa.vision.router.select_client", return_value=mock_client):
        
        result = await handle_vision_request(request_body)
        
        # Verify text was cleaned (no ``` or newlines)
        assistant_response = result.history[-1]["content"]
        assert "```" not in assistant_response
        assert "\n" not in assistant_response
        assert assistant_response == "This is a testwith newlines"


@pytest.mark.asyncio
@pytest.mark.vision
async def test_vision_flow_api_timeout():
    """Test Vision flow behavior under API timeout conditions."""
    
    request_body = VisionRequestBody(
        chat_id="test_timeout",
        user_id="test_user_timeout",
        model="gpt-4o",
        history=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                        }
                    }
                ]
            }
        ],
        scenario={}
    )
    
    # Mock client that takes too long to respond
    mock_client = AsyncMock(spec=AsyncOpenAI)
    
    async def slow_response(**kwargs):
        await asyncio.sleep(10)  # Simulate slow API
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Delayed response"
        return mock_response
    
    mock_client.chat.completions.create = slow_response
    
    with patch("masterbrain.endpoints.chat.qa.vision.router.select_client", return_value=mock_client):
        
        # Should timeout and raise exception
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                handle_vision_request(request_body),
                timeout=5.0
            )


@pytest.mark.asyncio
@pytest.mark.vision
async def test_vision_flow_with_scenario():
    """Test Vision flow with scenario data."""
    
    request_body = VisionRequestBody(
        chat_id="test_scenario",
        user_id="test_user_scenario",
        model="gpt-4o",
        history=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this medical image"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                        }
                    }
                ]
            }
        ],
        scenario={
            "protocol_schema": {"type": "medical_analysis"},
            "context": "radiology"
        }
    )
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "Medical image analysis complete."
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    with patch("masterbrain.endpoints.chat.qa.vision.router.select_client", return_value=mock_client):
        
        result = await handle_vision_request(request_body)
        
        # Verify scenario data is preserved
        assert result.scenario["protocol_schema"]["type"] == "medical_analysis"
        assert result.scenario["context"] == "radiology"
        
        # Verify vision analysis was performed
        assert len(result.history) == 2
        assert result.history[-1]["content"] == "Medical image analysis complete."
