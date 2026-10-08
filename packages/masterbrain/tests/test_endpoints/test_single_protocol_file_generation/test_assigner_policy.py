"""Offline contracts: no provider credentials or live model calls."""

from masterbrain.protocol_authoring import ASSIGNER_RUNTIME_POLICY
from masterbrain.endpoints.code_edit.types import CodeEditInput
from masterbrain.endpoints.code_edit.logic import build_code_edit_prompt
from masterbrain.endpoints.single_protocol_file_generation.types import ProtocolMessage
from masterbrain.endpoints.code_edit.logic import SYSTEM_PROMPT
from masterbrain.endpoints.protocol_check.logic.prompts import SYSTEM_MESSAGE_PROTOCOL_CHECK_PROMPT
from masterbrain.endpoints.protocol_debug.logic.prompts import SYSTEM_MESSAGE_PROTOCOL_DEBUG_PROMPT
from masterbrain.endpoints.protocol_generation.assigner.logic.prompts import USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
from masterbrain.endpoints.single_protocol_file_generation.logic.prompts.system import SYSTEM_MESSAGE_PROMPT
from masterbrain.endpoints.single_protocol_file_generation.logic.prompts.shared import REFERENCE_PROTOCOL_EXAMPLE
from masterbrain.endpoints.single_protocol_file_generation.logic.prompts.user_protocol import USER_MESSAGE_PROTOCOL_TAIL_TEMPLATE


def test_generation_edit_check_and_debug_share_runtime_policy():
    for prompt in (SYSTEM_MESSAGE_PROMPT, SYSTEM_PROMPT, SYSTEM_MESSAGE_PROTOCOL_CHECK_PROMPT, SYSTEM_MESSAGE_PROTOCOL_DEBUG_PROMPT):
        assert ASSIGNER_RUNTIME_POLICY in prompt
        assert "prefer client-side assigners" in prompt
        assert "trusted server verification" in prompt
        assert "API/CSV imports must supply derived values" in prompt
        assert "Never put JavaScript in assigner.py" in prompt


def test_single_file_examples_use_client_syntax_without_python_duplicates():
    assert REFERENCE_PROTOCOL_EXAMPLE.count("```assigner runtime=client") == 2
    assert "@assigner(" not in REFERENCE_PROTOCOL_EXAMPLE
    assert 'gt=0' in REFERENCE_PROTOCOL_EXAMPLE
    assert "```assigner runtime=client" in USER_MESSAGE_PROTOCOL_TAIL_TEMPLATE
    assert "缺失观测值不得补零" in USER_MESSAGE_PROTOCOL_TAIL_TEMPLATE
    # The template is literal-replaced, not str.format-ed: JS/AIMD braces survive.
    rendered = USER_MESSAGE_PROTOCOL_TAIL_TEMPLATE.replace("{USER_MESSAGE_REF_PROTOCOL}", "synthetic")
    assert "{{var|ratio: float}}" in rendered
    assert "return {ratio: length / thickness};" in rendered


def test_legacy_python_endpoint_keeps_its_contract_and_skips_inline_outputs():
    assert "Python-only" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "跳过其已有输出，不重复生成" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE
    assert "from airalogy.assigner import AssignerResult, assigner" in USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE


def test_client_preference_is_opt_in_for_older_hosts():
    assert not ProtocolMessage(instruction="synthetic").prefer_client_assigners
    assert not CodeEditInput(prompt="synthetic").prefer_client_assigners
    assert "prefer_client_assigners=false" in build_code_edit_prompt(CodeEditInput(prompt="synthetic"))
    assert "prefer_client_assigners=true" in build_code_edit_prompt(CodeEditInput(prompt="synthetic", prefer_client_assigners=True))
