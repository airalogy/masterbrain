__all__ = ["generate_stream"]

import asyncio
import time
from datetime import datetime
from pathlib import Path
from string import Template
from typing import cast

from openai.types.chat import ChatCompletionToolParam
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)

from masterbrain.configs import DASHSCOPE_CLIENT, DEBUG
from masterbrain.endpoints.chat.qa.language.types import ChatInput
from masterbrain.utils.print import print_with_border

PROMPT_PATH = Path(__file__).parent / "prompt.md"
PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


TOOLS = cast(
    list[ChatCompletionToolParam],
    [
        {
            "type": "function",
            "function": {
                "name": "inject_airalogy_protocols",
                "description": "Inject Airalogy Protocols based on provided Protocol IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "airalogy_protocol_ids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        }
                    },
                    "required": ["airalogy_protocol_ids"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inject_airalogy_records",
                "description": "Inject Airalogy Records based on provided Record IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "airalogy_record_ids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        }
                    },
                    "required": ["airalogy_record_ids"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inject_airalogy_discussions",
                "description": "Inject Airalogy Discussions based on provided Discussion IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "airalogy_discussion_ids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        }
                    },
                    "required": ["airalogy_discussion_ids"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    ],
)


async def generate_stream(
    chat_input: ChatInput,
    debug: bool = DEBUG,
):
    start_time = time.time()
    system_prompt = Template(PROMPT_TEMPLATE).substitute(
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S %a"),
    )

    if debug:
        print_with_border(f"System Prompt:\n{system_prompt}")

    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(
            {
                "role": "system",
                "content": system_prompt,
            }
        )
    ]
    messages.extend(chat_input.messages)

    completion = await DASHSCOPE_CLIENT.chat.completions.create(
        messages=messages,
        model=chat_input.model.name,
        tools=TOOLS,
        tool_choice="none",
        stream=True,
        extra_body={
            "enable_thinking": chat_input.model.enable_thinking,
            "enable_search": chat_input.model.enable_search,
        },
    )

    content = ""

    think_opened = False
    think_closed = False

    async for chunk in completion:
        if chunk.choices:
            delta = chunk.choices[0].delta

            if debug:
                print(f"Delta: {delta}")

            # Stream reasoning content wrapped in <think> ... </think>
            if (
                hasattr(delta, "reasoning_content")
                and delta.reasoning_content is not None  # type: ignore
            ):
                rc = delta.reasoning_content  # type: ignore
                if not think_opened:
                    yield "<think>\n"
                    content += "<think>\n"
                    think_opened = True
                content += rc
                yield rc

            # When answer content starts, close think if it was opened
            if hasattr(delta, "content") and delta.content:
                c = delta.content
                if think_opened and not think_closed:
                    yield "\n</think>\n"
                    content += "\n</think>\n"
                    think_closed = True
                content += c
                yield c

            await asyncio.sleep(0)
            
    # Close dangling </think> if stream ended during reasoning phase
    if think_opened and not think_closed:
        yield "\n</think>"
        content += "\n</think>"

    end_time = time.time()
    time_taken = end_time - start_time

    if debug:
        print_with_border(
            f"""
            Full streamed output:
            {content}
            {"#" * 80}
            Time taken: {time_taken:.6f} s
            """.strip()
        )
