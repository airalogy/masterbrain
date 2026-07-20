"""Live health checks for configured model providers."""

from __future__ import annotations

import asyncio
from typing import Literal
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from masterbrain import configs
from masterbrain.providers import DEFAULT_PROVIDER_BASE_URL, ProviderName

ProviderHealthStatus = Literal[
    "ok",
    "not_configured",
    "invalid_configuration",
    "unreachable",
    "authentication_failed",
    "permission_denied",
    "rate_limited",
    "provider_error",
    "invalid_response",
    "model_unavailable",
]


class ProviderHealth(BaseModel):
    provider: ProviderName
    status: ProviderHealthStatus
    configured: bool
    default_model: str
    model_available: bool | None = None
    model_count: int | None = None


class ModelProvidersHealth(BaseModel):
    status: Literal["ok", "degraded", "unconfigured"]
    providers: list[ProviderHealth]


router = APIRouter()


def _valid_base_url(base_url: str) -> bool:
    try:
        parsed = urlsplit(base_url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _provider_health(
    provider: ProviderName,
    health_status: ProviderHealthStatus,
    *,
    configured: bool,
    default_model: str,
    model_available: bool | None = None,
    model_count: int | None = None,
) -> ProviderHealth:
    return ProviderHealth(
        provider=provider,
        status=health_status,
        configured=configured,
        default_model=default_model,
        model_available=model_available,
        model_count=model_count,
    )


async def probe_provider(
    provider: ProviderName,
    *,
    api_key: str,
    base_url: str,
    default_model: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ProviderHealth:
    """Validate one provider without generating model output."""

    if not api_key.strip():
        return _provider_health(
            provider,
            "not_configured",
            configured=False,
            default_model=default_model,
        )

    resolved_base_url = base_url.strip() or DEFAULT_PROVIDER_BASE_URL[provider]
    if not _valid_base_url(resolved_base_url):
        return _provider_health(
            provider,
            "invalid_configuration",
            configured=True,
            default_model=default_model,
        )

    try:
        async with httpx.AsyncClient(
            transport=transport,
            timeout=10.0,
        ) as client:
            response = await client.get(
                f"{resolved_base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
    except httpx.RequestError:
        return _provider_health(
            provider,
            "unreachable",
            configured=True,
            default_model=default_model,
        )

    failure_status: ProviderHealthStatus | None = None
    if response.status_code == 401:
        failure_status = "authentication_failed"
    elif response.status_code == 403:
        failure_status = "permission_denied"
    elif response.status_code == 429:
        failure_status = "rate_limited"
    elif response.status_code >= 400:
        failure_status = "provider_error"

    if failure_status is not None:
        return _provider_health(
            provider,
            failure_status,
            configured=True,
            default_model=default_model,
        )

    try:
        payload = response.json()
    except ValueError:
        return _provider_health(
            provider,
            "invalid_response",
            configured=True,
            default_model=default_model,
        )

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        return _provider_health(
            provider,
            "invalid_response",
            configured=True,
            default_model=default_model,
        )

    model_ids = {
        item.get("id")
        for item in payload["data"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    model_available = default_model in model_ids
    return _provider_health(
        provider,
        "ok" if model_available else "model_unavailable",
        configured=True,
        default_model=default_model,
        model_available=model_available,
        model_count=len(model_ids),
    )


async def check_model_providers() -> ModelProvidersHealth:
    providers = await asyncio.gather(
        probe_provider(
            "qwen",
            api_key=configs.DASHSCOPE_API_KEY,
            base_url=configs.DASHSCOPE_BASE_URL,
            default_model=configs.DEFAULT_QWEN_TEXT_MODEL,
        ),
        probe_provider(
            "openai",
            api_key=configs.OPENAI_API_KEY,
            base_url=configs.OPENAI_BASE_URL,
            default_model=configs.DEFAULT_OPENAI_MODEL,
        ),
    )

    configured = [provider for provider in providers if provider.configured]
    if not configured:
        health_status: Literal["ok", "degraded", "unconfigured"] = "unconfigured"
    elif all(provider.status == "ok" for provider in configured):
        health_status = "ok"
    else:
        health_status = "degraded"

    return ModelProvidersHealth(status=health_status, providers=list(providers))


@router.get("/health/providers", response_model=ModelProvidersHealth)
async def get_model_provider_health(response: Response) -> ModelProvidersHealth:
    health = await check_model_providers()
    if health.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return health
