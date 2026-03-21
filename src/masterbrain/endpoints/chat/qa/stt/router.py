__all__ = ["chat_qa_stt_router"]

import asyncio
import base64
import os
import time
import uuid
from typing import Optional
from urllib.parse import urlparse
from typing import get_args

import httpx
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
import dashscope

from masterbrain.configs import select_client, AvailableQwenModel, DASHSCOPE_API_KEY
from masterbrain.types.error import LlmError

from .types import STTRequestBody, STTResponseBody


chat_qa_stt_router = APIRouter()

# Directory path for temporary file storage
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def get_audio_format_from_url(url: str) -> str:
    """Extract audio format from URL path."""
    parsed = urlparse(url)
    path = parsed.path
    extension = os.path.splitext(path)[1].lstrip('.')

    if not extension:
        raise HTTPException(
            status_code=400,
            detail="Cannot determine audio format from URL. Please provide audio_format parameter."
        )

    # Validate the format
    supported_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    if extension.lower() not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {extension}. Supported formats: {', '.join(supported_formats)}"
        )

    return extension.lower()


async def download_audio_from_url(url: str) -> bytes:
    """Download audio file from URL."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download audio from URL: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download audio from URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error downloading audio: {str(e)}"
        )


async def transcribe_audio(
    client: AsyncOpenAI,
    audio_bytes: bytes,
    audio_format: str,
    model_name: str
) -> str:
    """
    Transcribe audio bytes to text.

    Parameters
    ----------
    client : AsyncOpenAI
        OpenAI client instance
    audio_bytes : bytes
        Audio file content as bytes
    audio_format : str
        Audio file format (e.g., 'wav', 'mp3')
    model_name : str
        STT model to use

    Returns
    -------
    str
        Transcribed text
    """
    # Generate unique temporary filename
    temp_audio_filename = f"tmp_files/tmp_{uuid.uuid4().hex}.{audio_format}"
    temp_audio_path = os.path.join(CURRENT_DIR, temp_audio_filename)

    try:
        # Save audio data to temporary file
        with open(temp_audio_path, "wb") as audio_file:
            os.makedirs(os.path.dirname(temp_audio_path), exist_ok=True)
            audio_file.write(audio_bytes)
            print(f"Audio file saved temporarily: {temp_audio_filename}")

        # Transcribe audio
        try:
            with open(temp_audio_path, "rb") as audio_file:
                transcription_response = await client.audio.transcriptions.create(
                    model=model_name,
                    file=audio_file
                )
            return transcription_response.text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during transcription: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                print(f"Temporary audio file cleaned up: {temp_audio_filename}")
            except OSError:
                print(f"Warning: Could not remove temporary audio file: {temp_audio_filename}")


async def transcribe_audio_qwen(
    model_name: str,
    audio_bytes: Optional[bytes] = None,
    audio_format: Optional[str] = None,
    audio_url: Optional[str] = None
) -> str:
    """
    Transcribe audio to text using Qwen dashscope API.

    Supports two input methods:
    1. audio_bytes + audio_format: For base64 input, saves to temp file
    2. audio_url: For URL input, directly passes URL to API (no download)

    For qwen3-asr-flash model, the audio file size should not exceed 10MB.

    Parameters
    ----------
    model_name : str
        Qwen STT model to use (e.g., 'qwen3-asr-flash')
    audio_bytes : Optional[bytes]
        Audio file content as bytes (for base64 input)
    audio_format : Optional[str]
        Audio file format (e.g., 'wav', 'mp3'), required with audio_bytes
    audio_url : Optional[str]
        Audio URL (for URL input)

    Returns
    -------
    str
        Transcribed text
    """
    # Validate inputs
    if audio_url is None and (audio_bytes is None or audio_format is None):
        raise HTTPException(
            status_code=400,
            detail="Either audio_url or (audio_bytes + audio_format) must be provided"
        )

    temp_audio_path = None

    try:
        # Determine audio URL for API call
        if audio_url:
            # Use URL directly, no download needed
            print(f"Using audio URL directly: {audio_url}")
            audio_file_url = audio_url
        else:
            # Validate file size for qwen3-asr-flash model
            if model_name == "qwen3-asr-flash" and audio_bytes:
                file_size_mb = len(audio_bytes) / (1024 * 1024)
                if file_size_mb > 10:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Audio file size ({file_size_mb:.2f}MB) exceeds the 10MB limit for qwen3-asr-flash model"
                    )

            # Save audio bytes to temporary file
            temp_audio_filename = f"tmp_files/tmp_{uuid.uuid4().hex}.{audio_format}"
            temp_audio_path = os.path.join(CURRENT_DIR, temp_audio_filename)

            os.makedirs(os.path.dirname(temp_audio_path), exist_ok=True)
            with open(temp_audio_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
                print(f"Audio file saved temporarily: {temp_audio_filename}")

            # Convert to absolute file:// URL for dashscope API
            absolute_path = os.path.abspath(temp_audio_path)
            audio_file_url = f"file://{absolute_path}"

        # Transcribe audio using dashscope API
        def call_dashscope_api():
            """Synchronous dashscope API call"""
            messages = [
                {"role": "system", "content": [{"text": ""}]},
                {"role": "user", "content": [{"audio": audio_file_url}]}
            ]
            response = dashscope.MultiModalConversation.call(
                api_key=DASHSCOPE_API_KEY,
                model=model_name,
                messages=messages,
                result_format="message",
                asr_options={
                    "enable_itn": False
                }
            )
            return response

        # Run synchronous dashscope call in thread pool
        response = await asyncio.to_thread(call_dashscope_api)

        # Extract transcribed text from response
        if response.status_code == 200:
            # Parse response to get transcribed text
            output_content = response.output.choices[0].message.content
            if isinstance(output_content, list) and len(output_content) > 0:
                transcribed_text = output_content[0].get("text", "")
                return transcribed_text
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected response format from dashscope API"
                )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Dashscope API error: {response.code} - {response.message}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
    finally:
        # Clean up temporary file if it was created
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                print(f"Temporary audio file cleaned up: {os.path.basename(temp_audio_path)}")
            except OSError:
                print(f"Warning: Could not remove temporary audio file: {os.path.basename(temp_audio_path)}")


@chat_qa_stt_router.post(
    "/chat/qa/stt",
    summary="Speech to Text Conversion",
    responses={
        200: {"description": "Success", "model": STTResponseBody},
        400: {"description": "Bad Request", "model": LlmError},
    },
)
async def handle_stt_request(request_data: STTRequestBody) -> STTResponseBody:
    """
    Convert speech to text.

    Supports two input methods:
    1. Base64 encoded audio data (requires audio_format)
    2. Audio URL (auto-detects format from URL)

    Supported audio formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    start_time = time.time()

    try:
        if request_data.model in get_args(AvailableQwenModel):
            # Qwen model handling
            if request_data.input_type == "base64":
                # Decode base64 audio data
                try:
                    audio_bytes = base64.b64decode(request_data.audio)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")

                # Use provided audio format (guaranteed to be not None by Pydantic validator)
                if request_data.audio_format is None:
                    raise HTTPException(status_code=400, detail="audio_format is required for base64 input")

                transcribed_text = await transcribe_audio_qwen(
                    model_name=request_data.model,
                    audio_bytes=audio_bytes,
                    audio_format=request_data.audio_format
                )

            elif request_data.input_type == "url":
                # Use URL directly without downloading
                print(f"Using audio URL directly for Qwen model: {request_data.audio}")
                transcribed_text = await transcribe_audio_qwen(
                    model_name=request_data.model,
                    audio_url=request_data.audio
                )

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported input_type: {request_data.input_type}")

        else:
            # OpenAI/other models handling - always need to download and save to file
            audio_format: str

            if request_data.input_type == "base64":
                # Decode base64 audio data
                try:
                    audio_bytes = base64.b64decode(request_data.audio)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")

                # Use provided audio format (guaranteed to be not None by Pydantic validator)
                if request_data.audio_format is None:
                    raise HTTPException(status_code=400, detail="audio_format is required for base64 input")
                audio_format = request_data.audio_format

            elif request_data.input_type == "url":
                # Download audio from URL
                print(f"Downloading audio from URL: {request_data.audio}")
                audio_bytes = await download_audio_from_url(request_data.audio)

                # Determine audio format from URL or use provided format
                if request_data.audio_format:
                    audio_format = request_data.audio_format
                else:
                    audio_format = get_audio_format_from_url(request_data.audio)

                print(f"Detected audio format: {audio_format}")

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported input_type: {request_data.input_type}")

            # Get OpenAI client and transcribe audio to text
            client = select_client(request_data.model)
            transcribed_text = await transcribe_audio(
                client=client,
                audio_bytes=audio_bytes,
                audio_format=audio_format,
                model_name=request_data.model
            )

        end_time = time.time()
        print(f"STT Recognition completed in {end_time - start_time:.6f} seconds")

        return STTResponseBody(text=transcribed_text)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in STT processing: {str(e)}")
