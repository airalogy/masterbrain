from types import SimpleNamespace

import pytest

from masterbrain.providers.litellm import (
    build_litellm_openai_compatible_client,
    normalize_litellm_model_name,
)


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
    assert normalize_litellm_model_name("gpt-4o-mini", provider="openai") == "gpt-4o-mini"


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
async def test_chat_completion_facade_delegates_to_litellm(monkeypatch):
    calls = []

    async def fake_acompletion(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[])

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(acompletion=fake_acompletion),
    )

    client = build_litellm_openai_compatible_client(
        provider="qwen",
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    await client.chat.completions.create(
        model="qwen3.5-flash",
        messages=[{"role": "user", "content": "hello"}],
        stream=True,
        extra_body={"enable_thinking": False},
    )

    assert calls == [
        {
            "model": "openai/qwen3.5-flash",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
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
        return SimpleNamespace(text="hello")

    monkeypatch.setattr(
        "masterbrain.providers.litellm._load_litellm",
        lambda: SimpleNamespace(atranscription=fake_atranscription),
    )

    client = build_litellm_openai_compatible_client(
        provider="openai",
        api_key="test-key",
    )

    await client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=object(),
    )

    assert calls[0]["model"] == "gpt-4o-transcribe"
    assert calls[0]["api_key"] == "test-key"
    assert "api_base" not in calls[0]

