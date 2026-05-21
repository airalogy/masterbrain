__all__ = ["protocol_generation_aimd_router"]

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from masterbrain.endpoints.protocol_generation.aimd.logic import generate_stream
from masterbrain.endpoints.protocol_generation.aimd.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
)
from masterbrain.types.error import LlmError
from masterbrain.utils.llm import ensure_model_api_key, preflight_text_stream

from .types import AimdProtocolMessage

protocol_generation_aimd_router = APIRouter()


@protocol_generation_aimd_router.post(
    "/protocol_generation/aimd",
    summary="STEP1: Protocol AIMD Generation",
    responses={
        200: {"description": "Success", "model": AimdProtocolMessage},
        400: {"description": "Bad Request", "model": LlmError},
    },
)
async def generate_protocol_aimd(protocol_msg: AimdProtocolMessage):
    history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]
    ensure_model_api_key(protocol_msg.use_model.name)
    stream = await preflight_text_stream(
        generate_stream(protocol_msg, history),
        model_name=protocol_msg.use_model.name,
    )

    return StreamingResponse(stream, media_type="text/plain")
