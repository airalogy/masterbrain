"""Provider-neutral model usage contracts and delivery hooks.

LiteLLM and provider SDK objects are intentionally normalized at this boundary.
Downstream applications can persist :class:`ModelUsageEvent` without importing
or depending on a particular model SDK.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Protocol
from uuid import uuid4

UsageStatus = Literal["succeeded", "failed", "cancelled"]
UsageSource = Literal["provider", "litellm", "estimated", "unavailable"]

logger = logging.getLogger(__name__)


def _new_id() -> str:
    return str(uuid4())


def _non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return decimal_value if decimal_value.is_finite() and decimal_value >= 0 else None


def to_usage_mapping(value: Any) -> dict[str, Any]:
    """Convert SDK/Pydantic usage objects to a plain mapping without prompt data."""

    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(exclude_none=True)
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}

    dict_method = getattr(value, "dict", None)
    if callable(dict_method):
        dumped = dict_method()
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}

    raw = getattr(value, "__dict__", None)
    if isinstance(raw, Mapping):
        return {
            str(key): item for key, item in raw.items() if not str(key).startswith("_")
        }
    return {}


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _nested_mapping(raw: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = raw.get(key)
        mapped = to_usage_mapping(value)
        if mapped:
            return mapped
    return {}


@dataclass(frozen=True, slots=True)
class UsageContext:
    """Business identity attached to every upstream model call."""

    operation_id: str = field(default_factory=_new_id)
    request_id: str | None = None
    parent_operation_id: str | None = None
    feature: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    project_id: str | None = None
    chat_id: str | None = None
    attributes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.operation_id.strip():
            raise ValueError("operation_id must not be empty")
        object.__setattr__(self, "attributes", dict(self.attributes))


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """Normalized usage for one real provider call.

    The public shape is owned by Masterbrain. ``raw_usage`` preserves the
    provider/LiteLLM fields needed for later reconciliation without making them
    part of the stable billing contract.
    """

    provider: str
    requested_model: str
    resolved_model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    reasoning_tokens: int = 0
    audio_input_tokens: int = 0
    audio_output_tokens: int = 0
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0
    audio_seconds: Decimal | None = None
    provider_cost: Decimal | None = None
    provider_cost_currency: str | None = None
    provider_cost_source: str | None = None
    source: UsageSource = "unavailable"
    raw_usage: Mapping[str, Any] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if not self.requested_model.strip():
            raise ValueError("requested_model must not be empty")
        if not self.resolved_model.strip():
            object.__setattr__(self, "resolved_model", self.requested_model)

        token_fields = (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cached_input_tokens",
            "cache_creation_input_tokens",
            "reasoning_tokens",
            "audio_input_tokens",
            "audio_output_tokens",
            "accepted_prediction_tokens",
            "rejected_prediction_tokens",
        )
        for field_name in token_fields:
            object.__setattr__(
                self, field_name, _non_negative_int(getattr(self, field_name))
            )

        if self.total_tokens == 0 and (self.input_tokens or self.output_tokens):
            object.__setattr__(
                self, "total_tokens", self.input_tokens + self.output_tokens
            )
        object.__setattr__(self, "audio_seconds", _decimal_or_none(self.audio_seconds))
        normalized_cost = _decimal_or_none(self.provider_cost)
        object.__setattr__(self, "provider_cost", normalized_cost)
        if normalized_cost is None:
            object.__setattr__(self, "provider_cost_currency", None)
            object.__setattr__(self, "provider_cost_source", None)
        else:
            currency = str(self.provider_cost_currency or "").strip().upper() or None
            cost_source = str(self.provider_cost_source or "").strip() or None
            object.__setattr__(self, "provider_cost_currency", currency)
            object.__setattr__(self, "provider_cost_source", cost_source)
        object.__setattr__(self, "raw_usage", dict(self.raw_usage))

    @property
    def available(self) -> bool:
        return self.source != "unavailable"


def normalize_model_usage(
    *,
    provider: str,
    requested_model: str,
    resolved_model: str | None = None,
    raw_usage: Any = None,
    provider_cost: Any = None,
    provider_cost_currency: str | None = None,
    provider_cost_source: str | None = None,
    source: UsageSource = "provider",
) -> ModelUsage:
    """Normalize OpenAI/LiteLLM/LangChain/DashScope usage fields."""

    raw = to_usage_mapping(raw_usage)
    prompt_details = _nested_mapping(
        raw,
        "prompt_tokens_details",
        "input_tokens_details",
        "input_token_details",
    )
    completion_details = _nested_mapping(
        raw,
        "completion_tokens_details",
        "output_tokens_details",
        "output_token_details",
    )
    cache_details = _nested_mapping(raw, "cache", "cache_tokens_details")

    input_tokens = _non_negative_int(raw.get("prompt_tokens", raw.get("input_tokens")))
    output_tokens = _non_negative_int(
        raw.get("completion_tokens", raw.get("output_tokens"))
    )
    total_tokens = _non_negative_int(raw.get("total_tokens"))

    cached_input_tokens = _non_negative_int(
        raw.get(
            "cache_read_input_tokens",
            raw.get(
                "cached_input_tokens",
                prompt_details.get(
                    "cached_tokens",
                    prompt_details.get("cache_read", cache_details.get("read")),
                ),
            ),
        )
    )
    cache_creation_input_tokens = _non_negative_int(
        raw.get(
            "cache_creation_input_tokens",
            raw.get(
                "cache_write_input_tokens",
                prompt_details.get("cache_creation", cache_details.get("write")),
            ),
        )
    )
    reasoning_tokens = _non_negative_int(
        raw.get(
            "reasoning_tokens",
            raw.get(
                "thoughts_token_count",
                raw.get(
                    "reasoning",
                    completion_details.get(
                        "reasoning_tokens",
                        completion_details.get("reasoning"),
                    ),
                ),
            ),
        )
    )
    audio_input_tokens = _non_negative_int(
        raw.get("audio_input_tokens", prompt_details.get("audio_tokens"))
    )
    audio_output_tokens = _non_negative_int(
        raw.get("audio_output_tokens", completion_details.get("audio_tokens"))
    )

    normalized_source: UsageSource = (
        source if raw or provider_cost is not None else "unavailable"
    )
    return ModelUsage(
        provider=provider,
        requested_model=requested_model,
        resolved_model=resolved_model or requested_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
        reasoning_tokens=reasoning_tokens,
        audio_input_tokens=audio_input_tokens,
        audio_output_tokens=audio_output_tokens,
        accepted_prediction_tokens=_non_negative_int(
            completion_details.get("accepted_prediction_tokens")
        ),
        rejected_prediction_tokens=_non_negative_int(
            completion_details.get("rejected_prediction_tokens")
        ),
        audio_seconds=_decimal_or_none(
            raw.get("audio_seconds", raw.get("duration_seconds", raw.get("seconds")))
        ),
        provider_cost=_decimal_or_none(
            provider_cost
            if provider_cost is not None
            else raw.get("response_cost", raw.get("total_cost", raw.get("cost")))
        ),
        provider_cost_currency=(
            provider_cost_currency or raw.get("cost_currency") or raw.get("currency")
        ),
        provider_cost_source=(provider_cost_source or raw.get("cost_source")),
        source=normalized_source,
        raw_usage=raw,
    )


@dataclass(frozen=True, slots=True)
class ModelUsageEvent:
    """Auditable result of one provider request."""

    context: UsageContext
    call_type: str
    status: UsageStatus
    usage: ModelUsage
    started_at: datetime
    ended_at: datetime
    latency_ms: int
    event_id: str = field(default_factory=_new_id)
    call_id: str = field(default_factory=_new_id)
    provider_request_id: str | None = None
    error_type: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "latency_ms", max(int(self.latency_ms), 0))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def operation_id(self) -> str:
        return self.context.operation_id

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation suitable for Platform storage."""

        value = asdict(self)
        value["started_at"] = self.started_at.isoformat()
        value["ended_at"] = self.ended_at.isoformat()
        usage = value["usage"]
        for key in ("audio_seconds", "provider_cost"):
            if usage[key] is not None:
                usage[key] = str(usage[key])
        return _json_value(value)


