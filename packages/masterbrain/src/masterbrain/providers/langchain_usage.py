"""LangChain callback bridge into Masterbrain's provider-neutral usage events."""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler

from masterbrain.usage import UsageCallTracker, to_usage_mapping


def _merge_usage(target: dict[str, Any], value: Any) -> None:
    for key, item in to_usage_mapping(value).items():
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            target[key] = target.get(key, 0) + item
            continue
        nested = to_usage_mapping(item)
        if nested:
            existing = target.setdefault(key, {})
            if isinstance(existing, dict):
                _merge_usage(existing, nested)
        elif key not in target:
            target[key] = item


def _langchain_result_values(
    response: Any,
) -> tuple[dict[str, Any], str | None, Any, str | None, str | None]:
    llm_output = to_usage_mapping(getattr(response, "llm_output", None))
    usage = to_usage_mapping(llm_output.get("token_usage") or llm_output.get("usage"))
    resolved_model = llm_output.get("model_name") or llm_output.get("model")
    provider_cost = (
        llm_output.get("response_cost")
        or llm_output.get("total_cost")
        or llm_output.get("cost")
    )
    provider_cost_currency = llm_output.get("cost_currency") or llm_output.get(
        "currency"
    )
    provider_request_id = llm_output.get("id") or llm_output.get("request_id")

    merged_usage: dict[str, Any] = {}
    for generation_group in getattr(response, "generations", None) or []:
        for generation in generation_group:
            message = getattr(generation, "message", None)
            if message is None:
                continue
            if not usage:
                _merge_usage(merged_usage, getattr(message, "usage_metadata", None))
            response_metadata = to_usage_mapping(
                getattr(message, "response_metadata", None)
            )
            if not usage and not merged_usage:
                _merge_usage(
                    merged_usage,
                    response_metadata.get("token_usage")
                    or response_metadata.get("usage"),
                )
            resolved_model = (
                resolved_model
                or response_metadata.get("model_name")
                or response_metadata.get("model")
            )
            provider_cost = (
                provider_cost
                or response_metadata.get("response_cost")
                or response_metadata.get("total_cost")
                or response_metadata.get("cost")
            )
            provider_cost_currency = (
                provider_cost_currency
                or response_metadata.get("cost_currency")
                or response_metadata.get("currency")
            )
            provider_request_id = (
                provider_request_id
                or getattr(message, "id", None)
                or response_metadata.get("id")
                or response_metadata.get("request_id")
            )
    return (
        usage or merged_usage,
        resolved_model,
        provider_cost,
        provider_cost_currency,
        provider_request_id,
    )


class MasterbrainLangChainUsageCallback(AsyncCallbackHandler):
    """Record every underlying LangChain model run as one immutable event."""

    def __init__(self, *, provider: str, requested_model: str) -> None:
        self.provider = provider
        self.requested_model = requested_model
        self._trackers: dict[str, UsageCallTracker] = {}

    def _start(self, run_id: Any) -> None:
        key = str(run_id)
        self._trackers.setdefault(
            key,
            UsageCallTracker(
                provider=self.provider,
                requested_model=self.requested_model,
                call_type="chat.completion",
                call_id=key,
                metadata={"runtime": "langchain"},
            ),
        )

    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        del serialized, prompts, kwargs
        self._start(run_id)

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        del serialized, messages, kwargs
        self._start(run_id)

    async def on_llm_end(self, response: Any, *, run_id: Any, **kwargs: Any) -> None:
        del kwargs
        key = str(run_id)
        tracker = self._trackers.pop(key, None)
        if tracker is None:
            self._start(run_id)
            tracker = self._trackers.pop(key)
        (
            usage,
            resolved_model,
            provider_cost,
            provider_cost_currency,
            provider_request_id,
        ) = _langchain_result_values(response)
        await tracker.succeed(
            resolved_model=resolved_model,
            raw_usage=usage,
            provider_cost=provider_cost,
            provider_cost_currency=provider_cost_currency,
            source="provider",
            provider_cost_source="langchain",
            provider_request_id=provider_request_id,
        )

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        del kwargs
        key = str(run_id)
        tracker = self._trackers.pop(key, None)
        if tracker is None:
            self._start(run_id)
            tracker = self._trackers.pop(key)
        await tracker.fail(error)


__all__ = ["MasterbrainLangChainUsageCallback"]
