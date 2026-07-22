from types import SimpleNamespace

import pytest

from masterbrain.usage import (
    InMemoryUsageSink,
    UsageContext,
    bind_usage_context,
    bind_usage_sinks,
)
from masterbrain.providers.litellm import (
    build_litellm_openai_compatible_client,
    normalize_litellm_model_name,
)


class FakeAsyncStream:
    def __init__(self, *chunks):
        self._chunks = iter(chunks)
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._chunks)
        except StopIteration:
            raise StopAsyncIteration

    async def aclose(self):
        self.closed = True


def test_normalize_qwen_model_uses_openai_compatible_prefix():
    assert (
        normalize_litellm_model_name(
            "qwen3.5-flash",
            provider="qwen",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        == "openai/qwen3.5-flash"
    )


def test_normalize_openai_model_keeps_official_model_without_custom_base():
    assert (
        normalize_litellm_model_name("gpt-4o-mini", provider="openai") == "gpt-4o-mini"
    )


def test_normalize_openai_model_prefixes_custom_openai_compatible_base():
    assert (
        normalize_litellm_model_name(
            "gpt-4o-mini",
            provider="openai",
            api_base="https://example.test/v1",
        )
        == "openai/gpt-4o-mini"
    )


@pytest.mark.asyncio
async def test_non_stream_chat_completion_records_usage(monkeypatch):
    async def fake_acompletion(**_kwargs):
        return SimpleNamespace(
            id="call-non-stream",
            model="gpt-4o-mini-2026-01-01",
            choices=[],
            usage={
                "prompt_tokens": 20,
                "completion_tokens": 5,
                "total_tokens": 25,
            },
            _hidden_params={"response_cost": 0.0001},
        )

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(acompletion=fake_acompletion),
    )
    client = build_litellm_openai_compatible_client(
        provider="openai",
        api_key="test-key",
    )
    sink = InMemoryUsageSink()

    with bind_usage_sinks(sink):
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
        )

    assert response.id == "call-non-stream"
    assert sink.events[0].usage.total_tokens == 25
    assert str(sink.events[0].usage.provider_cost) == "0.0001"
    assert sink.events[0].usage.provider_cost_currency == "USD"
    assert sink.events[0].usage.provider_cost_source == "litellm"


@pytest.mark.asyncio
async def test_chat_completion_facade_delegates_to_litellm(monkeypatch):
    calls = []

    async def fake_acompletion(**kwargs):
        calls.append(kwargs)
        return FakeAsyncStream(
            SimpleNamespace(id="call-1", model="qwen3.5-flash", choices=[object()]),
            SimpleNamespace(
                id="call-1",
                model="qwen3.5-flash-2026-07-01",
                choices=[],
                usage={
                    "prompt_tokens": 1200,
                    "completion_tokens": 300,
                    "total_tokens": 1500,
                    "prompt_tokens_details": {"cached_tokens": 800},
                    "completion_tokens_details": {"reasoning_tokens": 100},
                },
                _hidden_params={"response_cost": 0.0025},
            ),
        )

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(acompletion=fake_acompletion),
    )

    client = build_litellm_openai_compatible_client(
        provider="qwen",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    sink = InMemoryUsageSink()
    context = UsageContext(operation_id="operation-1", tenant_id="lab-1")
    with bind_usage_context(context), bind_usage_sinks(sink):
        stream = await client.chat.completions.create(
            model="qwen3.5-flash",
            messages=[{"role": "user", "content": "hello"}],
            stream=True,
            stream_options={"some_future_option": True},
            extra_body={"enable_thinking": False},
        )
    # Streaming may outlive the request-local ContextVar scope; the tracker
    # keeps the context and sink selected when the upstream call starts.
    chunks = [chunk async for chunk in stream]

    assert len(chunks) == 2
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.context is context
    assert event.status == "succeeded"
    assert event.provider_request_id == "call-1"
    assert event.usage.provider == "qwen"
    assert event.usage.requested_model == "qwen3.5-flash"
    assert event.usage.resolved_model == "qwen3.5-flash-2026-07-01"
    assert event.usage.input_tokens == 1200
    assert event.usage.output_tokens == 300
    assert event.usage.cached_input_tokens == 800
    assert event.usage.reasoning_tokens == 100
    assert str(event.usage.provider_cost) == "0.0025"
    assert event.usage.provider_cost_currency == "USD"

    assert calls == [
        {
            "model": "openai/qwen3.5-flash",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
            "stream_options": {
                "some_future_option": True,
                "include_usage": True,
            },
            "extra_body": {"enable_thinking": False},
            "api_key": "test-key",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }
    ]


@pytest.mark.asyncio
async def test_audio_transcription_facade_delegates_to_litellm(monkeypatch):
    calls = []

    async def fake_atranscription(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            id="transcription-1",
            model="gpt-4o-transcribe-2026-01-01",
            text="hello",
            usage={"input_tokens": 40, "output_tokens": 5, "total_tokens": 45},
        )

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(atranscription=fake_atranscription),
    )

    client = build_litellm_openai_compatible_client(
        provider="openai",
        api_key="test-key",
    )

    sink = InMemoryUsageSink()
    with bind_usage_sinks(sink):
        await client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=object(),
        )

    assert calls[0]["model"] == "gpt-4o-transcribe"
    assert calls[0]["api_key"] == "test-key"
    assert "api_base" not in calls[0]
    assert sink.events[0].call_type == "audio.transcription"
    assert sink.events[0].provider_request_id == "transcription-1"
    assert sink.events[0].usage.total_tokens == 45


@pytest.mark.asyncio
async def test_chat_completion_failure_is_recorded(monkeypatch):
    async def fake_acompletion(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(acompletion=fake_acompletion),
    )
    client = build_litellm_openai_compatible_client(
        provider="openai",
        api_key="test-key",
    )
    sink = InMemoryUsageSink()

    with (
        bind_usage_sinks(sink),
        pytest.raises(RuntimeError, match="provider unavailable"),
    ):
        await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
        )

    assert len(sink.events) == 1
    assert sink.events[0].status == "failed"
    assert sink.events[0].error_type == "RuntimeError"
    assert sink.events[0].usage.available is False


@pytest.mark.asyncio
async def test_closing_stream_without_usage_records_cancellation(monkeypatch):
    raw_stream = FakeAsyncStream(SimpleNamespace(choices=[object()]))

    async def fake_acompletion(**_kwargs):
        return raw_stream

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(acompletion=fake_acompletion),
    )
    client = build_litellm_openai_compatible_client(
        provider="openai",
        api_key="test-key",
    )
    sink = InMemoryUsageSink()

    with bind_usage_sinks(sink):
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
            stream=True,
        )
        await stream.__anext__()
        await stream.aclose()

    assert raw_stream.closed is True
    assert sink.events[0].status == "cancelled"
