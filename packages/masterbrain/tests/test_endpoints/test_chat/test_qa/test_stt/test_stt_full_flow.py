"""
Full flow tests for STT (Speech-to-Text) functionality.
Tests the complete STT pipeline from audio input to text output.
"""

import asyncio
import base64
from typing import get_args
from unittest.mock import AsyncMock, patch, mock_open, MagicMock

import pytest
from openai import AsyncOpenAI

from masterbrain.configs import DEBUG, AvailableQwenModel
from masterbrain.endpoints.chat.qa.stt.router import handle_stt_request
from masterbrain.endpoints.chat.qa.stt.types import STTRequestBody, STTResponseBody, SupportedSTTModels

# discover allowed model names from the pydantic model's Literal annotation
STT_MODEL_NAMES = list(get_args(SupportedSTTModels))
QWEN_MODEL_NAMES = [m for m in STT_MODEL_NAMES if m in get_args(AvailableQwenModel)]
OPENAI_MODEL_NAMES = [m for m in STT_MODEL_NAMES if m not in get_args(AvailableQwenModel)]

# Sample base64 encoded audio data (a minimal WAV file)
SAMPLE_AUDIO_BASE64 = base64.b64encode(
    b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
).decode('utf-8')


@pytest.mark.asyncio
@pytest.mark.stt
@pytest.mark.parametrize("model_name", OPENAI_MODEL_NAMES)
async def test_full_stt_flow_openai(model_name: str):
    """Test the complete STT flow from request to response with OpenAI models."""

    if DEBUG:
        print(f"Testing full STT flow with OpenAI model: {model_name}")

    # Create test request body
    request_body = STTRequestBody(
        audio=SAMPLE_AUDIO_BASE64,
        input_type="base64",
        audio_format="wav",
        model=model_name
    )

    # Mock the OpenAI client and its response
    mock_client = AsyncMock(spec=AsyncOpenAI)
    mock_transcription_response = AsyncMock()
    mock_transcription_response.text = "This is a test transcription result."
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription_response)

    # Mock file operations and client selection
    with patch("masterbrain.endpoints.chat.qa.stt.router.select_client", return_value=mock_client), \
         patch("builtins.open", mock_open()), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"), \
         patch("os.makedirs"):

        result = await asyncio.wait_for(
            handle_stt_request(request_body),
            timeout=30
        )

        # Verify the result
        assert isinstance(result, STTResponseBody)
        assert result.text == "This is a test transcription result."


@pytest.mark.asyncio
@pytest.mark.stt
@pytest.mark.parametrize("model_name", QWEN_MODEL_NAMES)
async def test_full_stt_flow_qwen(model_name: str):
    """Test the complete STT flow from request to response with Qwen models."""

    if DEBUG:
        print(f"Testing full STT flow with Qwen model: {model_name}")

    # Create test request body
    request_body = STTRequestBody(
        audio=SAMPLE_AUDIO_BASE64,
        input_type="base64",
        audio_format="wav",
        model=model_name
    )

    # Mock dashscope API response
    mock_dashscope_response = MagicMock()
    mock_dashscope_response.status_code = 200
    mock_dashscope_response.output = MagicMock()
    mock_dashscope_response.output.choices = [MagicMock()]
    mock_dashscope_response.output.choices[0].message = MagicMock()
    mock_dashscope_response.output.choices[0].message.content = [{"text": "This is a test transcription result from Qwen."}]

    # Mock file operations and dashscope API
    with patch("masterbrain.endpoints.chat.qa.stt.router.asyncio.to_thread", return_value=mock_dashscope_response), \
         patch("builtins.open", mock_open()), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"), \
         patch("os.makedirs"), \
         patch("os.path.abspath", return_value="/fake/path/tmp.wav"):

        result = await asyncio.wait_for(
            handle_stt_request(request_body),
            timeout=30
        )

        # Verify the result
        assert isinstance(result, STTResponseBody)
        assert result.text == "This is a test transcription result from Qwen."


@pytest.mark.asyncio
@pytest.mark.stt
async def test_stt_flow_default_model():
    """Test STT flow with default model (qwen3-asr-flash)."""

    if DEBUG:
        print("Testing STT flow with default model")

    # Create test request body without specifying model
    request_body = STTRequestBody(
        audio=SAMPLE_AUDIO_BASE64,
        input_type="base64",
        audio_format="wav"
    )

    # Mock dashscope API response for default Qwen model
    mock_dashscope_response = MagicMock()
    mock_dashscope_response.status_code = 200
    mock_dashscope_response.output = MagicMock()
    mock_dashscope_response.output.choices = [MagicMock()]
    mock_dashscope_response.output.choices[0].message = MagicMock()
    mock_dashscope_response.output.choices[0].message.content = [{"text": "Transcription with default model."}]

    with patch("masterbrain.endpoints.chat.qa.stt.router.asyncio.to_thread", return_value=mock_dashscope_response), \
         patch("builtins.open", mock_open()), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"), \
         patch("os.makedirs"), \
         patch("os.path.abspath", return_value="/fake/path/tmp.wav"):

        result = await asyncio.wait_for(
            handle_stt_request(request_body),
            timeout=30
        )

        # Verify the result
        assert isinstance(result, STTResponseBody)
        assert result.text == "Transcription with default model."


@pytest.mark.asyncio
@pytest.mark.stt
async def test_stt_flow_error_handling():
    """Test error handling in the STT flow."""

    # Test with invalid base64 audio
    request_body = STTRequestBody(
        audio="invalid_base64!!!",
        input_type="base64",
        audio_format="wav",
        model="qwen3-asr-flash"
    )

    with pytest.raises(Exception) as exc_info:
        await handle_stt_request(request_body)

    assert "Invalid base64 audio data" in str(exc_info.value)
