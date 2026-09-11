import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import AuthenticationError, InternalServerError
from openai.resources.embeddings import AsyncEmbeddings
from pydantic import ValidationError

from masterbrain import configs
from masterbrain.embeddings import (
    EmbeddingRequest,
    EmbeddingResponse,
    InvalidEmbeddingResponse,
    create_embeddings,
)
from masterbrain.fastapi.main import app
from masterbrain.providers.litellm import build_litellm_openai_compatible_client
from masterbrain.providers.registry import AvailableModel, detect_model_provider
from masterbrain.usage import (
    InMemoryUsageSink,
    UsageContext,
    bind_usage_context,
    bind_usage_sinks,
)
from masterbrain.utils import llm


@pytest.mark.parametrize(
    "overrides",
    [
        {"dimensions": True},
        {"vectors": []},
        {"vectors": [[0.1]]},
        {"vectors": [[float("nan"), 0.2]]},
        {"vectors": [[True, 0.2]]},
        {"vectors": [["0.1", 0.2]]},
    ],
)
def test_public_response_contract_rejects_invalid_external_results(overrides):
    with pytest.raises(ValidationError):
        EmbeddingResponse.model_validate(
            {
                "model": "text-embedding-v4",
                "dimensions": 2,
                "vectors": [[0.1, 0.2]],
                **overrides,
            }
        )


@pytest.fixture(autouse=True)
def configured_clients(monkeypatch):
    monkeypatch.setattr(llm, "DASHSCOPE_API_KEY", "synthetic-key")
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "synthetic-key")
    for attribute, provider in [
        ("DASHSCOPE_CLIENT", "qwen"),
        ("OPENAI_CLIENT", "openai"),
    ]:
        monkeypatch.setattr(
            configs,
            attribute,
            build_litellm_openai_compatible_client(
                provider=provider,
                api_key="synthetic-key",
                base_url="https://embedding.example.test/v1",
            ),
        )

    # Every test is offline, including tests of paths that must not call a provider.
    async def unexpected_provider(*_args, **_kwargs):
        raise AssertionError("Unexpected provider call")

    monkeypatch.setattr(httpx.AsyncClient, "send", unexpected_provider)


def provider_response(**overrides):
    return {
        "_request_id": "embedding-call",
        "model": "text-embedding-v4",
        "data": [{"index": 0, "embedding": [0.1, 0.2]}],
        "usage": {"prompt_tokens": 12, "total_tokens": 12},
        "_hidden_params": {"response_cost": 0.00001},
        **overrides,
    }


def fake_provider(monkeypatch, response=None, error=None):
    calls = []

    async def aembedding(_resource, **kwargs):
        calls.append(kwargs)
        if error is not None:
            raise error
        result = response if response is not None else provider_response()
        return SimpleNamespace(**result) if isinstance(result, dict) else result

    monkeypatch.setattr(AsyncEmbeddings, "create", aembedding)
    return calls


def request(**overrides):
    return EmbeddingRequest.model_validate(
        {
            "model": "text-embedding-v4",
            "input": ["research evidence"],
            "dimensions": 2,
            **overrides,
        }
    )


@pytest.mark.parametrize(
    "model,provider",
    [
        ("text-embedding-v4", "qwen"),
        ("text-embedding-3-small", "openai"),
        ("text-embedding-3-large", "openai"),
        ("text-embedding-ada-002", "openai"),
    ],
)
def test_embedding_model_routing_does_not_change_chat_model_catalog(model, provider):
    from typing import get_args

    assert detect_model_provider(model) == provider
    assert model not in get_args(AvailableModel)


