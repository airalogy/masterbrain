__all__ = ["generate_stream"]

import asyncio
import time

from langchain.prompts import PromptTemplate

from masterbrain.configs import select_client
from masterbrain.endpoints.protocol_check.logic.prompts import (
    SYSTEM_MESSAGE_PROTOCOL_CHECK_PROMPT,
    USER_MESSAGE_PROTOCOL_CHECK_TEMPLATE_HEAD,
    USER_MESSAGE_PROTOCOL_CHECK_TEMPLATE_TAIL,
)
from masterbrain.endpoints.protocol_check.types import ProtocolCheckInput


async def generate_stream(protocol_check_input: ProtocolCheckInput):
    """Generate streaming response for protocol check"""
    start_time = time.time()

    # Build message history
    history = [{"role": "system", "content": SYSTEM_MESSAGE_PROTOCOL_CHECK_PROMPT}]

    # Determine target file type based on provided files
    target_file = determine_target_file(protocol_check_input)
    protocol_check_input.target_file = target_file

    # Prepare template parameters
    template_params = {
        "aimd_protocol": protocol_check_input.aimd_protocol or "",
        "py_model": protocol_check_input.py_model or "",
        "py_assigner": protocol_check_input.py_assigner or "",
        "feedback": protocol_check_input.feedback or "",
    }

    # Build user prompt
    prompt = PromptTemplate(
        input_variables=list(template_params.keys()),
        template=USER_MESSAGE_PROTOCOL_CHECK_TEMPLATE_HEAD,
    ).format(**template_params)
    prompt += USER_MESSAGE_PROTOCOL_CHECK_TEMPLATE_TAIL

    history.append({"role": "user", "content": prompt})

    # Select client
    client = select_client(protocol_check_input.model.name)

    # Create streaming response
    response = await client.chat.completions.create(
        messages=history,
        model=protocol_check_input.model.name,
        stream=True,
        timeout=1800,
        extra_body={
            "enable_thinking": protocol_check_input.model.enable_thinking,
            "enable_search": protocol_check_input.model.enable_search,
        },
    )

    buffer = ""
    content_started = False
    content_ended = False
    pending_buffer = ""
    no_marker_count = 0
    max_tokens_wait = 10

    # Determine start marker based on file type
    start_markers = ["```python\n", "```aimd\n"]
    start_marker = start_markers[1] if target_file == "protocol" else start_markers[0]

    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            pending_buffer += content

            # If too many tokens received without finding start marker, assume model doesn't use markers and start streaming all content
            if not content_started:
                no_marker_count += 1
                if no_marker_count >= max_tokens_wait:
                    content_started = True
                    yield pending_buffer
                    buffer += pending_buffer
                    pending_buffer = ""
                    continue

            # Process markers in pending buffer
            filtered_content = ""

            # Look for start marker first
            if not content_started and start_marker in pending_buffer:
                parts = pending_buffer.split(start_marker, 1)
                pending_buffer = parts[1] if len(parts) > 1 else ""
                content_started = True

            # If we've started content collection, check for end marker (```)
            if content_started and not content_ended and "```" in pending_buffer:
                parts = pending_buffer.split("```", 1)
                pending_buffer = parts[0]
                content_ended = True

            # If we've started content collection
            if content_started:
                filtered_content = pending_buffer
                pending_buffer = ""
                buffer += filtered_content
                yield filtered_content

                # If we've reached the end marker, stop processing further content
                if content_ended:
                    break

            await asyncio.sleep(0)

    # Handle any remaining content in pending buffer
    if pending_buffer:
        yield pending_buffer
        buffer += pending_buffer

    end_time = time.time()
    print(f"Protocol Check Total Time: {end_time - start_time:.6f} s")


def determine_target_file(protocol_check_input: ProtocolCheckInput) -> str:
    """Determine target file type based on provided files"""
    if protocol_check_input.py_assigner:
        return "assigner"
    elif protocol_check_input.py_model:
        return "model"
    else:
        return "protocol"
