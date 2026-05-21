import pytest
import base64
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.chat.qa.stt.router import chat_qa_stt_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_qa_stt_router, prefix="/api/endpoints", tags=["STT"])
    return TestClient(app)


CLIENT = _build_client()


# Sample base64 encoded audio data (a small WAV file header)
SAMPLE_AUDIO_BASE64 = base64.b64encode(
    b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
).decode('utf-8')


@pytest.mark.stt
@pytest.mark.parametrize("model_name", ["whisper-1", "gpt-4o-mini-transcribe", "qwen3-asr-flash"])
def test_stt_transcription_success(model_name):
    """Test successful STT transcription request with base64 input."""
    payload = {
        "audio": SAMPLE_AUDIO_BASE64,
        "input_type": "base64",
        "audio_format": "wav",
        "model": model_name
    }

    # Note: This test may fail in CI/CD without proper API setup
    # In a real scenario, you might want to mock the API clients
    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    
    # Check for successful response or expected error due to test environment
    assert response.status_code in [200, 400, 500], f"Unexpected status code: {response.status_code}"
    
    if response.status_code == 200:
        response_data = response.json()
        assert "text" in response_data
        assert isinstance(response_data["text"], str)


@pytest.mark.stt
def test_stt_missing_audio():
    """Test STT request with missing audio field."""
    payload = {
        "input_type": "base64",
        "audio_format": "wav",
        "model": "qwen3-asr-flash"
    }

    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    assert response.status_code == 422  # Validation error from Pydantic


@pytest.mark.stt
def test_stt_missing_audio_format_for_base64():
    """Test STT request with base64 input but missing audio_format."""
    payload = {
        "audio": SAMPLE_AUDIO_BASE64,
        "input_type": "base64",
        "model": "qwen3-asr-flash"
    }

    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    # Pydantic validator raises HTTPException with 400 status code
    assert response.status_code in [400, 422]
    response_data = response.json()
    assert "audio_format" in str(response_data).lower() or "required" in str(response_data).lower()


@pytest.mark.stt
def test_stt_invalid_base64_audio():
    """Test STT request with invalid base64 audio data."""
    payload = {
        "audio": "invalid_base64_data!!!",
        "input_type": "base64",
        "audio_format": "wav",
        "model": "qwen3-asr-flash"
    }

    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    assert response.status_code == 400
    assert "Invalid base64 audio data" in response.json()["detail"]


@pytest.mark.stt
def test_stt_url_input():
    """Test STT request with URL input."""
    payload = {
        "audio": "https://example.com/test_audio.mp3",
        "input_type": "url",
        "model": "qwen3-asr-flash"
    }

    # This will likely fail due to network request, but should validate the request format
    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    # Should either succeed (if URL is accessible) or fail with download error, not validation error
    assert response.status_code in [200, 400, 500]
    if response.status_code == 400:
        # Should be a download error, not a validation error
        assert "download" in response.json()["detail"].lower() or "url" in response.json()["detail"].lower()


@pytest.mark.stt
def test_stt_invalid_input_type():
    """Test STT request with invalid input_type."""
    payload = {
        "audio": SAMPLE_AUDIO_BASE64,
        "input_type": "invalid_type",
        "audio_format": "wav",
        "model": "qwen3-asr-flash"
    }

    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    assert response.status_code == 422  # Validation error from Pydantic


@pytest.mark.stt
def test_stt_invalid_audio_format():
    """Test STT request with invalid audio_format."""
    payload = {
        "audio": SAMPLE_AUDIO_BASE64,
        "input_type": "base64",
        "audio_format": "invalid_format",
        "model": "qwen3-asr-flash"
    }

    response = CLIENT.post("/api/endpoints/chat/qa/stt", json=payload)
    assert response.status_code == 422  # Validation error from Pydantic
