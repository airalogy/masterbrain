import asyncio
import base64
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncOpenAI

from masterbrain.configs import DEBUG
from masterbrain.endpoints.chat.qa.vision.router import recognize_image
from masterbrain.endpoints.chat.qa.vision.types import SupportedVisionModels

# discover allowed model names from the pydantic model's Literal annotation
VISION_MODEL_NAMES = list(get_args(SupportedVisionModels))

# Sample base64 encoded image data (1x1 pixel PNG)
SAMPLE_IMAGE_BASE64 = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
).decode('utf-8')


@pytest.mark.asyncio
@pytest.mark.vision
@pytest.mark.parametrize("model_name", VISION_MODEL_NAMES)
async def test_recognize_image_success(model_name: str):
    """Test successful image recognition with mocked OpenAI client."""
    
    if DEBUG:
        print(f"Testing Vision model: {model_name}")
    
    # Mock the OpenAI client and its response
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "I can see a small transparent image with minimal visual content."
    
    # Configure the async mock properly
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    # Prepare conversation history with image
    conversation_history = [
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
    ]
    
    result = await asyncio.wait_for(
        recognize_image(mock_client, conversation_history, model_name),
        timeout=30
    )
    
    # Verify the result
    assert isinstance(result, str)
    assert result == "I can see a small transparent image with minimal visual content."
    assert result.strip() != ""
    
    # Verify OpenAI API was called with correct parameters
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == model_name
    assert "messages" in call_kwargs
    assert len(call_kwargs["messages"]) == 1


@pytest.mark.asyncio
@pytest.mark.vision
async def test_recognize_image_text_only():
    """Test image recognition with text-only content."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "I see only text content, no image provided."
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    # Conversation with only text content
    conversation_history = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe what you see"
                }
            ]
        }
    ]
    
    result = await recognize_image(mock_client, conversation_history, "gpt-4o")
    
    assert isinstance(result, str)
    assert result == "I see only text content, no image provided."


@pytest.mark.asyncio
@pytest.mark.vision
async def test_recognize_image_api_error():
    """Test image recognition when OpenAI API fails."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
    
    conversation_history = [
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
    ]
    
    with pytest.raises(Exception) as exc_info:
        await recognize_image(mock_client, conversation_history, "gpt-4o")
    
    # Should raise HTTPException with 500 status code for API errors
    assert "Vision recognition failed" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.vision
async def test_recognize_image_empty_response():
    """Test handling of empty response from vision model."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = None  # Empty response
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    conversation_history = [
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
    ]
    
    result = await recognize_image(mock_client, conversation_history, "gpt-4o")
    
    # Should return empty string for None response
    assert result == ""


@pytest.mark.asyncio
@pytest.mark.vision
async def test_recognize_image_multiple_images():
    """Test image recognition with multiple images in conversation."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "I can see multiple images in this conversation."
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    conversation_history = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Compare these images"
                },
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{SAMPLE_IMAGE_BASE64}"
                    }
                }
            ]
        }
    ]
    
    result = await recognize_image(mock_client, conversation_history, "gpt-4o")
    
    assert result == "I can see multiple images in this conversation."


@pytest.mark.asyncio
@pytest.mark.vision
async def test_recognize_image_with_timeout():
    """Test image recognition with timeout to ensure it doesn't hang."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "Quick recognition result"
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    conversation_history = [
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
    ]
    
    # Run with a timeout to ensure it completes quickly
    result = await asyncio.wait_for(
        recognize_image(mock_client, conversation_history, "gpt-4o"),
        timeout=5.0
    )
    
    assert result == "Quick recognition result"


@pytest.mark.asyncio
@pytest.mark.vision
async def test_recognize_image_jpeg_format():
    """Test image recognition with JPEG format image."""
    
    # Sample JPEG data (minimal 1x1 pixel JPEG)
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    jpeg_base64 = base64.b64encode(jpeg_data).decode('utf-8')
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_completion_response = AsyncMock()
    mock_completion_response.choices = [AsyncMock()]
    mock_completion_response.choices[0].message.content = "I can see a JPEG image."
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_response)
    
    conversation_history = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{jpeg_base64}"
                    }
                }
            ]
        }
    ]
    
    result = await recognize_image(mock_client, conversation_history, "gpt-4o")
    
    assert result == "I can see a JPEG image."