class UsageSink(Protocol):
    """Application-owned destination for immutable usage events."""

    async def record_usage(self, event: ModelUsageEvent) -> None: ...


UsageSinkCallable = Callable[[ModelUsageEvent], Any]
UsageSinkLike = UsageSink | UsageSinkCallable

_current_usage_context: ContextVar[UsageContext | None] = ContextVar(
    "masterbrain_usage_context",
    default=None,
)
_usage_sink_override: ContextVar[tuple[UsageSinkLike, ...] | None] = ContextVar(
    "masterbrain_usage_sinks",
    default=None,
)
_default_usage_sinks: tuple[UsageSinkLike, ...] = ()


def get_usage_context() -> UsageContext | None:
    return _current_usage_context.get()


def capture_usage_context(*, feature: str | None = None) -> UsageContext:
    context = get_usage_context()
    if context is not None:
        return context
    return UsageContext(feature=feature)


@contextmanager
def bind_usage_context(
    context: UsageContext | None = None,
    **context_values: Any,
) -> Iterator[UsageContext]:
    """Bind an operation context across nested async model calls."""

    if context is not None and context_values:
        raise ValueError("Pass either a UsageContext or keyword values, not both")
    bound = context or UsageContext(**context_values)
    token = _current_usage_context.set(bound)
    try:
        yield bound
    finally:
        _current_usage_context.reset(token)


