__all__ = ["protocol_generation_assigner_router"]

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from masterbrain.endpoints.protocol_generation.assigner.logic import generate_stream
from masterbrain.endpoints.protocol_generation.assigner.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
)
from masterbrain.types.error import LlmError

from .types import AssignerProtocolMessage

protocol_generation_assigner_router = APIRouter()


@protocol_generation_assigner_router.post(
    "/protocol_generation/assigner",
    summary="STEP3: Protocol Assigner Generation",
    responses={
        200: {"description": "Success", "model": AssignerProtocolMessage},
        400: {"description": "Bad Request", "model": LlmError},
    },
)
async def generate_protocol_assigner(protocol_msg: AssignerProtocolMessage):
    history = [{"role": "system", "content": SYSTEM_MESSAGE_PROMPT}]

    return StreamingResponse(
        generate_stream(protocol_msg, history), media_type="text/plain"
    )
