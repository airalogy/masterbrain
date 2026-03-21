__all__ = ["chat_qa_language_router"]

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from masterbrain.endpoints.chat.qa.language.logic import generate_stream

from .types import ChatInput

chat_qa_language_router = APIRouter()


@chat_qa_language_router.post(
    "/chat/qa/language",
    summary="Chat w/o injected Airalogy Protocols, Records, and Discussions",
)
async def chat_qa_language(chat_input: ChatInput):
    return StreamingResponse(
        generate_stream(chat_input=chat_input), media_type="text/plain; charset=utf-8"
    )