def test_embeddings_use_configured_transport_and_record_trusted_usage(monkeypatch):
    calls = fake_provider(monkeypatch)
    sink = InMemoryUsageSink()
    context = UsageContext(
        operation_id="operation-embedding", tenant_id="lab", user_id="user"
    )
    with bind_usage_sinks(sink), bind_usage_context(context):
        result = asyncio.run(create_embeddings(request()))
    assert result.vectors == [[0.1, 0.2]]
    assert calls == [
        {
            "model": "text-embedding-v4",
            "input": ["research evidence"],
            "dimensions": 2,
            "encoding_format": "float",
            "timeout": 60,
        }
    ]
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.context is context
    assert event.call_type == "embedding"
    assert event.status == "succeeded"
    assert event.usage.provider == "qwen"
    assert event.usage.input_tokens == event.usage.total_tokens == 12
    assert event.usage.output_tokens == 0
    assert event.usage.resolved_model == "text-embedding-v4"
    assert event.usage.provider_cost is None
    assert event.usage.provider_cost_currency is None
    assert event.provider_request_id == "embedding-call"
    assert "research evidence" not in str(event.to_dict())


def test_legacy_vector_dimensions_are_preserved(monkeypatch):
    calls = fake_provider(
        monkeypatch, provider_response(data=[{"index": 0, "embedding": [0.1] * 1024}])
    )
    result = asyncio.run(create_embeddings(request(dimensions=1024)))
    assert result.dimensions == len(result.vectors[0]) == calls[0]["dimensions"] == 1024


def test_optional_dimensions_and_out_of_order_sdk_objects(monkeypatch):
    calls = fake_provider(
        monkeypatch,
        SimpleNamespace(
            model="text-embedding-3-small",
            data=[
                SimpleNamespace(index=1, embedding=[3, 4]),
                SimpleNamespace(index=0, embedding=[1, 2]),
            ],
        ),
    )
    result = asyncio.run(
        create_embeddings(
            request(
                model="text-embedding-3-small",
                input=["first", "second"],
                dimensions=None,
            )
        )
    )
    assert "dimensions" not in calls[0]
    assert result.vectors == [[1.0, 2.0], [3.0, 4.0]]
    assert result.dimensions == 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"input": []},
        {"input": [""]},
        {"input": [" \n "]},
        {"input": [1]},
        {"input": ["a"] * 7},
        {"input": ["a" * 32769]},
        {"dimensions": 0},
        {"dimensions": True},
        {"dimensions": "1024"},
        {"dimensions": 8193},
        {"model": "gpt-4o"},
        {"model": "openai/text-embedding-v4"},
        {"model": "text-embedding-ada-002", "dimensions": 2},
        {"api_base": "https://untrusted.test"},
        {"api_key": "untrusted"},
        {"tenant_id": "other-lab"},
    ],
)
def test_invalid_requests_fail_before_provider_call(overrides):
    with pytest.raises(ValidationError):
        request(**overrides)


@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"index": 0, "embedding": [0.1]}],
        [{"index": 0, "embedding": [0.1, 0.2]}, {"index": 0, "embedding": [0.1, 0.2]}],
        [{"index": 1, "embedding": [0.1, 0.2]}],
        [{"index": True, "embedding": [0.1, 0.2]}],
        [{"index": 0, "embedding": []}],
        [{"index": 0, "embedding": "base64-encoded-vector"}],
        [{"index": 0, "embedding": [True, 0.2]}],
        [{"index": 0, "embedding": ["0.1", 0.2]}],
        [{"index": 0, "embedding": [float("nan"), 0.2]}],
        [{"index": 0, "embedding": [float("inf"), 0.2]}],
        [{"index": 0, "embedding": [10**1000, 0.2]}],
    ],
)
def test_invalid_provider_vectors_cannot_reach_index(monkeypatch, data):
    fake_provider(monkeypatch, provider_response(data=data))
    with pytest.raises(InvalidEmbeddingResponse):
        asyncio.run(create_embeddings(request()))


@pytest.mark.parametrize(
    "error,status",
    [
        (RuntimeError("synthetic failure"), "failed"),
        (asyncio.CancelledError(), "cancelled"),
    ],
)
def test_failure_and_cancellation_are_metered_without_fallback(
    monkeypatch, error, status
):
    calls = fake_provider(monkeypatch, error=error)
    sink = InMemoryUsageSink()
    with bind_usage_sinks(sink), pytest.raises(type(error)):
        asyncio.run(create_embeddings(request()))
    assert len(calls) == len(sink.events) == 1
    assert sink.events[0].status == status
    assert sink.events[0].usage.source == "unavailable"


