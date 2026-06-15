"""Helpers for LLM provider selection, credential validation, and error mapping."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    RateLimitError,
)

from masterbrain.configs import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from masterbrain.providers import DEFAULT_PROVIDER_BASE_URL, ProviderName, detect_model_provider

PROXY_ENV_NAMES = (
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "ALL_PROXY",
    "all_proxy",
)


def required_api_key_env(model_name: str) -> str:
    """Return the env var name required for the selected model provider."""

    provider = detect_model_provider(model_name)
    if provider == "openai":
        return "OPENAI_API_KEY"
    return "DASHSCOPE_API_KEY"


def missing_api_key_message(model_name: str) -> str | None:
    """Return a user-facing message when the selected provider key is missing."""

    provider = detect_model_provider(model_name)
    if provider == "openai" and not OPENAI_API_KEY.strip():
        return (
            f"OPENAI_API_KEY is not configured. Model `{model_name}` requires a valid OpenAI "
            "API key. Add it to your `.env` file and restart Masterbrain."
        )
    if provider == "qwen" and not DASHSCOPE_API_KEY.strip():
        return (
            f"DASHSCOPE_API_KEY is not configured. Model `{model_name}` requires a valid "
            "DashScope/Qwen API key. Add it to your `.env` file and restart Masterbrain."
        )
    return None


def ensure_model_api_key(model_name: str) -> None:
    """Raise a 400 HTTP error when the selected model provider key is missing."""

    message = missing_api_key_message(model_name)
    if message:
        raise HTTPException(status_code=400, detail=message)


def qwen_chat_extra_body(
    model_name: str,
    *,
    enable_thinking: bool = False,
    enable_search: bool = False,
) -> dict[str, bool] | None:
    """Return DashScope/Qwen-only chat options for models that support them."""

    try:
        provider = detect_model_provider(model_name)
    except ValueError:
        return None

    if provider != "qwen":
        return None

    return {
        "enable_thinking": enable_thinking,
        "enable_search": enable_search,
    }


def _extract_provider_error_message(exc: Exception) -> str | None:
    """Try to recover the provider's human-readable message from an SDK exception."""

    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = body.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

    message = str(exc).strip()
    return message or None


def _sanitize_url(url: str) -> str:
    """Drop credentials and query fragments before reflecting URLs back to the user."""

    value = url.strip()
    if not value:
        return value

    try:
        parsed = urlsplit(value)
    except ValueError:
        return value

    hostname = parsed.hostname
    if hostname is None:
        return value

    netloc = hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"

    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def _looks_like_absolute_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.hostname)


def _configured_base_url(model_name: str | None) -> str | None:
    if not model_name:
        return None

    try:
        provider = detect_model_provider(model_name)
    except ValueError:
        return None

    if provider == "openai":
        return OPENAI_BASE_URL.strip() or DEFAULT_PROVIDER_BASE_URL["openai"]
    return DASHSCOPE_BASE_URL.strip() or DEFAULT_PROVIDER_BASE_URL["qwen"]


def _extract_request_target(exc: Exception) -> str | None:
    request = getattr(exc, "request", None)
    if request is None:
        return None

    method = getattr(request, "method", None)
    url = getattr(request, "url", None)
    if url is None:
        return method

    target = _sanitize_url(str(url))
    if method:
        return f"{method} {target}"
    return target


def _extract_exception_chain_messages(exc: Exception) -> list[str]:
    messages: list[str] = []
    seen_messages: set[str] = set()
    seen_exceptions: set[int] = set()
    current = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
    top_level_message = str(exc).strip().lower()

    while current is not None and id(current) not in seen_exceptions:
        seen_exceptions.add(id(current))
        message = str(current).strip()
        normalized = message.lower()
        if message and normalized != top_level_message and normalized not in seen_messages:
            seen_messages.add(normalized)
            messages.append(message)
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)

    return messages


def _active_proxy_settings() -> list[str]:
    settings: list[str] = []

    for env_name in PROXY_ENV_NAMES:
        value = os.environ.get(env_name, "").strip()
        if not value:
            continue
        settings.append(f"{env_name}={_sanitize_url(value)}")

    return settings


def _looks_like_local_proxy(proxy_setting: str) -> bool:
    _, _, proxy_url = proxy_setting.partition("=")
    try:
        parsed = urlsplit(proxy_url)
    except ValueError:
        return False
    return parsed.hostname in {"127.0.0.1", "localhost", "::1", "0.0.0.0"}


