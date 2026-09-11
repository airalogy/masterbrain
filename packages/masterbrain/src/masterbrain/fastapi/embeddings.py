"""HTTP adapter for the shared embedding capability."""

from fastapi import APIRouter, HTTPException

from masterbrain.embeddings import (
    EmbeddingRequest,
    EmbeddingResponse,
    InvalidEmbeddingResponse,
    create_embeddings,
)

router = APIRouter()


@router.post("/embeddings", response_model=EmbeddingResponse)
async def embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    try:
        return await create_embeddings(request)
    except InvalidEmbeddingResponse as exc:
        # Do not reflect raw provider payloads or source text in API errors.
        raise HTTPException(
            status_code=502, detail="Invalid embedding provider response"
        ) from exc
