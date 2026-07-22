import asyncio
import json
from decimal import Decimal

import pytest

from masterbrain.usage import (
    InMemoryUsageSink,
    UsageCallTracker,
    UsageContext,
    aggregate_usage_events,
    bind_usage_context,
    bind_usage_sinks,
    get_usage_context,
    normalize_model_usage,
)


def test_normalize_model_usage_supports_common_provider_shapes():
    usage = normalize_model_usage(
        provider="qwen",
        requested_model="qwen3.5-flash",
        resolved_model="qwen3.5-flash-2026-07-01",
        raw_usage={
            "input_tokens": 1200,
            "output_tokens": 300,
            "input_tokens_details": {
                "cached_tokens": 800,
                "cache_creation": 25,
            },
            "output_tokens_details": {
                "reasoning_tokens": 100,
                "accepted_prediction_tokens": 12,
            },
        },
        provider_cost="0.0089",
        provider_cost_currency="cny",
        provider_cost_source="provider",
        source="litellm",
    )

    assert usage.input_tokens == 1200
    assert usage.output_tokens == 300
    assert usage.total_tokens == 1500
    assert usage.cached_input_tokens == 800
    assert usage.cache_creation_input_tokens == 25
    assert usage.reasoning_tokens == 100
    assert usage.accepted_prediction_tokens == 12
    assert usage.provider_cost == Decimal("0.0089")
    assert usage.provider_cost_currency == "CNY"
    assert usage.provider_cost_source == "provider"
    assert usage.source == "litellm"


def test_usage_context_is_nested_and_restored():
    outer = UsageContext(operation_id="outer")
    inner = UsageContext(operation_id="inner")

    assert get_usage_context() is None
    with bind_usage_context(outer):
        assert get_usage_context() is outer
        with bind_usage_context(inner):
            assert get_usage_context() is inner
        assert get_usage_context() is outer
    assert get_usage_context() is None


@pytest.mark.asyncio
async def test_tracker_emits_json_ready_events_and_aggregates():
    sink = InMemoryUsageSink()
    context = UsageContext(operation_id="operation-1", feature="record.qa")

    with bind_usage_context(context), bind_usage_sinks(sink):
        first = UsageCallTracker(
            provider="openai",
            requested_model="gpt-4o-mini",
            call_type="chat.completion",
        )
        await first.succeed(
            raw_usage={"prompt_tokens": 10, "completion_tokens": 4},
            provider_cost=Decimal("0.02"),
            provider_cost_currency="USD",
            provider_cost_source="litellm",
            source="litellm",
        )

        second = UsageCallTracker(
            provider="openai",
            requested_model="gpt-4o-mini",
            call_type="chat.completion",
        )
        await second.fail(RuntimeError("no capacity"))

        third = UsageCallTracker(
            provider="openai",
            requested_model="gpt-4o-mini",
            call_type="chat.completion",
        )
        await third.fail(asyncio.CancelledError())

    aggregate = aggregate_usage_events(sink.events)
    assert aggregate.operation_id == "operation-1"
    assert aggregate.call_count == 3
    assert aggregate.succeeded_calls == 1
    assert aggregate.failed_calls == 1
    assert aggregate.cancelled_calls == 1
    assert aggregate.total_tokens == 14
    assert aggregate.provider_cost_by_currency == {"USD": Decimal("0.02")}
    assert aggregate.provider_costs_without_currency == ()
    assert (
        json.loads(json.dumps(sink.events[0].to_dict()))["usage"]["provider_cost"]
        == "0.02"
    )


@pytest.mark.asyncio
async def test_sink_failure_does_not_change_model_call_result(caplog):
    async def failing_sink(_event):
        raise RuntimeError("storage unavailable")

    with bind_usage_sinks(failing_sink):
        tracker = UsageCallTracker(
            provider="openai",
            requested_model="gpt-4o-mini",
            call_type="chat.completion",
        )
        event = await tracker.succeed(raw_usage={"total_tokens": 1})

    assert event is not None
    assert event.status == "succeeded"
    assert "Usage sink failed" in caplog.text


def test_aggregate_requires_operation_id_for_mixed_operations():
    # The guard prevents accidentally combining unrelated users or billable jobs.
    with pytest.raises(ValueError, match="operation_id is required"):
        aggregate_usage_events(
            [
                _event_for_operation("operation-1"),
                _event_for_operation("operation-2"),
            ]
        )


def test_aggregate_never_adds_different_or_unknown_currencies():
    aggregate = aggregate_usage_events(
        [
            _event_for_operation("operation-1", cost="0.10", currency="USD"),
            _event_for_operation("operation-1", cost="0.70", currency="CNY"),
            _event_for_operation("operation-1", cost="0.05"),
        ]
    )

    assert aggregate.provider_cost_by_currency == {
        "USD": Decimal("0.10"),
        "CNY": Decimal("0.70"),
    }
    assert aggregate.provider_costs_without_currency == (Decimal("0.05"),)


def test_aggregate_rejects_mixed_tenant_identity():
    first = _event_for_operation("operation-1", tenant_id="lab-1")
    second = _event_for_operation("operation-1", tenant_id="lab-2")

    with pytest.raises(ValueError, match="same tenant_id"):
        aggregate_usage_events([first, second])


def _event_for_operation(
    operation_id: str,
    *,
    cost: str | None = None,
    currency: str | None = None,
    tenant_id: str | None = None,
):
    from datetime import UTC, datetime

    from masterbrain.usage import ModelUsageEvent

    return ModelUsageEvent(
        context=UsageContext(operation_id=operation_id, tenant_id=tenant_id),
        call_type="chat.completion",
        status="succeeded",
        usage=normalize_model_usage(
            provider="openai",
            requested_model="gpt-4o-mini",
            raw_usage={"total_tokens": 1},
            provider_cost=cost,
            provider_cost_currency=currency,
        ),
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
        latency_ms=1,
    )