def _build_connection_hint(
    *,
    base_url: str | None,
    proxy_settings: list[str],
    cause_messages: list[str],
) -> str | None:
    if base_url and not _looks_like_absolute_url(base_url):
        return (
            f"Configured base URL `{base_url}` is not a valid absolute URL. "
            "Fix the corresponding `.env` value and restart the backend."
        )

    if any(_looks_like_local_proxy(setting) for setting in proxy_settings):
        return (
            "Detected proxy environment variables pointing to a local proxy. "
            "If that proxy is not running, start it or unset `http_proxy`, "
            "`https_proxy`, and `all_proxy`, then restart the backend."
        )

    cause_blob = " ".join(cause_messages).lower()
    if any(
        token in cause_blob
        for token in (
            "could not resolve host",
            "name or service not known",
            "temporary failure in name resolution",
            "nodename nor servname provided",
        )
    ):
        return (
            "DNS resolution failed while reaching the model provider. "
            "Check your network, DNS, or proxy settings."
        )

    if any(token in cause_blob for token in ("connection refused", "failed to connect")):
        return (
            "The TCP connection was refused. Check whether the configured provider base URL "
            "or proxy target is reachable from this machine."
        )

    if any(token in cause_blob for token in ("timed out", "timeout")):
        return "The network connection timed out before the model provider responded."

    return None


def _build_api_connection_detail(
    exc: APIConnectionError,
    *,
    model_name: str | None,
    provider_message: str | None,
) -> str:
    lines: list[str] = []

    if model_name:
        lines.append(f"Masterbrain could not connect to the model provider for `{model_name}`.")
        try:
            provider = detect_model_provider(model_name)
        except ValueError:
            provider = None
        if provider:
            lines.append(f"Provider: `{provider}`")
    else:
        lines.append("Masterbrain could not connect to the model provider.")

    base_url = _configured_base_url(model_name)
    if base_url:
        lines.append(f"Base URL: `{_sanitize_url(base_url)}`")

    request_target = _extract_request_target(exc)
    if request_target:
        lines.append(f"Request target: `{request_target}`")

    cause_messages = _extract_exception_chain_messages(exc)
    if cause_messages:
        lines.append(f"Underlying error: {cause_messages[0]}")
    elif provider_message and provider_message.lower() != "connection error.":
        lines.append(f"Provider message: {provider_message}")

    proxy_settings = _active_proxy_settings()
    if proxy_settings:
        formatted = ", ".join(f"`{setting}`" for setting in proxy_settings)
        lines.append(f"Detected proxy env: {formatted}")

    hint = _build_connection_hint(
        base_url=base_url,
        proxy_settings=proxy_settings,
        cause_messages=cause_messages,
    )
    if hint:
        lines.append(f"Hint: {hint}")

    return "\n".join(lines)


def llm_http_exception(exc: Exception, model_name: str | None = None) -> HTTPException:
    """Map SDK/provider failures into user-facing HTTP errors."""

    provider_message = _extract_provider_error_message(exc)

    if isinstance(exc, AuthenticationError):
        if model_name:
            missing_message = missing_api_key_message(model_name)
            if missing_message:
                return HTTPException(status_code=400, detail=missing_message)

            env_name = required_api_key_env(model_name)
            detail = (
                f"{env_name} was rejected by the model provider for `{model_name}`. "
                "Check that the API key is correct, active, and belongs to the expected provider."
            )
            if provider_message:
                detail = f"{detail}\nProvider message: {provider_message}"
            return HTTPException(status_code=401, detail=detail)

        detail = "Model API authentication failed. Check that the corresponding API key is configured correctly."
        if provider_message:
            detail = f"{detail}\nProvider message: {provider_message}"
        return HTTPException(status_code=401, detail=detail)

    if isinstance(exc, PermissionDeniedError):
        detail = provider_message or "The model provider denied this request."
        return HTTPException(status_code=403, detail=detail)

    if isinstance(exc, RateLimitError):
        detail = provider_message or "The model provider rate limit was exceeded."
        return HTTPException(status_code=429, detail=detail)

    if isinstance(exc, APITimeoutError):
        detail = provider_message or "The model request timed out."
        return HTTPException(status_code=504, detail=detail)

    if isinstance(exc, APIConnectionError):
        detail = _build_api_connection_detail(
            exc,
            model_name=model_name,
            provider_message=provider_message,
        )
        return HTTPException(status_code=502, detail=detail)

    if isinstance(exc, BadRequestError):
        detail = provider_message or "The model request was rejected as invalid."
        return HTTPException(status_code=400, detail=detail)

    if isinstance(exc, APIStatusError):
        status_code = exc.status_code if isinstance(exc.status_code, int) else 500
        detail = provider_message or "The model provider returned an unexpected error."
        return HTTPException(status_code=status_code, detail=detail)

    detail = provider_message or str(exc) or "Unexpected model runtime error."
    return HTTPException(status_code=500, detail=detail)


async def preflight_text_stream(
    stream: AsyncGenerator[str, None],
    *,
    model_name: str | None = None,
) -> AsyncGenerator[str, None]:
    """Pull the first chunk early so auth/config errors become normal HTTP responses."""

    try:
        first_chunk = await anext(stream)
    except StopAsyncIteration:
        async def empty_stream() -> AsyncGenerator[str, None]:
            if False:
                yield ""

        return empty_stream()
    except HTTPException:
        raise
    except Exception as exc:
        raise llm_http_exception(exc, model_name) from exc

    async def chained_stream() -> AsyncGenerator[str, None]:
        yield first_chunk
        async for chunk in stream:
            yield chunk

    return chained_stream()
