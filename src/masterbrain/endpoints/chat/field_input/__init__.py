"""
Field Input Endpoint

This module provides automatic slot filling functionality for experimental data.
"""

from .router import field_input_router
from .types import (
    FieldInputRequest,
    FieldInputResponse, 
    SlotOperation,
    SlotUpdateResult,
    SupportedModels,
)

__all__ = [
    "field_input_router",
    "FieldInputRequest",
    "FieldInputResponse",
    "SlotOperation", 
    "SlotUpdateResult",
    "SupportedModels",
]
