__all__ = ["paper_generation_router"]

from fastapi import APIRouter

from masterbrain.endpoints.paper_generation.logic import generate_paper
from masterbrain.endpoints.paper_generation.types import PaperGenerationInput, PaperGenerationOutput
from masterbrain.types.error import LlmError
from masterbrain.utils.llm import ensure_model_api_key

paper_generation_router = APIRouter()


@paper_generation_router.post(
    "/paper_generation",
    summary="Paper Generation",
    responses={
        200: {"description": "Success", "model": PaperGenerationOutput},
        400: {"description": "Bad Request", "model": LlmError},
        504: {"description": "Gateway Timeout", "model": LlmError},
    },
)
async def process_paper_generation(paper_generation_input: PaperGenerationInput):
    """Process protocol debug request"""
    protocol_markdown_list = paper_generation_input.protocol_markdown_list
    model = paper_generation_input.model
    enable_external_reference_search = paper_generation_input.enable_external_reference_search
    ensure_model_api_key(model.name)

    paper_markdown = await generate_paper(protocol_markdown_list, model, enable_external_reference_search)

    return PaperGenerationOutput(paper_markdown=paper_markdown)
