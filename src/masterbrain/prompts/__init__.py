"""
In this module every different-purposed prompt is stored in a separate file. Then all the prompts are loaded in the __init__.py file of the module.
"""

from typing import Literal, get_args

from masterbrain.prompts.system_message_masterbrain import SYSTEM_MESSAGE_MASTERBRAIN

__all__ = [
    "SYSTEM_MESSAGE_MASTERBRAIN",
    "AvailableSystemMessageNames",
    "AVAILABLE_SYSTEM_MESSAGES",
]


AvailableSystemMessageNames = Literal["masterbrain"]
DEFAULT_SYSTEM_MESSAGE_NAME = "masterbrain"

AVAILABLE_SYSTEM_MESSAGES = {
    "masterbrain": SYSTEM_MESSAGE_MASTERBRAIN,
}

assert set(AVAILABLE_SYSTEM_MESSAGES.keys()) == set(
    get_args(AvailableSystemMessageNames)
)
