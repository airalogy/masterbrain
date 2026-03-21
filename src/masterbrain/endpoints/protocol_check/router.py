__all__ = ["protocol_check_router"]

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from masterbrain.endpoints.protocol_check.logic import generate_stream
from masterbrain.endpoints.protocol_check.types import ProtocolCheckInput
from masterbrain.types.error import LlmError

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
    return StreamingResponse(
        generate_stream(protocol_check_input=protocol_check_input),
        media_type="text/plain; charset=utf-8"
    )
