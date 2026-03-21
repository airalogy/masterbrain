__all__ = ["generate_debug_result"]

import json
import time
from typing import cast, List

from langchain.prompts import PromptTemplate
from openai.types.chat import ChatCompletionMessageParam

from masterbrain.configs import select_client
from masterbrain.endpoints.protocol_debug.logic.prompts import (
    AIMD_SYNTAX,
    SYSTEM_MESSAGE_PROTOCOL_DEBUG_PROMPT,
    USER_MESSAGE_PROTOCOL_DEBUG_TEMPLATE,
)
from masterbrain.endpoints.protocol_debug.types import ProtocolDebugInput, ProtocolDebugOutput

# JSON Schema to enforce structured output from LLM
RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "has_errors": {
            "type": "boolean",
            "description": "Whether syntax errors were found in the suspect segment",
        },
        "fixed_segment": {
            "type": "string",
            "description": "The fixed segment content. Empty string if no errors.",
        },
        "reason": {
            "type": "string",
            "description": "Explanation of each fix, or a note that no errors were found.",
        },
    },
    "required": ["has_errors", "fixed_segment", "reason"],
    "additionalProperties": False,
}


async def generate_debug_result(protocol_debug_input: ProtocolDebugInput) -> ProtocolDebugOutput:
    """Generate debug result for protocol debug"""
    start_time = time.time()

    full_protocol = protocol_debug_input.full_protocol
    suspect_protocol = protocol_debug_input.suspect_protocol

    if not suspect_protocol:
        return ProtocolDebugOutput(
            has_errors=False, fixed_protocol="", response="The part to be checked is empty."
        )

    # Build user prompt
    user_prompt = PromptTemplate(
        input_variables=["AIMD_SYNTAX", "FULL_PROTOCOL", "SUSPECT_PROTOCOL"],
        template=USER_MESSAGE_PROTOCOL_DEBUG_TEMPLATE,
    ).format(
        AIMD_SYNTAX=AIMD_SYNTAX,
        FULL_PROTOCOL=full_protocol,
        SUSPECT_PROTOCOL=suspect_protocol,
    )

    conversation_history = [
        {"role": "system", "content": SYSTEM_MESSAGE_PROTOCOL_DEBUG_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    client = select_client(protocol_debug_input.model.name)
    response = await client.chat.completions.create(
        messages=cast(List[ChatCompletionMessageParam], conversation_history),
        model=protocol_debug_input.model.name,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "protocol_debug_result",
                "strict": True,
                "schema": RESPONSE_JSON_SCHEMA,
            },
        },
        timeout=1800,
        extra_body={
            "enable_thinking": protocol_debug_input.model.enable_thinking,
            "enable_search": protocol_debug_input.model.enable_search,
        },
    )

    # Parse response
    raw = response.choices[0].message.content or ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ProtocolDebugOutput(
            has_errors=False, fixed_protocol="", response=f"Failed to parse LLM response: {raw[:200]}"
        )

    has_errors = bool(data.get("has_errors", False))
    fixed_segment = data.get("fixed_segment", "") if has_errors else ""
    reason = data.get("reason", "")

    # Normalize reason to string
    if isinstance(reason, list):
        parts = []
        for item in reason:
            if isinstance(item, dict):
                parts.append("; ".join(f"{k}: {v}" for k, v in item.items()))
            else:
                parts.append(str(item))
        reason = "\n".join(parts)
    elif not isinstance(reason, str):
        reason = str(reason)

    end_time = time.time()
    print(f"Protocol Debug Total Time: {end_time - start_time:.6f} s")

    return ProtocolDebugOutput(
        has_errors=has_errors, fixed_protocol=fixed_segment, response=reason
    )
