"""
The data model for the chat.
"""

from datetime import datetime

from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, field_validator, model_validator

from masterbrain.prompts import DEFAULT_SYSTEM_MESSAGE_NAME, AvailableSystemMessageNames
from masterbrain.types.model import Model

__all__ = [
    "HumanFeedback",
    "ChatDoc",
]


type ChatCompletionUATMessageParam = (
    ChatCompletionUserMessageParam
    | ChatCompletionAssistantMessageParam
    | ChatCompletionToolMessageParam
)
"""
The union of the user, assistant, and tool message parameters.
"""

type ChatCompletionATMessageParam = (
    ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam
)
"""
The union of the assistant and tool message parameters.
"""


class HumanFeedback(BaseModel):
    """
    The data model for human feedback.
    """

    score: int = 0
    """
    upvote: 1; downvote: -1; no feedback (default): 0
    """
    additional: str = ""


class ChatDoc(BaseModel):
    """
    The data model for the chat.
    """

    chat_id: str = ""
    user_id: str = ""
    start_time: datetime = datetime.now()
    end_time: datetime = datetime.now()
    active: bool = True
    """
    If false, the chat is not available for continuing.
    """
    deleted: bool = False
    """
    When user delete the chat in the frontend, this value is set to true.
    """
    title: str = ""

    model: Model = Model()
    system_message_name: AvailableSystemMessageNames = DEFAULT_SYSTEM_MESSAGE_NAME
    function_names: list[str] = []
    """
    Because the definition of a function also requires the ChatDoc model, thus we can't use the AvailableFunctionNames directly. Instead, we use the string representation of the function name. This will solve the circular import issue.
    """

    scenario: dict = {}
    """
    The `scenario` is a dictionary that contains the information about the scenario-related data. The scenario-related data can be used during the chat session to support the generation of the assistant's response.
    """
    scenario_messages: list[ChatCompletionUATMessageParam] = []
    main_messages: list[ChatCompletionUATMessageParam] = [
        {
            "role": "user",
            "content": "Hello, world!",
        }
    ]
    """
    The system message is required for the model to generate the response. However, it should not be exposed to the frontend user. Because if the user can get the specific content of the system_message. It may launch a dialogue attack targeting. Therefore, we only include the messages without system message in the chat doc.
    """
    human_feedback: list[HumanFeedback] = [HumanFeedback()]
    """
    The length of human_feedback should be the same as the length of main_messages. The human_feedback is used to organize the user's feedback on the assistant's response. The user can like or dislike the assistant's response. Further, we can use the feedback to improve the assistant's response.
    """

    @field_validator("main_messages")
    @classmethod
    def validate_main_messages(
        cls, v: list[ChatCompletionUATMessageParam]
    ) -> list[ChatCompletionUATMessageParam]:
        """
        Validate that main_messages has at least 1 message. Reason: The first message is the user's message.
        """
        assert len(v) > 0, "main_messages should have at least 1 message"
        return v

    @model_validator(mode="after")
    def validate_len_human_feedback(self):
        """
        Validate that the length of human_feedback is the same as the length of main_messages.
        """
        assert len(self.human_feedback) == len(self.main_messages), (
            "len human_feedback != len main_messages"
        )
        return self
