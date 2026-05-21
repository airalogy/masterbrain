from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


SupportedSTTModels = Literal[
    "whisper-1",
    "whisper-base",
    "whisper-large-v3",
    "whisper-large-v3-turbo",
    "gpt-4o-transcribe",
    "gpt-4o-mini-transcribe",
    "qwen3-asr-flash",
    "qwen3-asr-flash-filetrans"
]

SupportedAudioFormats = Literal[
    "mp3",
    "mp4",
    "mpeg",
    "mpga",
    "m4a",
    "wav",
    "webm"
]

AudioInputType = Literal["base64", "url"]


class STTRequestBody(BaseModel):
    """
    Speech-to-Text request body.

    Supports two input methods:
    1. Base64 encoded audio data (audio + input_type="base64")
    2. Audio URL (audio + input_type="url")

    Examples
    --------
    Base64 input:
        {
            "audio": "UklGRiQAAABXQVZFZm10...",
            "input_type": "base64",
            "audio_format": "wav",
            "model": "qwen3-asr-flash"
        }

    URL input:
        {
            "audio": "https://example.com/audio.mp3",
            "input_type": "url",
            "model": "qwen3-asr-flash"
        }
    """
    audio: str = Field(..., description="Base64 encoded audio data or audio URL")
    input_type: AudioInputType = Field(default="base64", description="Type of audio input: 'base64' or 'url'")
    audio_format: Optional[SupportedAudioFormats] = Field(
        default=None,
        description="Audio format. Required for base64 input, auto-detected for URLs"
    )
    model: SupportedSTTModels = Field(default="qwen3-asr-flash", description="STT model to use")

    @field_validator("audio_format")
    @classmethod
    def validate_audio_format(cls, v, info):
        """Validate that audio_format is provided for base64 input"""
        if info.data.get("input_type") == "base64" and v is None:
            raise ValueError("audio_format is required when input_type is 'base64'")
        return v


class STTResponseBody(BaseModel):
    text: str
