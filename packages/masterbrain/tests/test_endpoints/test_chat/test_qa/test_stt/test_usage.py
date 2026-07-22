from types import SimpleNamespace

import pytest

from masterbrain.endpoints.chat.qa.stt.router import transcribe_audio_qwen
from masterbrain.usage import InMemoryUsageSink, bind_usage_sinks


@pytest.mark.asyncio
async def test_dashscope_transcription_records_usage(monkeypatch):
    response = SimpleNamespace(
        status_code=200,
        request_id="dashscope-request-1",
        model="qwen3-asr-flash-2026-07-01",
        usage={"input_tokens": 88, "output_tokens": 12, "total_tokens": 100},
        output=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=[{"text": "transcribed"}])
                )
            ]
        ),
    )

    async def fake_to_thread(_function):
        return response

    monkeypatch.setattr(
        "masterbrain.endpoints.chat.qa.stt.router.asyncio.to_thread",
        fake_to_thread,
    )
    sink = InMemoryUsageSink()

    with bind_usage_sinks(sink):
        text = await transcribe_audio_qwen(
            model_name="qwen3-asr-flash",
            audio_url="https://example.test/audio.wav",
        )

    assert text == "transcribed"
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.provider_request_id == "dashscope-request-1"
    assert event.metadata == {"runtime": "dashscope"}
    assert event.usage.total_tokens == 100
