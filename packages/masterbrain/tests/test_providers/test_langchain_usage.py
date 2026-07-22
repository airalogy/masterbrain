from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import create_chat_model
from masterbrain.providers.langchain_usage import MasterbrainLangChainUsageCallback
from masterbrain.usage import InMemoryUsageSink, bind_usage_sinks


def test_paper_model_installs_usage_callback(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        "masterbrain.endpoints.paper_generation.logic.utils.init_chat_model",
        fake_init_chat_model,
    )
    config = Configuration(
        writer_provider="openai",
        writer_model="qwen3.5-flash",
        writer_model_kwargs={"temperature": 0.2},
    )

    create_chat_model(config)

    assert captured["model"] == "qwen3.5-flash"
    assert captured["model_kwargs"] == {"temperature": 0.2}
    callback = captured["callbacks"][0]
    assert isinstance(callback, MasterbrainLangChainUsageCallback)
    assert callback.provider == "qwen"


@pytest.mark.asyncio
async def test_langchain_callback_records_llm_output_usage():
    callback = MasterbrainLangChainUsageCallback(
        provider="openai",
        requested_model="gpt-4o-mini",
    )
    run_id = uuid4()
    sink = InMemoryUsageSink()
    result = LLMResult(
        generations=[[ChatGeneration(message=AIMessage(content="done"))]],
        llm_output={
            "model_name": "gpt-4o-mini-2026-01-01",
            "token_usage": {
                "prompt_tokens": 25,
                "completion_tokens": 7,
                "total_tokens": 32,
            },
        },
    )

    with bind_usage_sinks(sink):
        await callback.on_chat_model_start({}, [[]], run_id=run_id)
        await callback.on_llm_end(result, run_id=run_id)

    assert len(sink.events) == 1
    assert sink.events[0].call_id == str(run_id)
    assert sink.events[0].metadata == {"runtime": "langchain"}
    assert sink.events[0].usage.resolved_model == "gpt-4o-mini-2026-01-01"
    assert sink.events[0].usage.total_tokens == 32


@pytest.mark.asyncio
async def test_langchain_callback_falls_back_to_message_usage_metadata():
    callback = MasterbrainLangChainUsageCallback(
        provider="qwen",
        requested_model="qwen3.5-flash",
    )
    run_id = uuid4()
    sink = InMemoryUsageSink()
    message = AIMessage(
        id="qwen-request-1",
        content="done",
        usage_metadata={
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "input_token_details": {"cache_read": 60},
            "output_token_details": {"reasoning": 8},
        },
        response_metadata={"model_name": "qwen3.5-flash-2026-07-01"},
    )
    result = LLMResult(generations=[[ChatGeneration(message=message)]])

    with bind_usage_sinks(sink):
        await callback.on_llm_start({}, ["prompt"], run_id=run_id)
        await callback.on_llm_end(result, run_id=run_id)

    usage = sink.events[0].usage
    assert usage.input_tokens == 100
    assert usage.output_tokens == 20
    assert usage.cached_input_tokens == 60
    assert usage.reasoning_tokens == 8
    assert sink.events[0].provider_request_id == "qwen-request-1"


@pytest.mark.asyncio
async def test_langchain_callback_records_failure():
    callback = MasterbrainLangChainUsageCallback(
        provider="openai",
        requested_model="gpt-4o-mini",
    )
    run_id = uuid4()
    sink = InMemoryUsageSink()

    with bind_usage_sinks(sink):
        await callback.on_llm_start({}, ["prompt"], run_id=run_id)
        await callback.on_llm_error(RuntimeError("failed"), run_id=run_id)

    assert sink.events[0].status == "failed"
    assert sink.events[0].error_type == "RuntimeError"
