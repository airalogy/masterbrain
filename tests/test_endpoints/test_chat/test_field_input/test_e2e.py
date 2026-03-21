"""
End-to-End Tests for Field Input

真实 LLM 调用测试，不使用任何 Mock，验证完整的槽位填充流程。
覆盖：
  - 文本槽位填充（qwen3.5-flash / qwen3-max）
  - 图片 URL 槽位填充（two_step 模式：先 OCR 再抽取）
  - 图片 URL 槽位填充（one_step 模式：VL 模型直接抽取）
  - 防幻觉验证（时间字段不被自动推断）

运行方式：
    pytest tests/test_endpoints/test_chat/test_field_input/test_e2e.py -v -m e2e -s

    # 仅跑文本
    pytest ... -k "text"
    # 仅跑图片（全部）
    pytest ... -k "image"
    # 仅跑 one_step
    pytest ... -k "one_step"
    # 仅跑 two_step
    pytest ... -k "two_step"

注意：需要配置对应的 API Key 环境变量才能运行。
"""

import json
from pathlib import Path

import pytest

from masterbrain.endpoints.chat.field_input.logic.slot_service import handle_slot_extraction
from masterbrain.endpoints.chat.field_input.types import FieldInputRequest, FieldInputResponse, ModelConfig

FIXTURE_DIR = Path(__file__).parent

# Qwen 文本测试模型（按速度从快到慢）
QWEN_TEXT_MODELS = ["qwen3.5-flash", "qwen3-max"]

# Qwen 图片 two_step：使用文本模型（VL 回退由 get_vision_model_for 自动处理）
QWEN_IMAGE_TWO_STEP_MODELS = ["qwen3-max"]

# Qwen 图片 one_step：直接使用 VL 模型
QWEN_IMAGE_ONE_STEP_MODELS = ["qwen-vl-plus-latest"]


def load_fixture(filename: str) -> dict:
    """从 JSON fixture 文件加载测试数据。"""
    with open(FIXTURE_DIR / filename) as f:
        return json.load(f)