def configure_usage_sinks(*sinks: UsageSinkLike) -> None:
    """Set process-wide sinks during application startup."""

    global _default_usage_sinks
    _default_usage_sinks = tuple(sinks)


@contextmanager
def bind_usage_sinks(*sinks: UsageSinkLike) -> Iterator[None]:
    """Temporarily override sinks, primarily for tests and embedded callers."""

    token = _usage_sink_override.set(tuple(sinks))
    try:
        yield
    finally:
        _usage_sink_override.reset(token)


async def emit_usage_event(event: ModelUsageEvent) -> None:
    """Deliver an event without allowing observability failures to break AI calls."""

    sinks = _usage_sink_override.get()
    if sinks is None:
        sinks = _default_usage_sinks
    await _deliver_usage_event(event, sinks)


async def _deliver_usage_event(
    event: ModelUsageEvent,
    sinks: tuple[UsageSinkLike, ...],
) -> None:
    for sink in sinks:
        try:
            handler = getattr(sink, "record_usage", None)
            result = handler(event) if callable(handler) else sink(event)  # type: ignore[misc]
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("Usage sink failed for event %s", event.event_id)


class InMemoryUsageSink:
    """Simple sink for tests, local tools, and integration prototypes."""

    def __init__(self) -> None:
        self.events: list[ModelUsageEvent] = []

    async def record_usage(self, event: ModelUsageEvent) -> None:
        self.events.append(event)


@dataclass(frozen=True, slots=True)
class OperationUsage:
    operation_id: str
    tenant_id: str | None
    user_id: str | None
    project_id: str | None
    chat_id: str | None
    call_count: int
    succeeded_calls: int
    failed_calls: int
    cancelled_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_input_tokens: int
    cache_creation_input_tokens: int
    reasoning_tokens: int
    audio_input_tokens: int
    audio_output_tokens: int
    accepted_prediction_tokens: int
    rejected_prediction_tokens: int
    audio_seconds: Decimal | None
    provider_cost_by_currency: Mapping[str, Decimal]
    provider_costs_without_currency: tuple[Decimal, ...]


