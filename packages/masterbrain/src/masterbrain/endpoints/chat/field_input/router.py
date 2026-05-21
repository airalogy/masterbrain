"""
Field Input Router

FastAPI router for the field_input endpoint.
"""

from fastapi import APIRouter, HTTPException

from masterbrain.types.error import LlmError
from masterbrain.utils.llm import ensure_model_api_key, llm_http_exception

from .types import FieldInputRequest, FieldInputResponse
from .logic import handle_slot_extraction

field_input_router = APIRouter()


@field_input_router.post(
    "/chat/field_input",
    summary="Automatic Slot Filling",
    responses={
        200: {"description": "Success", "model": FieldInputResponse},
        400: {"description": "Bad Request", "model": LlmError},
    },
)
async def field_input(chat_request: FieldInputRequest) -> FieldInputResponse:
    """
    Field Input endpoint for automatic slot filling.
    
    This endpoint extracts relevant information from user input and automatically
    fills predefined slots/fields based on the provided protocol schema.
    
    Args:
        chat_request: Field input request containing conversation history and protocol schema
        
    Returns:
        FieldInputResponse: Updated conversation with slot filling operations
    """
    try:
        ensure_model_api_key(chat_request.model.name)
        return await handle_slot_extraction(chat_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise llm_http_exception(e, chat_request.model.name) from e
