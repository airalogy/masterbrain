from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from masterbrain.fastapi.usage import install_usage_context_middleware
from masterbrain.usage import UsageContext, get_usage_context


def _test_app(*, context_factory=None) -> FastAPI:
    app = FastAPI()
    if context_factory is None:
        install_usage_context_middleware(app)
    else:
        install_usage_context_middleware(app, context_factory=context_factory)

    @app.get("/usage-context")
    async def read_usage_context():
        context = get_usage_context()
        assert context is not None
        return {
            "operation_id": context.operation_id,
            "request_id": context.request_id,
            "tenant_id": context.tenant_id,
            "feature": context.feature,
        }

    @app.get("/stream-context")
    async def stream_usage_context():
        async def content():
            context = get_usage_context()
            assert context is not None
            yield context.operation_id

        return StreamingResponse(content())

    return app


def test_usage_context_middleware_correlates_request_and_response():
    client = TestClient(_test_app())
    response = client.get(
        "/usage-context",
        headers={
            "X-Masterbrain-Operation-Id": "operation-from-platform",
            "X-Request-Id": "request-1",
            # Identity headers are deliberately not trusted by the default factory.
            "X-Tenant-Id": "spoofed-tenant",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Masterbrain-Operation-Id"] == "operation-from-platform"
    assert response.json() == {
        "operation_id": "operation-from-platform",
        "request_id": "request-1",
        "tenant_id": None,
        "feature": "GET /usage-context",
    }


def test_embedding_app_can_supply_authenticated_billing_identity():
    def context_factory(request):
        return UsageContext(
            operation_id="platform-operation",
            tenant_id="authenticated-lab",
            user_id="authenticated-user",
            feature=request.url.path,
        )

    client = TestClient(_test_app(context_factory=context_factory))
    response = client.get("/usage-context")

    assert response.headers["X-Masterbrain-Operation-Id"] == "platform-operation"
    assert response.json()["tenant_id"] == "authenticated-lab"


def test_usage_context_remains_bound_while_streaming_response_is_consumed():
    client = TestClient(_test_app())
    response = client.get(
        "/stream-context",
        headers={"X-Masterbrain-Operation-Id": "stream-operation"},
    )

    assert response.text == "stream-operation"
    assert response.headers["X-Masterbrain-Operation-Id"] == "stream-operation"
