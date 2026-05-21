__all__ = ["code_edit_router"]

from fastapi import APIRouter, HTTPException

from masterbrain.endpoints.code_edit.logic import generate_code_edit_result
from masterbrain.endpoints.code_edit.types import CodeEditInput, CodeEditOutput
from masterbrain.types.error import LlmError

code_edit_router = APIRouter()


@code_edit_router.post(
    "/code_edit",
    summary="Code Edit via OpenCode",
    responses={
        200: {"description": "Success", "model": CodeEditOutput},
        400: {"description": "Bad Request", "model": LlmError},
        503: {"description": "OpenCode Runtime Unavailable", "model": LlmError},
        500: {"description": "Runtime Error", "model": LlmError},
        504: {"description": "Gateway Timeout", "model": LlmError},
    },
)
async def process_code_edit(code_edit_input: CodeEditInput):
    """Run an opencode-backed code editing request against a materialized workspace."""
    try:
        return await generate_code_edit_result(code_edit_input)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        detail = str(exc).strip() or "OpenCode runtime error."

        if "timed out" in detail.lower():
            raise HTTPException(status_code=504, detail=detail) from exc

        if "opencode" in detail.lower():
            raise HTTPException(status_code=503, detail=detail) from exc

        raise HTTPException(status_code=500, detail=detail) from exc