def test_http_endpoint_correlates_usage_without_trusting_identity_headers(monkeypatch):
    fake_provider(monkeypatch)
    sink = InMemoryUsageSink()
    with bind_usage_sinks(sink):
        response = TestClient(app).post(
            "/api/endpoints/embeddings",
            json=request().model_dump(),
            headers={
                "X-Masterbrain-Operation-Id": "operation-test",
                "X-Tenant-Id": "untrusted-lab",
            },
        )
    assert response.status_code == 200
    assert response.json()["vectors"] == [[0.1, 0.2]]
    assert response.headers["X-Masterbrain-Operation-Id"] == "operation-test"
    assert len(sink.events) == 1
    assert sink.events[0].context.operation_id == "operation-test"
    assert sink.events[0].context.tenant_id is None


def test_http_endpoint_rejects_invalid_request_without_provider():
    response = TestClient(app).post(
        "/api/endpoints/embeddings",
        json=request().model_dump() | {"api_base": "https://untrusted.test"},
    )
    assert response.status_code == 422


def test_missing_provider_key_does_not_fall_back_to_other_provider(monkeypatch):
    monkeypatch.setattr(llm, "DASHSCOPE_API_KEY", "")
    response = TestClient(app).post(
        "/api/endpoints/embeddings", json=request().model_dump()
    )
    assert response.status_code == 400
    assert "DASHSCOPE_API_KEY" in response.json()["detail"]


def test_http_endpoint_does_not_reflect_invalid_provider_content(monkeypatch):
    fake_provider(
        monkeypatch,
        provider_response(data=[{"index": 0, "embedding": "private-source-content"}]),
    )
    response = TestClient(app).post(
        "/api/endpoints/embeddings", json=request().model_dump()
    )
    assert response.status_code == 502
    assert "private-source-content" not in response.text


def test_http_provider_error_uses_existing_error_mapping(monkeypatch):
    error = AuthenticationError(
        "synthetic authentication failure",
        response=httpx.Response(
            401, request=httpx.Request("POST", "https://embedding.example.test/v1")
        ),
        body={},
    )
    fake_provider(monkeypatch, error=error)
    response = TestClient(app).post(
        "/api/endpoints/embeddings", json=request().model_dump()
    )
    assert response.status_code == 401


@pytest.mark.parametrize("status_code", [200, 500])
def test_real_sdk_preserves_qwen_dimensions_and_does_not_retry(
    monkeypatch, status_code
):
    calls = []

    async def send(_client, outgoing, **_kwargs):
        assert str(outgoing.url) == "https://embedding.example.test/v1/embeddings"
        assert outgoing.headers["authorization"] == "Bearer synthetic-key"
        calls.append(json.loads(outgoing.content))
        body = provider_response(
            data=[{"object": "embedding", "index": 0, "embedding": [0.1] * 1024}]
        )
        if status_code != 200:
            body = {"error": {"message": "synthetic outage", "type": "server_error"}}
        return httpx.Response(
            status_code,
            request=outgoing,
            json=body,
            headers={"x-request-id": "embedding-http-call"},
        )

    def forbidden_sync_send(*_args, **_kwargs):
        raise AssertionError("Unexpected synchronous network access")

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    monkeypatch.setattr(httpx.Client, "send", forbidden_sync_send)
    sink = InMemoryUsageSink()
    with bind_usage_sinks(sink):
        if status_code == 200:
            result = asyncio.run(create_embeddings(request(dimensions=1024)))
            assert result.dimensions == 1024
        else:
            with pytest.raises(InternalServerError):
                asyncio.run(create_embeddings(request(dimensions=1024)))
    assert len(calls) == len(sink.events) == 1
    assert calls[0]["dimensions"] == 1024
    assert calls[0]["model"] == "text-embedding-v4"
    assert calls[0]["encoding_format"] == "float"
    assert sink.events[0].status == ("succeeded" if status_code == 200 else "failed")
    if status_code == 200:
        assert sink.events[0].provider_request_id == "embedding-http-call"
