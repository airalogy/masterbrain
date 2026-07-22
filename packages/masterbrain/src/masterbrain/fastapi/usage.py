"""FastAPI/ASGI request correlation for model usage events."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from masterbrain.usage import UsageContext, bind_usage_context

OPERATION_ID_HEADER = "X-Masterbrain-Operation-Id"
REQUEST_ID_HEADER = "X-Request-Id"

UsageContextFactory = Callable[[Request], UsageContext | Awaitable[UsageContext]]


def _safe_header_value(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value or len(value) > 128 or any(ord(character) < 32 for character in value):
        return None
    return value


def default_usage_context_factory(request: Request) -> UsageContext:
    """Build a correlation-only context without trusting billing identity headers."""

    return UsageContext(
        operation_id=_safe_header_value(request.headers.get(OPERATION_ID_HEADER))
        or str(uuid4()),
        request_id=_safe_header_value(request.headers.get(REQUEST_ID_HEADER)),
        feature=f"{request.method} {request.url.path}",
    )


class UsageContextMiddleware:
    """Bind request metadata until the full response, including streams, completes."""

    def __init__(
        self,
        app: ASGIApp,
        context_factory: UsageContextFactory = default_usage_context_factory,
    ) -> None:
        self.app = app
        self.context_factory = context_factory

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        context_or_awaitable = self.context_factory(request)
        context = (
            await context_or_awaitable
            if inspect.isawaitable(context_or_awaitable)
            else context_or_awaitable
        )
        if not isinstance(context, UsageContext):
            raise TypeError("usage context factory must return UsageContext")

        async def send_with_operation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers[OPERATION_ID_HEADER] = context.operation_id
            await send(message)

        with bind_usage_context(context):
            await self.app(scope, receive, send_with_operation_id)


def install_usage_context_middleware(
    app: FastAPI,
    *,
    context_factory: UsageContextFactory = default_usage_context_factory,
) -> None:
    """Install usage correlation; call before the application starts serving."""

    app.add_middleware(UsageContextMiddleware, context_factory=context_factory)


__all__ = [
    "OPERATION_ID_HEADER",
    "REQUEST_ID_HEADER",
    "UsageContextFactory",
    "UsageContextMiddleware",
    "default_usage_context_factory",
    "install_usage_context_middleware",
]
