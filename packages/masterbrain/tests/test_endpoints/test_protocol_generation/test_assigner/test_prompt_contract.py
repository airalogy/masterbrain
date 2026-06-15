from masterbrain.endpoints.protocol_check.logic.prompts import (
    SYSTEM_MESSAGE_PROTOCOL_CHECK_PROMPT,
)
from masterbrain.endpoints.protocol_generation.assigner.logic.prompts import (
    SYSTEM_MESSAGE_PROMPT,
    USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE,
)


def test_assigner_generation_prompt_requires_current_syntax():
    assert "from airalogy.assigner import AssignerResult, assigner" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "dependent_fields: dict" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "不要导入或使用 `AssignerBase`" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "不要生成 `class Assigner(...)`" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "不要生成 `@staticmethod`" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "不要使用参数名 `dependent_data`" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE


def test_assigner_system_prompt_rejects_deprecated_syntax():
    assert "module-level and function-based" in SYSTEM_MESSAGE_PROMPT
    assert "Do not use `AssignerBase`" in SYSTEM_MESSAGE_PROMPT
    assert "Do not use `AssignerBase`, `class Assigner`, `@staticmethod`, or `dependent_data`" in SYSTEM_MESSAGE_PROMPT


def test_protocol_check_reference_example_uses_current_assigner_syntax():
    reference_example = SYSTEM_MESSAGE_PROTOCOL_CHECK_PROMPT.split("最终的assigner.py：", 1)[1]

    assert "from airalogy.assigner import AssignerResult, assigner" in reference_example
    assert "def calculate_inhibition_rate(dependent_fields: dict) -> AssignerResult" in reference_example
    assert "class Assigner" not in reference_example.split("============================", 1)[0]
    assert "AssignerBase" not in reference_example.split("============================", 1)[0]
    assert "@staticmethod" not in reference_example.split("============================", 1)[0]
    assert "dependent_data" not in reference_example.split("============================", 1)[0]
