from .chat.field_input.router import field_input_router
from .chat.qa.language.router import chat_qa_language_router
from .chat.qa.stt.router import chat_qa_stt_router
from .chat.qa.vision.router import chat_qa_vision_router
from .paper_generation.router import paper_generation_router
from .protocol_check.router import protocol_check_router
from .protocol_debug.router import protocol_debug_router
from .protocol_generation.aimd.router import protocol_generation_aimd_router
from .protocol_generation.assigner.router import protocol_generation_assigner_router
from .protocol_generation.model.router import protocol_generation_model_router
from .single_protocol_file_generation import single_protocol_file_generation_router

__all__ = [
    "chat_qa_language_router",
    "chat_qa_stt_router",
    "chat_qa_vision_router",
    "field_input_router",
    "protocol_generation_aimd_router",
    "protocol_generation_assigner_router",
    "protocol_generation_model_router",
    "single_protocol_file_generation_router",
    "protocol_check_router",
    "protocol_debug_router",
    "paper_generation_router",
]
"""
This module (dir) is used to manage the codes related to the endpoints of the API.
Each sub-module (sub-dir) corresponds to a specific endpoint.
"""
