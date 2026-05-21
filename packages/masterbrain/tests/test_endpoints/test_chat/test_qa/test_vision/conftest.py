"""
Configuration for Vision tests.
"""

import pytest
import base64


def pytest_configure(config):
    """Configure pytest markers for Vision tests."""
    config.addinivalue_line(
        "markers", "vision: mark test as a Vision (Image Recognition) test"
    )


@pytest.fixture(scope="session")
def vision_test_config():
    """Test configuration for Vision tests."""
    return {
        "timeout": 30,
        "max_retries": 3,
        "test_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-vision-preview", "qwen-vl-plus", "qwen-vl-plus-latest", "qwen-vl-max-0201"]
    }


@pytest.fixture
def sample_image_data():
    """Sample image data for testing (1x1 pixel PNG)."""
    # Minimal PNG file - 1x1 transparent pixel
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(png_data).decode('utf-8')


@pytest.fixture
def sample_jpeg_data():
    """Sample JPEG data for testing (minimal JPEG)."""
    # Minimal JPEG file - 1x1 pixel
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    return base64.b64encode(jpeg_data).decode('utf-8')


@pytest.fixture
def mock_vision_request():
    """Mock Vision request body for testing."""
    from masterbrain.endpoints.chat.qa.vision.types import VisionRequestBody
    
    def _create_request(chat_id="test_chat", user_id="test_user", model="gpt-4o", image_data=None):
        if image_data is None:
            # Use sample PNG data if not provided
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            image_data = base64.b64encode(png_data).decode('utf-8')
        
        return VisionRequestBody(
            chat_id=chat_id,
            user_id=user_id,
            model=model,
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
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            scenario={}
        )
    
    return _create_request
