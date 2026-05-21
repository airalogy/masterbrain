"""
This module loads the system message from the template file and injects the current date to the prompt.
"""

import os
from datetime import date

from langchain_core.prompts import PromptTemplate


__all__ = [
    "SYSTEM_MESSAGE_MASTERBRAIN",
]

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_MESSAGE_MASTERBRAIN_TEMPLATE_FILE_PATH = os.path.join(
    CURRENT_DIR, "masterbrain.md"
)
with open(SYSTEM_MESSAGE_MASTERBRAIN_TEMPLATE_FILE_PATH, "r", encoding="utf-8") as file:
    SYSTEM_MESSAGE_TEMPLATE = file.read()

# inject current date to prompt
current_date = date.today().isoformat()

SYSTEM_MESSAGE_MASTERBRAIN = PromptTemplate.from_template(
    SYSTEM_MESSAGE_TEMPLATE
).format(current_date=current_date)

# TODO: Use scheduled tasks to update system messages daily
