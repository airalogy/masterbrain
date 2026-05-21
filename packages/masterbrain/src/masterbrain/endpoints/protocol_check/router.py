__all__ = ["protocol_check_router"]

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from masterbrain.endpoints.protocol_check.logic import generate_stream
from masterbrain.endpoints.protocol_check.types import ProtocolCheckInput
from masterbrain.types.error import LlmError
from masterbrain.utils.llm import ensure_model_api_key, preflight_text_stream

protocol_check_router = APIRouter()


@protocol_check_router.post(
    "/protocol_check",
    summary="Protocol Check and Improvement",
    responses={
        200: {"description": "Success", "model": ProtocolCheckInput},
        400: {"description": "Bad Request", "model": LlmError},
        504: {"description": "Gateway Timeout", "model": LlmError},
    },
)
async def process_protocol_check(protocol_check_input: ProtocolCheckInput):
    """Process protocol check request"""
    ensure_model_api_key(protocol_check_input.model.name)
    stream = await preflight_text_stream(
        generate_stream(protocol_check_input=protocol_check_input),
        model_name=protocol_check_input.model.name,
    )
    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8"
    )
