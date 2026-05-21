__all__ = ["chat_qa_vision_router"]

import time
from typing import Tuple, List, Dict, Any, Optional, cast

from fastapi import APIRouter, HTTPException
from openai.types.chat import ChatCompletionMessageParam

from masterbrain.configs import select_client
from masterbrain.types.error import LlmError
from masterbrain.utils.llm import ensure_model_api_key, llm_http_exception

from .types import VisionRequestBody

chat_qa_vision_router = APIRouter()


def parse_request_data(request_data: VisionRequestBody) -> Tuple[Optional[str], Optional[str], str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    chat_id = request_data.chat_id or None
    user_id = request_data.user_id or None
    model = request_data.model or "gpt-4o"
    conversation_history = request_data.history or []
    scenario_data = request_data.scenario or {}
    protocol_schema = scenario_data.get("protocol_schema", None)

    return chat_id, user_id, model, conversation_history, protocol_schema


async def recognize_image(client, conversation_history: List[Dict[str, Any]], model_name: str) -> str:
    try:
        response = await client.chat.completions.create(
            messages=cast(List[ChatCompletionMessageParam], conversation_history), 
            model=model_name
        )
        recognized_text = response.choices[0].message.content
        return recognized_text or ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision recognition failed: {str(e)}")


@chat_qa_vision_router.post(
    "/chat/qa/vision",
    summary="Image Recognition and Interpretation",
    responses={
        200: {"description": "Success", "model": dict},
        400: {"description": "Bad Request", "model": LlmError},
    },
)
async def handle_vision_request(request_data: VisionRequestBody) -> VisionRequestBody:
    _, _, model, conversation_history, _ = parse_request_data(request_data)
    ensure_model_api_key(model)
    
    if not conversation_history:
        raise HTTPException(status_code=400, detail="No conversation history provided")
        
    start_time = time.time()
    
    try:
        # Get the last message for vision processing
        last_message = conversation_history[-1]
        if "content" not in last_message:
            raise HTTPException(status_code=400, detail="No content in last message")
        
        # Prepare conversation for vision model
        vision_conversation = [last_message]
        
        # Get client and process vision request
        client = select_client(model)
        recognized_text = await recognize_image(client, vision_conversation, model)
        
        # Clean up the recognized text
        cleaned_text = recognized_text.replace("```", "").replace("\n", "").strip()
        
        # Add recognized text to conversation history
        conversation_history.append({"role": "assistant", "content": cleaned_text})
        
        end_time = time.time()
        print(f"Vision Recognition completed in {end_time - start_time:.6f} seconds")
        
        return request_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise llm_http_exception(e, model) from e
