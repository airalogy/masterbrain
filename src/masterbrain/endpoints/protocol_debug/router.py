__all__ = ["protocol_debug_router"]

from fastapi import APIRouter

from masterbrain.endpoints.protocol_debug.logic import generate_debug_result
from masterbrain.endpoints.protocol_debug.types import ProtocolDebugInput, ProtocolDebugOutput
from masterbrain.types.error import LlmError

protocol_debug_router = APIRouter()


@protocol_debug_router.post(
    "/protocol_debug",
    summary="Protocol Debug",
    responses={
        200: {"description": "Success", "model": ProtocolDebugOutput},
        400: {"description": "Bad Request", "model": LlmError},
        504: {"description": "Gateway Timeout", "model": LlmError},
    },
)
async def process_protocol_debug(protocol_debug_input: ProtocolDebugInput):
    """Process protocol debug request"""
    return await generate_debug_result(protocol_debug_input)
