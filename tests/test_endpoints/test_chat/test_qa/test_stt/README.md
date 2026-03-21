# STT (Speech-to-Text) Tests

This directory contains the complete test suite for STT (Speech-to-Text) functionality.

## API Overview

The STT endpoint supports converting audio to text using both OpenAI's Whisper models and Qwen's ASR models. The system automatically selects the appropriate API based on the model name.

### Endpoint

- **POST** `/chat/qa/stt`

### Supported Input Methods

1. **Base64 Encoded Audio** (`input_type="base64"`)
   - Requires `audio_format` parameter
   - Audio data must be base64 encoded string

2. **Audio URL** (`input_type="url"`)
   - Automatically detects format from URL extension
   - Can optionally specify `audio_format` parameter

### Supported Audio Formats

- `mp3` - MPEG Audio Layer 3
- `mp4` - MPEG-4 Audio
- `mpeg` - MPEG Audio
- `mpga` - MPEG Audio
- `m4a` - MPEG-4 Audio (AAC)
- `wav` - Waveform Audio
- `webm` - WebM Audio

### Supported Models

#### OpenAI Models
- `whisper-large-v3-turbo` - OpenAI Whisper Large v3 Turbo
- `gpt-4o-transcribe` - GPT-4o Transcribe

#### Qwen Models
- `qwen3-asr-flash` - Qwen3 ASR Flash (default)

**Note:** The default model is `qwen3-asr-flash`. Qwen models use DashScope API and have a 10MB file size limit and 3-minute duration limit for `qwen3-asr-flash`.

### Request Examples

#### Base64 Input (Default Qwen Model)

```json
{
  "audio": "UklGRiQAAABXQVZFZm10...",
  "input_type": "base64",
  "audio_format": "wav",
  "model": "qwen3-asr-flash"
}
```

#### Base64 Input (OpenAI Model)

```json
{
  "audio": "UklGRiQAAABXQVZFZm10...",
  "input_type": "base64",
  "audio_format": "wav",
  "model": "whisper-large-v3-turbo"
}
```

#### URL Input

```json
{
  "audio": "https://example.com/audio.mp3",
  "input_type": "url",
  "model": "qwen3-asr-flash"
}
```

#### URL Input with Explicit Format

```json
{
  "audio": "https://example.com/audio",
  "input_type": "url",
  "audio_format": "mp3",
  "model": "qwen3-asr-flash"
}
```

### Response Format

```json
{
  "text": "Transcribed text from the audio"
}
```

## Test Files

- **test_router.py** - Tests for the FastAPI router endpoints
  - Tests request validation
  - Tests different input types (base64, URL)
  - Tests error handling

- **test_stt_full_flow.py** - Integration tests for the complete STT flow
  - Tests end-to-end transcription with mocked OpenAI client
  - Tests all supported models
  - Tests error handling

- **test_transcribe.py** - Unit tests for the transcription function
  - Tests audio transcription logic
  - Tests file handling and cleanup
  - Tests error scenarios

- **conftest.py** - Test fixtures and configuration
  - Provides sample audio data fixtures
  - Configures pytest markers

## Running Tests

### Method 1: Direct pytest usage

```bash
# Run all STT tests
pytest tests/test_endpoints/test_chat/test_qa/test_stt/ -v -m stt

# Run specific test files
pytest tests/test_endpoints/test_chat/test_qa/test_stt/test_router.py -v
pytest tests/test_endpoints/test_chat/test_qa/test_stt/test_transcribe.py -v
pytest tests/test_endpoints/test_chat/test_qa/test_stt/test_stt_full_flow.py -v

# Run tests for specific models
pytest tests/test_endpoints/test_chat/test_qa/test_stt/ -v -k "whisper-1"

# Enable debug output
DEBUG=true pytest tests/test_endpoints/test_chat/test_qa/test_stt/ -v -s
```

### Method 2: Run individual tests

```bash
# Run specific test function
pytest tests/test_endpoints/test_chat/test_qa/test_stt/test_router.py::test_stt_transcription_success -v

# Use parameterized tests
pytest tests/test_endpoints/test_chat/test_qa/test_stt/test_transcribe.py::test_transcribe_audio_success -v
```

## Test Data

The test suite includes sample audio data:
- **demo_base64_input_*.json** - Example base64 encoded audio requests
- **demo_url_input.json** - Example URL-based audio requests
- **demo_*_output.json** - Example responses

## Notes

- Tests use mocked API clients (OpenAI and DashScope) to avoid actual API calls during testing
- Base64 input requires `audio_format` to be specified
- URL input automatically detects format from the URL extension
- All temporary audio files are cleaned up after transcription
- **Qwen Model Limitations:**
  - `qwen3-asr-flash`: Maximum file size 10MB, maximum duration 3 minutes
  - Files exceeding these limits will return a 400 error
- **Model Selection:**
  - The system automatically selects the appropriate API (OpenAI or DashScope) based on the model name
  - Default model is `qwen3-asr-flash` (Qwen model)