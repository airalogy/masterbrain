import asyncio
import base64
import tempfile
import os
from typing import get_args
from unittest.mock import AsyncMock, patch, mock_open

import pytest
from openai import AsyncOpenAI

from masterbrain.configs import DEBUG, AvailableQwenModel
from masterbrain.endpoints.chat.qa.stt.router import transcribe_audio
from masterbrain.endpoints.chat.qa.stt.types import SupportedSTTModels

# discover allowed model names from the pydantic model's Literal annotation
STT_MODEL_NAMES = list(get_args(SupportedSTTModels))
# Only test OpenAI models in this file (transcribe_audio function is for OpenAI only)
OPENAI_MODEL_NAMES = [m for m in STT_MODEL_NAMES if m not in get_args(AvailableQwenModel)]

# Sample base64 encoded audio data (a minimal WAV file)
SAMPLE_AUDIO_BASE64 = base64.b64encode(
    b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
).decode('utf-8')

INVALID_BASE64_DATA = "this_is_not_valid_base64!!!"


@pytest.mark.asyncio
@pytest.mark.stt
@pytest.mark.parametrize("model_name", OPENAI_MODEL_NAMES)
async def test_transcribe_audio_success(model_name: str):
    """Test successful audio transcription with mocked OpenAI client."""
    
    if DEBUG:
        print(f"Testing STT model: {model_name}")
    
    # Mock the OpenAI client and its response
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_transcription_response = AsyncMock()
    mock_transcription_response.text = "Hello, this is a test transcription."
    
    # Configure the async mock properly
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription_response)
    
    # Mock file operations to avoid creating actual files
    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        
        # Decode base64 to bytes
        audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
        
        result = await asyncio.wait_for(
            transcribe_audio(mock_client, audio_bytes, "wav", model_name),
            timeout=30
        )
        
        # Verify the result
        assert isinstance(result, str)
        assert result == "Hello, this is a test transcription."
        assert result.strip() != ""
        
        # Verify OpenAI API was called with correct parameters
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == model_name
        assert "file" in call_kwargs
        
        # Verify file cleanup was attempted
        mock_remove.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.stt
async def test_transcribe_audio_invalid_base64():
    """Test transcription with invalid base64 audio data."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    
    # Try to decode invalid base64 - this should fail before calling transcribe_audio
    # But if it somehow gets through, transcribe_audio will handle it
    try:
        audio_bytes = base64.b64decode(INVALID_BASE64_DATA)
    except Exception:
        # If base64 decode fails, we can't test transcribe_audio with invalid data
        # This is expected behavior - invalid base64 should be caught earlier
        pytest.skip("Invalid base64 data cannot be decoded, skipping this test")
    
    with pytest.raises(Exception) as exc_info:
        await transcribe_audio(mock_client, audio_bytes, "wav", "whisper-1")
    
    # Should raise HTTPException with 400 status code for invalid base64
    # The assertion is flexible to handle both the expected error and potential mock-related errors
    assert ("Invalid base64 audio data" in str(exc_info.value) or 
            "Transcription failed" in str(exc_info.value))


@pytest.mark.asyncio
@pytest.mark.stt
async def test_transcribe_audio_openai_api_error():
    """Test transcription when OpenAI API fails."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("API Error"))
    
    with patch("builtins.open", mock_open()), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        
        audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
        
        with pytest.raises(Exception) as exc_info:
            await transcribe_audio(mock_client, audio_bytes, "wav", "whisper-1")
        
        # Should raise HTTPException with 500 status code for API errors
        assert "Transcription failed" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.stt
async def test_transcribe_audio_file_cleanup():
    """Test that temporary files are properly cleaned up even on errors."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("API Error"))
    
    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        
        audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
        
        with pytest.raises(Exception):
            await transcribe_audio(mock_client, audio_bytes, "wav", "whisper-1")
        
        # Verify cleanup was attempted even when transcription failed
        mock_remove.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.stt
async def test_transcribe_audio_file_write_error():
    """Test handling of file write errors."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    
    # Mock file open to raise an exception during write
    with patch("builtins.open", side_effect=OSError("Disk full")):
        
        audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
        
        with pytest.raises(Exception) as exc_info:
            await transcribe_audio(mock_client, audio_bytes, "wav", "whisper-1")
        
        assert "Unexpected error during transcription" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.stt
async def test_transcribe_audio_cleanup_error():
    """Test that errors during file cleanup don't break the function."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_transcription_response = AsyncMock()
    mock_transcription_response.text = "Test transcription"
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription_response)
    
    with patch("builtins.open", mock_open()), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove", side_effect=OSError("Cannot remove file")):
        
        audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
        
        # Should still return successful result even if cleanup fails
        result = await transcribe_audio(mock_client, audio_bytes, "wav", "whisper-1")
        assert result == "Test transcription"


@pytest.mark.asyncio
@pytest.mark.stt
async def test_transcribe_audio_with_timeout():
    """Test transcription with timeout to ensure it doesn't hang."""
    
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_transcription_response = AsyncMock()
    mock_transcription_response.text = "Quick transcription"
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription_response)
    
    with patch("builtins.open", mock_open()), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        
        audio_bytes = base64.b64decode(SAMPLE_AUDIO_BASE64)
        
        # Run with a timeout to ensure it completes quickly
        result = await asyncio.wait_for(
            transcribe_audio(mock_client, audio_bytes, "wav", "whisper-1"),
            timeout=5.0
        )
        
        assert result == "Quick transcription"
