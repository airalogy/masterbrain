__all__ = ["single_protocol_file_generation_router"]

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from masterbrain.endpoints.single_protocol_file_generation.logic import generate_stream
from masterbrain.endpoints.single_protocol_file_generation.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
)
from masterbrain.types.error import LlmError
from masterbrain.utils.llm import ensure_model_api_key, preflight_text_stream

from .types import ProtocolMessage

single_protocol_file_generation_router = APIRouter()


@single_protocol_file_generation_router.post(
    "/single_protocol_file_generation",
    summary="Single Protocol File",
    responses={
        200: {"description": "Success", "model": ProtocolMessage},
        400: {"description": "Bad Request", "model": LlmError},
    },
)
async def generate_protocol(protocol_msg: ProtocolMessage):
    history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]
    ensure_model_api_key(protocol_msg.use_model.name)
    stream = await preflight_text_stream(
        generate_stream(protocol_msg, history),
        model_name=protocol_msg.use_model.name,
    )

    return StreamingResponse(stream, media_type="text/plain")
