"""
Slot Service

This module contains the core business logic for slot extraction and filling.
"""

import copy
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Union, get_args

from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

from masterbrain.configs import DEFAULT_QWEN_VL_MODEL, AvailableQwenModel, select_client

from ..types import (
    FieldInputRequest,
    FieldInputResponse,
    SlotOperation,
    SlotUpdateResult,
)
from .prompts import create_slot_extraction_prompt
from .prompts.user_image import (
    clean_image_recognition_results,
    create_image_extraction_system_prompt,
)


def generate_unique_id() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def load_schema(schema: Union[str, dict]) -> dict:
    """Load schema data from a JSON file or a dictionary."""
    if isinstance(schema, str):
        with open(schema, "r") as file:
            return json.load(file)
    return schema


def extract_required_keys(schema_data: dict) -> list:
    """Extract required keys and their descriptions from the schema data."""
    required_keys = schema_data.get("required", [])
    properties = schema_data.get("properties", {})

    key_description_pairs = []
    for key in required_keys:
        prop = properties.get(key, {})
        description = prop.get("description", prop.get("title", key)).strip()
        key_description_pairs.append((key, description))

    return key_description_pairs


def format_update_info(update_info_list: List[Dict[str, Any]]) -> SlotUpdateResult:
    """Format update information into the required JSON structure."""
    operations = []
    for info in update_info_list:
        slot_name = info["slot_name"]
        new_value = info["new_value"]
        old_value = info["old_value"]
        # 统一转为字符串再做 null 检查，避免整数等非字符串值调用 .lower() 崩溃
        slot_name_str = str(slot_name) if slot_name is not None else "null"
        new_value_str = str(new_value) if new_value is not None else "null"
        if (
            slot_name
            and slot_name_str.lower() != "null"
            and new_value is not None
            and new_value_str.lower() != "null"
            and old_value != new_value
        ):  # 确保值确实发生了变化
            operations.append(
                SlotOperation(
                    operation="update",
                    rf_name=slot_name_str,
                    rf_value=new_value_str,
                )
            )

    return SlotUpdateResult(required=operations)


def is_base64_image(data):
    """Check if the given data is a base64 encoded image."""
    if data is None:
        return False
    if data.startswith("data:image/") and ";base64," in data:
        data = data.split(";base64,")[1]
        return True
    else:
        return False


def is_image_url(data):
    """Check if the given data is an image URL."""
    if data is None:
        return False

    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"]
    data = data.strip().lower()

    # 检查是否是一个URL
    if data.startswith(("http://", "https://")):
        # 检查是否以常见图片扩展名结尾
        if any(data.endswith(ext) for ext in image_extensions):
            return True
        # 检查常见图片CDN或图片服务格式
        if any(
            pattern in data
            for pattern in [
                "cloudinary.com/image",
                "imgur.com",
                "/images/",
                "img.",
                ".jpg?",
                ".png?",
                ".jpeg?",
            ]
        ):
            return True
    return False


# Qwen vision-capable model names
_QWEN_VL_MODELS = frozenset(
    {
        "qwen-vl-plus",
        "qwen-vl-plus-latest",
        "qwen-vl-max-0201",
        "qwen3-vl-flash",
        "qwen3-vl-plus",
        "qwen-omni-turbo-latest",
        "qwen3.5-flash",
        "qwen3.5-plus",
        "qwen3-max",
    }
)

# OpenAI vision-capable model names
_OPENAI_VL_MODELS = frozenset(
    {
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
    }
)


def get_vision_model_for(model_name: str) -> str:
    """
    Return a vision-capable model name for the same provider.

    If the given model already supports vision, return it as-is.
    Otherwise fall back to the default vision model of that provider:
      - Qwen  → DEFAULT_QWEN_VL_MODEL  (qwen-vl-plus-latest)
      - OpenAI → gpt-4o-mini
    """
    if model_name in _QWEN_VL_MODELS or model_name in _OPENAI_VL_MODELS:
        return model_name
    if model_name in get_args(AvailableQwenModel):
        return DEFAULT_QWEN_VL_MODEL
    return "gpt-4o-mini"


