import asyncio
import re
import time

from langchain.prompts import PromptTemplate

from masterbrain.configs import select_client
from masterbrain.endpoints.protocol_generation.aimd.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
    USER_MESSAGE_PROTOCOL_AIMD_HEAD_TEMPLATE,
    USER_MESSAGE_PROTOCOL_AIMD_TAIL_TEMPLATE,
)
from masterbrain.endpoints.protocol_generation.aimd.types import AimdProtocolMessage


async def generate_stream(protocol_msg: AimdProtocolMessage, history: list):
    start_time = time.time()

    # Prepare user prompt
    prompt = USER_MESSAGE_PROTOCOL_AIMD_HEAD_TEMPLATE + PromptTemplate(
        input_variables=["USER_MESSAGE_REF_PROTOCOL"],
        template=USER_MESSAGE_PROTOCOL_AIMD_TAIL_TEMPLATE,
    ).format(USER_MESSAGE_REF_PROTOCOL=protocol_msg.instruction)

    history.append({"role": "user", "content": prompt})

    client = select_client(protocol_msg.use_model.name)
    response = await client.chat.completions.create(
        messages=history,
        model=protocol_msg.use_model.name,
        stream=True,
        timeout=1800,
    )

    buffer = ""
    # Track if we've started content collection (after start marker)
    content_started = False
    # Track if we've received the end marker
    content_ended = False
    # Whether we bypassed marker detection (no ```aimd wrapper)
    bypass_mode = False
    # For collecting content
    pending_buffer = ""
    # Count how many tokens have been received without finding start marker
    no_marker_count = 0
    # Maximum tokens to wait before bypassing marker requirement
    max_tokens_wait = 8
    # Track nested code fence depth (for marker mode only)
    fence_depth = 0

    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            pending_buffer += content

            # If we've received too many tokens without finding a start marker,
            # assume the model is not using markers and start streaming all content
            if not content_started:
                no_marker_count += 1
                if no_marker_count >= max_tokens_wait:
                    content_started = True
                    bypass_mode = True
                    # Start streaming what we've already collected
                    yield pending_buffer
                    buffer += pending_buffer
                    pending_buffer = ""
                    continue

            # Process the pending buffer for markers
            filtered_content = ""

            # Look for start marker first
            if not content_started and "```aimd\n" in pending_buffer:
                # Remove everything up to and including the start marker
                parts = pending_buffer.split("```aimd\n", 1)
                pending_buffer = parts[1] if len(parts) > 1 else ""
                content_started = True
                fence_depth = 1

            # Check for end marker only in marker mode (not bypass mode)
            # In bypass mode, stream everything until the model finishes
            if content_started and not content_ended and not bypass_mode:
                # Track nested code fences to find the matching outer closing ```
                # Opening fences: ```identifier (assigner, quiz, fig, python, etc.)
                for m in re.finditer(r"```\w+", pending_buffer):
                    fence_depth += 1
                # Closing fences: bare ``` (not followed by word char)
                for m in re.finditer(r"```(?!\w)", pending_buffer):
                    fence_depth -= 1
                    if fence_depth <= 0:
                        # Found the matching outer closing ```
                        pending_buffer = pending_buffer[: m.start()]
                        content_ended = True
                        break

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

    # Handle any remaining content in the pending buffer
    # Even if we haven't started content collection based on markers,
    # send the accumulated content if there's anything
    if pending_buffer:
        yield pending_buffer
        buffer += pending_buffer

    end_time = time.time()
    print(f"Protocol.aimd Generation Total Time: {end_time - start_time:.6f} s")