def aggregate_usage_events(
    events: Sequence[ModelUsageEvent],
    *,
    operation_id: str | None = None,
) -> OperationUsage:
    """Aggregate call events while retaining each event for model-specific pricing."""

    selected = [
        event
        for event in events
        if operation_id is None or event.operation_id == operation_id
    ]
    if operation_id is None:
        operation_ids = {event.operation_id for event in selected}
        if len(operation_ids) > 1:
            raise ValueError(
                "operation_id is required when events contain multiple operations"
            )
        resolved_operation_id = next(iter(operation_ids), "")
    else:
        resolved_operation_id = operation_id

    def context_value(field_name: str) -> str | None:
        values = {getattr(event.context, field_name) for event in selected}
        if len(values) > 1:
            raise ValueError(
                f"events in one operation must share the same {field_name}"
            )
        return next(iter(values), None)

    costs_by_currency: dict[str, Decimal] = {}
    costs_without_currency = [
        event.usage.provider_cost
        for event in selected
        if event.usage.provider_cost is not None
        and event.usage.provider_cost_currency is None
    ]
    for event in selected:
        cost = event.usage.provider_cost
        currency = event.usage.provider_cost_currency
        if cost is None or currency is None:
            continue
        costs_by_currency[currency] = (
            costs_by_currency.get(currency, Decimal("0")) + cost
        )
    audio_seconds = [
        event.usage.audio_seconds
        for event in selected
        if event.usage.audio_seconds is not None
    ]
    return OperationUsage(
        operation_id=resolved_operation_id,
        tenant_id=context_value("tenant_id"),
        user_id=context_value("user_id"),
        project_id=context_value("project_id"),
        chat_id=context_value("chat_id"),
        call_count=len(selected),
        succeeded_calls=sum(event.status == "succeeded" for event in selected),
        failed_calls=sum(event.status == "failed" for event in selected),
        cancelled_calls=sum(event.status == "cancelled" for event in selected),
        input_tokens=sum(event.usage.input_tokens for event in selected),
        output_tokens=sum(event.usage.output_tokens for event in selected),
        total_tokens=sum(event.usage.total_tokens for event in selected),
        cached_input_tokens=sum(event.usage.cached_input_tokens for event in selected),
        cache_creation_input_tokens=sum(
            event.usage.cache_creation_input_tokens for event in selected
        ),
        reasoning_tokens=sum(event.usage.reasoning_tokens for event in selected),
        audio_input_tokens=sum(event.usage.audio_input_tokens for event in selected),
        audio_output_tokens=sum(event.usage.audio_output_tokens for event in selected),
        accepted_prediction_tokens=sum(
            event.usage.accepted_prediction_tokens for event in selected
        ),
        rejected_prediction_tokens=sum(
            event.usage.rejected_prediction_tokens for event in selected
        ),
        audio_seconds=(sum(audio_seconds, Decimal("0")) if audio_seconds else None),
        provider_cost_by_currency=costs_by_currency,
        provider_costs_without_currency=tuple(costs_without_currency),
    )


class UsageCallTracker:
    """Lifecycle helper shared by LiteLLM and external runtimes."""

    def __init__(
        self,
        *,
        provider: str,
        requested_model: str,
        call_type: str,
        context: UsageContext | None = None,
        call_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.provider = provider
        self.requested_model = requested_model
        self.call_type = call_type
        self.context = context or capture_usage_context(feature=call_type)
        self.call_id = call_id or _new_id()
        self.metadata = dict(metadata or {})
        self.started_at = datetime.now(UTC)
        self._started_clock = time.perf_counter()
        self._finished = False
        self._sink_override = _usage_sink_override.get()

    @property
    def finished(self) -> bool:
        return self._finished

    async def finish(
        self,
        *,
        status: UsageStatus,
        resolved_model: str | None = None,
        raw_usage: Any = None,
        provider_cost: Any = None,
        provider_cost_currency: str | None = None,
        provider_cost_source: str | None = None,
        source: UsageSource = "provider",
        provider_request_id: str | None = None,
        error_type: str | None = None,
    ) -> ModelUsageEvent | None:
        if self._finished:
            return None
        self._finished = True
        ended_at = datetime.now(UTC)
        event = ModelUsageEvent(
            context=self.context,
            call_type=self.call_type,
            status=status,
            usage=normalize_model_usage(
                provider=self.provider,
                requested_model=self.requested_model,
                resolved_model=resolved_model,
                raw_usage=raw_usage,
                provider_cost=provider_cost,
                provider_cost_currency=provider_cost_currency,
                provider_cost_source=provider_cost_source,
                source=source,
            ),
            started_at=self.started_at,
            ended_at=ended_at,
            latency_ms=round((time.perf_counter() - self._started_clock) * 1000),
            call_id=self.call_id,
            provider_request_id=provider_request_id,
            error_type=error_type,
            metadata=self.metadata,
        )
        if self._sink_override is None:
            await emit_usage_event(event)
        else:
            await _deliver_usage_event(event, self._sink_override)
        return event

    async def succeed(self, **values: Any) -> ModelUsageEvent | None:
        return await self.finish(status="succeeded", **values)

    async def fail(self, exc: BaseException) -> ModelUsageEvent | None:
        return await self.finish(
            status="cancelled" if isinstance(exc, asyncio.CancelledError) else "failed",
            source="unavailable",
            error_type=exc.__class__.__name__,
        )
