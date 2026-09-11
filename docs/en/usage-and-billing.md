# Model Usage and Billing Integration

Masterbrain normalizes usage from LiteLLM and provider-specific runtimes into a
stable application contract. An embedding application such as Platform can
persist these immutable events and apply its own versioned pricing rules.

## Ownership boundary

- LiteLLM or the provider SDK supplies raw token counters and, when available,
  an estimated provider cost.
- Masterbrain owns normalization, request correlation, per-call events,
  aggregation, and delivery through a `UsageSink`.
- Platform owns customer identity, pricing versions, credits, invoices,
  currencies, taxes, refunds, and billing reconciliation.

Reusable model calls and scientific reasoning belong to Masterbrain. Host-specific
context selection, permissions, approvals, durable task state, scientific assets,
and tool/device execution remain with Platform and its execution workers. Hosting
Masterbrain in-process does not require sending data to a central Airalogy service.

Do not calculate a customer's charge directly from `provider_cost`. That field,
its explicit `provider_cost_currency`, and `provider_cost_source` are useful for
upstream cost analysis and reconciliation, but provider price maps and exchange
rates can change. A bill should retain the usage event, the selected price rule,
and a price snapshot in Platform's billing currency.

## Stable usage shape

Each real upstream call emits one `ModelUsageEvent`. Its `usage` value includes:

```python
ModelUsage(
    provider="qwen",
    requested_model="qwen3.5-flash",
    resolved_model="qwen3.5-flash-2026-07-01",
    input_tokens=1200,
    output_tokens=300,
    cached_input_tokens=800,
    cache_creation_input_tokens=0,
    reasoning_tokens=100,
    total_tokens=1500,
    provider_cost=Decimal("0.018"),
    provider_cost_currency="CNY",
    provider_cost_source="provider",
    source="provider",
)
```

The event also contains an idempotency key (`event_id`), call ID, provider
request ID, status, latency, timestamps, call type, and an operation context.
Failed and cancelled upstream calls are emitted as events even when their token
usage is unavailable.

## Platform persistence

Register a server-side sink during application startup. The sink should insert
`event_id` under a unique constraint so retries remain idempotent.

```python
from masterbrain.usage import ModelUsageEvent, configure_usage_sinks


class PlatformUsageSink:
    def __init__(self, usage_repository):
        self.usage_repository = usage_repository

    async def record_usage(self, event: ModelUsageEvent) -> None:
        await self.usage_repository.insert_if_absent(
            event_id=event.event_id,
            payload=event.to_dict(),
        )


configure_usage_sinks(PlatformUsageSink(usage_repository))
```

Sink failures are logged and do not turn a successful model response into a
failed user request. A production billing sink should therefore persist
durably, monitor failures, and support reconciliation against provider reports.

## Authenticated request identity

The built-in FastAPI middleware adds an `X-Masterbrain-Operation-Id` response
header and binds the operation to all model calls, including streaming calls.
Its default factory only trusts correlation headers; it deliberately does not
accept tenant or user identity from arbitrary client headers.

An embedding Platform service should supply identity from its authenticated
server-side session:

```python
from masterbrain.fastapi.usage import install_usage_context_middleware
from masterbrain.usage import UsageContext


def platform_usage_context(request):
    principal = request.state.principal
    return UsageContext(
        operation_id=request.headers.get("X-Masterbrain-Operation-Id")
        or create_operation_id(),
        request_id=request.headers.get("X-Request-Id"),
        feature=f"{request.method} {request.url.path}",
        tenant_id=principal.lab_id,
        user_id=principal.user_id,
        project_id=request.path_params.get("project_id"),
    )


install_usage_context_middleware(app, context_factory=platform_usage_context)
```

If Platform calls Masterbrain functions directly instead of hosting its ASGI
middleware, use `bind_usage_context(UsageContext(...))` around the operation.

## Pricing and aggregation

`aggregate_usage_events(events, operation_id=...)` produces an operational
summary. Its cost summary is grouped by currency and never performs implicit
currency conversion. Billing should still price the underlying events
individually because one operation can contain multiple providers, models,
cache rates, or call types. Aggregation rejects events with conflicting tenant,
user, project, or chat identity. A recommended ledger key is:

```text
(provider, resolved_model, call_type, price_version, started_at)
```

Keep `requested_model` as the product choice and `resolved_model` as the actual
provider version. This supports model-specific prices without losing the user's
original selection.

## Runtime coverage

Masterbrain captures:

- LiteLLM chat completions, including final streaming usage chunks
- LiteLLM audio transcription responses
- OpenAI-compatible SDK text embeddings (`call_type="embedding"`)
- LangChain calls used by paper generation
- direct DashScope speech-to-text calls
- every OpenCode assistant/provider call in a code-edit run

LiteLLM streaming requests automatically enable `stream_options.include_usage`.
Masterbrain labels LiteLLM's price-map cost as `USD`; provider-native costs must
carry the currency reported by that provider, such as `CNY` for a RMB charge.
No exchange-rate conversion happens in Masterbrain.
The stream must be consumed to completion, or explicitly closed with `aclose()`,
for its final usage or cancellation event to be emitted.

## Text embeddings (since 0.12.0)

Version 0.12.0 adds a reusable async API and `POST /api/endpoints/embeddings`.
Downstream products should depend on the published package; do not commit
sibling-path dependencies or patched wheels.

```python
from masterbrain.embeddings import EmbeddingRequest, create_embeddings
from masterbrain.usage import UsageContext, bind_usage_context

with bind_usage_context(UsageContext(feature="protocol.index")):
    result = await create_embeddings(EmbeddingRequest(
        model="text-embedding-v4",
        input=["A bounded, authorized excerpt"],
        dimensions=1024,
    ))
# result.model, result.dimensions, result.vectors (in input order)
```

The HTTP request uses the same `model`, `input`, and optional `dimensions` fields.
Supported models are `text-embedding-v4`, `text-embedding-3-small`,
`text-embedding-3-large`, and `text-embedding-ada-002` (omit dimensions for ada).
Each batch accepts one to six non-blank strings, at most 32,768 characters each;
provider token limits still apply. Text is neither truncated nor silently split.
Larger jobs should batch explicitly so hosts can enforce budgets and cancellation.

Credentials and base URLs come from the existing server provider configuration,
never the HTTP payload. The API returns vectors only after validating their count,
indexes, dimensions, and finite numeric values. It performs no model fallback or
automatic retry; upstream failure and cancellation retain their usage events.
No source text or vectors are stored in the metering event.

The host must enforce authentication, authorized context, AI policy, and budgets
before calling; do not expose an unprotected Masterbrain service publicly. For
external deployment, configure a trusted usage sink on that service rather than
trusting tenant headers from callers. When AI is off or unavailable, hosts should
keep local keyword indexing/search working without calling embeddings.

For Platform's existing indexes, retain `text-embedding-v4` and 1024 dimensions.
Changing providers or models can change the vector space even at the same
dimension: reindex explicitly, never mix new query vectors with an incompatible
existing index. Authorization, index storage, and reindex scheduling remain host
responsibilities.
