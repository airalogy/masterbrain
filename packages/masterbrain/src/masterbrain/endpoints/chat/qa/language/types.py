from typing import Literal

from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel


class SupportedModels(BaseModel):
    name: Literal["qwen3.5-flash", "qwen3.5-plus", "qwen3-max"]
    enable_thinking: bool = False
    enable_search: bool = False


DEFAULT_MODEL = SupportedModels(
    name="qwen3.5-flash",
    enable_thinking=False,
    enable_search=False,
)


class ChatInput(BaseModel):
    model: SupportedModels = DEFAULT_MODEL
    messages: list[
        ChatCompletionAssistantMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionToolMessageParam
    ]
