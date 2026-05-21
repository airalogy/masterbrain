"""
Configuration for STT tests.
"""

import pytest


def pytest_configure(config):
    """Configure pytest markers for STT tests."""
    config.addinivalue_line(
        "markers", "stt: mark test as an STT (Speech-to-Text) test"
    )


@pytest.fixture(scope="session")
def stt_test_config():
    """Test configuration for STT tests."""
    return {
        "timeout": 30,
        "max_retries": 3,
        "test_models": ["whisper-1", "gpt-4o-mini-transcribe"]
    }


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing."""
    import base64
    # Minimal WAV file header
    return base64.b64encode(
        b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    ).decode('utf-8')


@pytest.fixture
def mock_stt_request():
    """Mock STT request body for testing."""
    from masterbrain.endpoints.chat.qa.stt.types import STTRequestBody
    
    def _create_request(
        audio_data=None,
        input_type="base64",
        audio_format="wav",
        model="whisper-1"
    ):
        if audio_data is None:
            import base64
            audio_data = base64.b64encode(
                b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
            ).decode('utf-8')
        
        return STTRequestBody(
            audio=audio_data,
            input_type=input_type,
            audio_format=audio_format if input_type == "base64" else None,
            model=model
        )
    
    return _create_request