class SlotMemory:
    """Memory management for slot extraction and conversation history."""

    def __init__(self, key_description_list: List[tuple]):
        self.default_slot_dict = {}
        self.default_update_dict = {
            "slot_name": None,
            "old_value": None,
            "new_value": None,
        }
        self.chat_history = []
        self.current_slots = {key: "null" for key, _ in key_description_list}
        self.current_update_info_list = [copy.deepcopy(self.default_update_dict)]
        self.current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M")
        self.inform_check = False
        self.key_description_list = key_description_list

    def update_information_check(self):
        """Check if all slots are filled with information."""
        self.inform_check = all(
            value != "null" for value in self.current_slots.values()
        )

    def parse_update_info(self, update_output: str) -> List[Dict[str, Any]]:
        """Parse the update information from a string."""
        if not update_output:
            return [self.default_update_dict]

        update_info_list = []
        update_output_list = [
            info.strip() for info in update_output.split("\n") if info
        ]
        for single_update in update_output_list:
            # Only process lines that start with "UPDATE"
            if not single_update.strip().startswith("UPDATE"):
                continue

            try:
                # Remove "UPDATE" and split by spaces, but only split into at most 3 parts
                # This ensures values with spaces stay together
                parts = single_update.replace("UPDATE", "", 1).strip().split(maxsplit=2)

                if len(parts) == 3:
                    slot_name, old_value, new_value = parts
                else:
                    slot_name, old_value, new_value = None, None, None
            except ValueError:
                slot_name, old_value, new_value = None, None, None

            update_info_list.append(
                {
                    "slot_name": slot_name,
                    "old_value": old_value,
                    "new_value": new_value,
                }
            )

        # Return default if no valid updates were found
        if not update_info_list:
            return [self.default_update_dict]

        return update_info_list

    async def generate_response(
        self,
        chat_request: FieldInputRequest,
        prompt_template: Union[str, PromptTemplate],
        input_text: str,
    ) -> SlotUpdateResult:
        """Generate a response using the OpenAI client."""
        # 检查输入是否为图片
        is_image = False
        image_note = ""

        # 检查是否为base64编码的图片
        if is_base64_image(input_text):
            is_image = True
            image_note = " (This input is from an image)"
        # 检查是否为图片URL
        elif is_image_url(input_text):
            is_image = True
            image_note = " (This input is from an image)"

        # 处理图片输入
        if is_image:
            vision_model = get_vision_model_for(chat_request.model.name)
            client = select_client(vision_model)

            if chat_request.image_mode == "one_step":
                # ── One-step：VL 模型直接读图 + 槽位抽取，一次完成 ──────────────
                system_prompt = prompt_template.format(
                    history=None,
                    input="[attached image]",
                    slots=self.current_slots,
                    check=self.inform_check,
                    current_datetime=self.current_datetime,
                    is_from_image=image_note,
                )
                response = await client.chat.completions.create(
                    model=vision_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract slot values directly from this image and respond in the required format:",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": input_text},
                                },
                            ],
                        },
                    ],
                )
                content = response.choices[0].message.content or ""
                output = content.replace("None", "null").strip()
                print("#one_step output", output)

                try:
                    output, update_output = output.strip("~~~").split("~~~")
                except ValueError:
                    update_output = None

                self.current_update_info_list = self.parse_update_info(update_output or "")

                try:
                    output_json = json.loads(output)
                except json.JSONDecodeError:
                    output_json = self.current_slots

                for key, value in output_json.items():
                    if value and value != "null":
                        self.current_slots[key] = value

                return format_update_info(self.current_update_info_list)

            else:
                # ── Two-step（默认）：先 OCR 提取文本，再做槽位抽取 ─────────────
                system_message = create_image_extraction_system_prompt(
                    self.key_description_list
                )
                response = await client.chat.completions.create(
                    model=vision_model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_message,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract all experiment data from this image:",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"{input_text}"},
                                },
                            ],
                        },
                    ],
                )
                input_text = response.choices[0].message.content or ""
                input_text = clean_image_recognition_results(input_text)
                print(f"图片识别结果:{input_text}")

        # 格式化系统提示
        system_prompt = prompt_template.format(
            history=None,
            input=input_text,
            slots=self.current_slots,
            check=self.inform_check,
            current_datetime=self.current_datetime,
            is_from_image=image_note if is_image else "",
        )

        self.chat_history.extend(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ]
        )
        client = select_client(chat_request.model.name)

        response = await client.chat.completions.create(
            model=chat_request.model.name,
            messages=self.chat_history,
        )
        content = response.choices[0].message.content or ""
        output = content.replace("None", "null").strip()

        print("#1", output)

        try:
            output, update_output = output.strip("~~~").split("~~~")
        except ValueError:
            update_output = None

        print("#2", update_output)

        self.current_update_info_list = self.parse_update_info(update_output or "")

        print("#3", self.current_update_info_list)

        try:
            output_json = json.loads(output)
        except json.JSONDecodeError:
            output_json = self.current_slots

        for key, value in output_json.items():
            if value and value != "null":
                self.current_slots[key] = value

        return format_update_info(self.current_update_info_list)


async def handle_slot_extraction(chat_request: FieldInputRequest) -> FieldInputResponse:
    """
    Handle slot extraction for field input.

    Args:
        chat_request: The field input request

    Returns:
        FieldInputResponse: Updated response with slot operations
    """
    start_time = time.time()
    _, _, history = (
        chat_request.chat_id,
        chat_request.user_id,
        chat_request.history,
    )

    # Check if history is empty
    if not history:
        raise ValueError("History cannot be empty")

    protocol_schema = chat_request.scenario.get("protocol_schema", {})
    query = history[-1]["content"]

    schema_data = load_schema(protocol_schema)
    key_description_list = extract_required_keys(schema_data)
    memory = SlotMemory(key_description_list)

    prompt_template = create_slot_extraction_prompt(key_description_list)
    operation_result = await memory.generate_response(
        chat_request, prompt_template, query
    )

    # Convert SlotUpdateResult to the expected format for tool calls
    # Use model_dump() for Pydantic v2 compatibility
    operations_dict = {
        "operations": [op.model_dump() for op in operation_result.required]
    }

    tmp_dict = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "id_sf_" + generate_unique_id(),
                "type": "function",
                "function": {"name": "slot_filling"},
                "arguments": json.dumps(operations_dict),
            }
        ],
    }
    history.append(tmp_dict)

    end_time = time.time()
    print(f"SF Total Time: {end_time - start_time:.6f} s")

    return FieldInputResponse(
        chat_id=chat_request.chat_id,
        user_id=chat_request.user_id,
        model=chat_request.model,
        history=history,
        scenario={"protocol_schema": protocol_schema},
    )
