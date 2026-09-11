"""Reusable, bounded text embeddings; authorization and indexes belong to hosts."""

from __future__ import annotations

import math
import sys
from collections.abc import Mapping
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from masterbrain.providers.registry import EmbeddingModel

MAX_EMBEDDING_BATCH_SIZE = 6
EmbeddingText = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=32768)
]


class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: EmbeddingModel
    input: list[EmbeddingText] = Field(
        min_length=1, max_length=MAX_EMBEDDING_BATCH_SIZE
    )
    dimensions: int | None = Field(default=None, strict=True, ge=1, le=8192)

    @model_validator(mode="after")
    def validate_content(self) -> EmbeddingRequest:
        if any(not text.strip() for text in self.input):
            raise ValueError("Embedding input must contain non-whitespace text")
        if self.model == "text-embedding-ada-002" and self.dimensions is not None:
            raise ValueError("text-embedding-ada-002 does not support dimensions")
        return self


class EmbeddingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=255, strict=True)
    dimensions: int = Field(strict=True, ge=1, le=8192)
    vectors: list[list[Annotated[float, Field(strict=True, allow_inf_nan=False)]]] = (
        Field(min_length=1, max_length=MAX_EMBEDDING_BATCH_SIZE)
    )

    @model_validator(mode="after")
    def validate_dimensions(self) -> EmbeddingResponse:
        if any(len(vector) != self.dimensions for vector in self.vectors):
            raise ValueError("Embedding response dimensions do not match")
        return self


class InvalidEmbeddingResponse(ValueError):
    """The provider returned vectors that cannot safely be indexed."""


def _field(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, Mapping) else getattr(value, name, None)


def _normalize_response(response: Any, request: EmbeddingRequest) -> EmbeddingResponse:
    data = _field(response, "data")
    if not isinstance(data, list) or len(data) != len(request.input):
        raise InvalidEmbeddingResponse("Embedding response count does not match input")
    vectors: dict[int, list[float]] = {}
    dimensions = request.dimensions
    for item in data:
        index = _field(item, "index")
        vector = _field(item, "embedding")
        if type(index) is not int or index not in range(len(data)) or index in vectors:
            raise InvalidEmbeddingResponse("Embedding response indexes are invalid")
        if not isinstance(vector, list) or not vector or len(vector) > 8192:
            raise InvalidEmbeddingResponse("Embedding response vector is invalid")
        if dimensions is None:
            dimensions = len(vector)
        if len(vector) != dimensions:
            raise InvalidEmbeddingResponse("Embedding response dimensions do not match")
        if any(
            type(value) not in (int, float)
            or abs(value) > sys.float_info.max
            or not math.isfinite(value)
            for value in vector
        ):
            raise InvalidEmbeddingResponse(
                "Embedding response contains non-finite or non-numeric values"
            )
        vectors[index] = [float(value) for value in vector]
    model = _field(response, "model")
    return EmbeddingResponse(
        model=model if isinstance(model, str) and model else request.model,
        dimensions=dimensions,
        vectors=[vectors[index] for index in range(len(data))],
    )


async def create_embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    """Embed one batch using configured credentials and the active UsageContext.

    No implicit model fallback: hosts must not mix different embedding spaces.
    This function neither reads host data nor writes a vector index.
    """
    from masterbrain.configs import select_client
    from masterbrain.utils.llm import ensure_model_api_key

    ensure_model_api_key(request.model)
    response = await select_client(request.model).embeddings.create(
        model=request.model,
        input=request.input,
        **(
            {"dimensions": request.dimensions} if request.dimensions is not None else {}
        ),
        encoding_format="float",
        timeout=60,
    )
    return _normalize_response(response, request)
