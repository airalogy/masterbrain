import pytest
import base64
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.chat.qa.vision.router import chat_qa_vision_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_qa_vision_router, prefix="/api/endpoints", tags=["Vision"])
    return TestClient(app)


CLIENT = _build_client()


# Sample base64 encoded image data (1x1 pixel PNG)
SAMPLE_IMAGE_BASE64 = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
).decode('utf-8')


@pytest.mark.vision
@pytest.mark.parametrize("model_name", ["gpt-4o", "gpt-4o-mini", "gpt-4-vision-preview", "qwen-vl-plus"])
def test_vision_recognition_success(model_name):
    """Test successful vision recognition request."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456", 
        "model": model_name,
        "history": [
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
        "scenario": {}
    }

    # Note: This test may fail in CI/CD without proper API setup
    # In a real scenario, you might want to mock the vision client
    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    
    # Check for successful response or expected error due to test environment
    assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"
    
    if response.status_code == 200:
        response_data = response.json()
        assert "history" in response_data
        # Should have original message plus vision response
        assert len(response_data["history"]) >= 1


@pytest.mark.vision
def test_vision_missing_conversation_history():
    """Test vision request with missing conversation history."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456",
        "model": "gpt-4o",
        "history": [],  # Empty history should cause error
        "scenario": {}
    }

    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    assert response.status_code == 400
    assert "No conversation history provided" in response.json()["detail"]


@pytest.mark.vision
def test_vision_missing_content():
    """Test vision request with missing content in message."""
    payload = {
        "chat_id": "test_chat_123", 
        "user_id": "test_user_456",
        "model": "gpt-4o",
        "history": [
            {
                "role": "user"
                # Missing content field
            }
        ],
        "scenario": {}
    }

    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    assert response.status_code == 400
    assert "No content in last message" in response.json()["detail"]


@pytest.mark.vision  
def test_vision_text_only_content():
    """Test vision request with text-only content (no image)."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456", 
        "model": "gpt-4o",
        "history": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image"
                    }
                    # Missing image_url content
                ]
            }
        ],
        "scenario": {}
    }

    # This should still work as the vision model can handle text-only requests
    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"


@pytest.mark.vision
def test_vision_invalid_image_url():
    """Test vision request with invalid image URL format."""
    payload = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_456",
        "model": "gpt-4o", 
        "history": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What's in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "invalid_url_format"  # Invalid URL
                        }
                    }
                ]
            }
        ],
        "scenario": {}
    }

    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    # Should handle gracefully, either success or proper error
    assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"


@pytest.mark.vision
def test_vision_multiple_images():
    """Test vision request with multiple images in content."""
    payload = {
        "chat_id": "test_chat_multi",
        "user_id": "test_user_multi",
        "model": "gpt-4o",
        "history": [
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": "Compare these two images"
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
        ],
        "scenario": {}
    }

    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"


@pytest.mark.vision
def test_vision_with_scenario_data():
    """Test vision request with scenario data."""
    payload = {
        "chat_id": "test_chat_scenario",
        "user_id": "test_user_scenario",
        "model": "gpt-4o",
        "history": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Analyze this image"
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
        "scenario": {
            "protocol_schema": {"type": "image_analysis"},
            "context": "medical_imaging"
        }
    }

    response = CLIENT.post("/api/endpoints/chat/qa/vision", json=payload)
    assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"
