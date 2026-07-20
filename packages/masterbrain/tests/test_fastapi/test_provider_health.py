import asyncio

import httpx
from fastapi.testclient import TestClient

from masterbrain.fastapi import provider_health
from masterbrain.fastapi.main import app


def test_unconfigured_provider_does_not_make_request():
    health = asyncio.run(
        provider_health.probe_provider(
            "qwen",
            api_key="",
            base_url="",
            default_model="qwen3.5-flash",
        )
    )

    assert health.status == "not_configured"
    assert health.configured is False


def test_provider_probe_rejects_invalid_base_url():
    health = asyncio.run(
        provider_health.probe_provider(
            "qwen",
            api_key="configured-key",
            base_url="not-a-url",
            default_model="qwen3.5-flash",
        )
    )

    assert health.status == "invalid_configuration"
    assert health.configured is True


def test_provider_probe_reports_authentication_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid key"}, request=request)

    health = asyncio.run(
        provider_health.probe_provider(
            "qwen",
            api_key="invalid-key",
            base_url="https://provider.example/v1",
            default_model="qwen3.5-flash",
            transport=httpx.MockTransport(handler),
        )
    )

    assert health.status == "authentication_failed"
    assert health.model_available is None


def test_provider_probe_checks_default_model_access():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "qwen3.5-flash"},
                    {"id": "qwen3.5-plus"},
                ]
            },
            request=request,
        )

    health = asyncio.run(
        provider_health.probe_provider(
            "qwen",
            api_key="configured-key",
            base_url="https://provider.example/v1",
            default_model="qwen3.5-flash",
            transport=httpx.MockTransport(handler),
        )
    )

    assert health.status == "ok"
    assert health.model_available is True
    assert health.model_count == 2


def test_health_endpoint_returns_503_when_no_provider_is_configured(monkeypatch):
    monkeypatch.setattr(provider_health.configs, "DASHSCOPE_API_KEY", "")
    monkeypatch.setattr(provider_health.configs, "OPENAI_API_KEY", "")

    response = TestClient(app).get("/api/health/providers")

    assert response.status_code == 503
    assert response.json()["status"] == "unconfigured"


def test_health_endpoint_returns_200_for_healthy_configured_provider(monkeypatch):
    async def healthy_providers():
        return provider_health.ModelProvidersHealth(
            status="ok",
            providers=[
                provider_health.ProviderHealth(
                    provider="qwen",
                    status="ok",
                    configured=True,
                    default_model="qwen3.5-flash",
                    model_available=True,
                    model_count=3,
                )
            ],
        )

    monkeypatch.setattr(provider_health, "check_model_providers", healthy_providers)

    response = TestClient(app).get("/api/health/providers")

    assert response.status_code == 200
    assert response.json()["providers"][0]["model_available"] is True