def assert_response_structure(result: FieldInputResponse, original_history_len: int, chat_id: str):
    """验证响应的通用结构，返回 operations 列表。"""
    assert isinstance(result, FieldInputResponse)
    assert result.chat_id == chat_id

    # history 应在原有基础上追加 1 条 assistant 消息
    assert len(result.history) == original_history_len + 1

    assistant_msg = result.history[-1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"] is None
    assert "tool_calls" in assistant_msg
    assert len(assistant_msg["tool_calls"]) == 1

    tool_call = assistant_msg["tool_calls"][0]
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "slot_filling"
    assert tool_call["id"].startswith("id_sf_")

    arguments = json.loads(tool_call["arguments"])
    assert "operations" in arguments

    for op in arguments["operations"]:
        assert op["operation"] == "update"
        assert op["rf_name"] and op["rf_name"].lower() != "null"
        assert op["rf_value"] and str(op["rf_value"]).lower() != "null"

    return arguments["operations"]


# ---------------------------------------------------------------------------
# 文本槽位填充 E2E 测试
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
@pytest.mark.parametrize("model_name", QWEN_TEXT_MODELS)
async def test_e2e_text_slot_extraction_qwen(model_name: str):
    """
    E2E：Qwen 文本输入槽位提取（参数化覆盖 qwen3.5-flash 和 qwen3-max）。

    Fixture: text_in_qwen.json
    输入：中文文本，明确给出 forward_primer_volume=50 和 reverse_primer_volume=150。
    期望：两个槽位均被正确提取，数值精确匹配。
    """
    data = load_fixture("text_in_qwen.json")
    data["model"]["name"] = model_name

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = assert_response_structure(result, len(data["history"]), data["chat_id"])
    op_map = {op["rf_name"]: str(op["rf_value"]) for op in ops}

    assert "forward_primer_volume" in op_map, (
        f"Expected 'forward_primer_volume' in extracted slots, got: {list(op_map.keys())}"
    )
    assert "reverse_primer_volume" in op_map, (
        f"Expected 'reverse_primer_volume' in extracted slots, got: {list(op_map.keys())}"
    )
    assert op_map["forward_primer_volume"] == "50", (
        f"Expected forward_primer_volume='50', got '{op_map['forward_primer_volume']}'"
    )
    assert op_map["reverse_primer_volume"] == "150", (
        f"Expected reverse_primer_volume='150', got '{op_map['reverse_primer_volume']}'"
    )


@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
async def test_e2e_text_slot_extraction_multi_turn_qwen():
    """
    E2E：Qwen 多轮对话文本槽位提取。

    Fixture: text_in_qwen.json（覆盖 history）
    验证在带有历史对话的情况下，仍能正确从最后一条用户消息中提取槽位。
    """
    data = load_fixture("text_in_qwen.json")
    data["model"]["name"] = "qwen3-max"
    data["history"] = [
        {"role": "user", "content": "我想记录一下实验数据。"},
        {"role": "assistant", "content": "好的，请告诉我 forward_primer_volume 和 reverse_primer_volume 的数值。"},
        {"role": "user", "content": "forward_primer_volume是50；reverse_primer_volume是150。"},
    ]

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = assert_response_structure(result, len(data["history"]), data["chat_id"])
    op_map = {op["rf_name"]: str(op["rf_value"]) for op in ops}

    assert "forward_primer_volume" in op_map
    assert "reverse_primer_volume" in op_map
    assert op_map["forward_primer_volume"] == "50"
    assert op_map["reverse_primer_volume"] == "150"


# ---------------------------------------------------------------------------
# 图片 URL 槽位填充 E2E 测试 —— two_step 模式
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
@pytest.mark.parametrize("model_name", QWEN_IMAGE_TWO_STEP_MODELS)
async def test_e2e_image_url_slot_extraction_two_step_qwen(model_name: str):
    """
    E2E：two_step 模式图片 URL 槽位提取。

    Fixture: imgL_in_qwen.json  (image_mode="two_step")
    流程：VL 模型 OCR → clean → 文本模型槽位抽取。
    期望：至少提取到 1 个有效槽位，槽位名在 schema 的 properties 中。
    """
    data = load_fixture("imgL_in_qwen.json")
    data["model"]["name"] = model_name

    schema_properties = set(data["scenario"]["protocol_schema"].get("properties", {}).keys())

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = assert_response_structure(result, len(data["history"]), data["chat_id"])

    assert len(ops) >= 1, (
        f"[two_step] Expected at least 1 slot from image, got 0. "
        f"Image: {data['history'][-1]['content']}"
    )
    for op in ops:
        assert op["rf_name"] in schema_properties, (
            f"[two_step] Slot '{op['rf_name']}' not in schema properties: {schema_properties}"
        )


@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
async def test_e2e_image_url_no_hallucination_two_step_qwen():
    """
    E2E：two_step 模式防幻觉验证。

    experiment_time 是系统内置时间字段，prompt 明确禁止自动推断时间，
    不应出现在提取结果中。
    """
    data = load_fixture("imgL_in_qwen.json")
    data["model"]["name"] = "qwen3-max"

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = json.loads(result.history[-1]["tool_calls"][0]["arguments"])["operations"]
    extracted_slots = {op["rf_name"] for op in ops}

    assert "experiment_time" not in extracted_slots, (
        f"[two_step] 'experiment_time' should NOT be auto-generated, "
        f"but appeared in: {extracted_slots}"
    )


# ---------------------------------------------------------------------------
# 图片 URL 槽位填充 E2E 测试 —— one_step 模式
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
@pytest.mark.parametrize("model_name", QWEN_IMAGE_ONE_STEP_MODELS)
async def test_e2e_image_url_slot_extraction_one_step_qwen(model_name: str):
    """
    E2E：one_step 模式图片 URL 槽位提取。

    Fixture: imgL_in_qwen_onestep.json  (image_mode="one_step")
    流程：VL 模型直接读图并输出槽位结果，单次 API 调用完成。
    期望：至少提取到 1 个有效槽位，槽位名在 schema 的 properties 中。
    """
    data = load_fixture("imgL_in_qwen_onestep.json")
    data["model"]["name"] = model_name

    schema_properties = set(data["scenario"]["protocol_schema"].get("properties", {}).keys())

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = assert_response_structure(result, len(data["history"]), data["chat_id"])

    assert len(ops) >= 1, (
        f"[one_step] Expected at least 1 slot from image, got 0. "
        f"Image: {data['history'][-1]['content']}"
    )
    for op in ops:
        assert op["rf_name"] in schema_properties, (
            f"[one_step] Slot '{op['rf_name']}' not in schema properties: {schema_properties}"
        )


@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
async def test_e2e_image_url_no_hallucination_one_step_qwen():
    """
    E2E：one_step 模式防幻觉验证。

    VL 模型在 one_step 模式下直接输出槽位结果时，
    experiment_time 同样不应被自动推断。
    """
    data = load_fixture("imgL_in_qwen_onestep.json")

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = json.loads(result.history[-1]["tool_calls"][0]["arguments"])["operations"]
    extracted_slots = {op["rf_name"] for op in ops}

    assert "experiment_time" not in extracted_slots, (
        f"[one_step] 'experiment_time' should NOT be auto-generated, "
        f"but appeared in: {extracted_slots}"
    )


# ---------------------------------------------------------------------------
# 对比测试：验证 one_step 和 two_step 都能提取到核心槽位
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.field_input
@pytest.mark.asyncio
@pytest.mark.parametrize("image_mode,fixture,model", [
    ("two_step", "imgL_in_qwen.json",          "qwen3-max"),
    ("one_step", "imgL_in_qwen_onestep.json",  "qwen-vl-plus-latest"),
])
async def test_e2e_image_both_modes_extract_slots(image_mode: str, fixture: str, model: str):
    """
    E2E：对比 one_step 和 two_step 两种模式均能从同一图片提取到槽位。

    同一张图片，两种模式应都能成功提取 ≥1 个槽位，
    且槽位名均在 schema properties 中。
    """
    data = load_fixture(fixture)
    data["model"]["name"] = model

    schema_properties = set(data["scenario"]["protocol_schema"].get("properties", {}).keys())

    request = FieldInputRequest(**data)
    result = await handle_slot_extraction(request)

    ops = assert_response_structure(result, len(data["history"]), data["chat_id"])

    assert len(ops) >= 1, (
        f"[{image_mode}] Expected ≥1 slot, got 0. Model: {model}"
    )
    for op in ops:
        assert op["rf_name"] in schema_properties, (
            f"[{image_mode}] Slot '{op['rf_name']}' not in schema"
        )
