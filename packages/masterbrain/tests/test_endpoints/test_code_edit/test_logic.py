"""Unit tests for code edit logic."""

from pathlib import Path

import pytest

from masterbrain.endpoints.code_edit.logic import (
    OpenCodeRunResult,
    build_code_edit_prompt,
    compute_workspace_changes,
    generate_code_edit_result,
)
from masterbrain.endpoints.code_edit.types import (
    ChatHistoryMessage,
    CodeEditInput,
    EditorSelection,
    SupportedModels,
    WorkspaceFile,
)


class FakeRuntime:
    """Test runtime that edits files directly in the temp workspace."""

    async def run(self, workspace_dir: Path, **_: object) -> OpenCodeRunResult:
        protocol_path = workspace_dir / "protocol.aimd"
        protocol_path.write_text(
            "# Protocol\n\n{{step|sample,1}} Collect sample twice.\n",
            encoding="utf-8",
        )
        helper_path = workspace_dir / "helper.py"
        helper_path.write_text(
            "def repeat(count: int) -> int:\n    return count * 2\n",
            encoding="utf-8",
        )
        return OpenCodeRunResult(
            message="Updated the protocol step and added a helper.",
            execution_log=[
                "Created OpenCode session session-123.",
                "Submitted edit request to dashscope/qwen3.5-flash.",
            ],
        )


class FakeNoChangeRuntime:
    """Test runtime that completes successfully without editing files."""

    async def run(self, workspace_dir: Path, **_: object) -> OpenCodeRunResult:
        assert (workspace_dir / "protocol.aimd").exists()
        return OpenCodeRunResult(
            message="Reviewed the file and no change was necessary.",
            execution_log=["OpenCode returned an answer without file edits."],
        )


def test_build_code_edit_prompt_contains_editor_context():
    code_edit_input = CodeEditInput(
        model=SupportedModels(name="qwen3.5-flash", enable_thinking=False),
        prompt="Refine the selected step.",
        files=[
            WorkspaceFile(
                path="protocol.aimd",
                content="# Protocol",
                type="aimd",
            )
        ],
        active_file_path="protocol.aimd",
        selection=EditorSelection(
            text="{{step|sample,1}} Collect sample once.",
            start_offset=10,
            end_offset=48,
        ),
        chat_history=[
            ChatHistoryMessage(role="user", content="Please improve the sampling step.")
        ],
    )

    prompt = build_code_edit_prompt(code_edit_input)

    assert "Active file: protocol.aimd" in prompt
    assert "Workspace file count: 1" in prompt
    assert "{{step|sample,1}} Collect sample once." in prompt
    assert "Current user request:" in prompt


def test_compute_workspace_changes_reports_create_modify_delete():
    before = {
        "protocol.aimd": "# old",
        "model.py": "print('old')\n",
    }
    after = {
        "protocol.aimd": "# new",
        "helper.py": "print('new helper')\n",
    }

    changed_files, warnings = compute_workspace_changes(before, after)

    assert warnings == []
    assert [change.path for change in changed_files] == [
        "helper.py",
        "model.py",
        "protocol.aimd",
    ]
    assert [change.status for change in changed_files] == [
        "created",
        "deleted",
        "modified",
    ]


@pytest.mark.asyncio
async def test_generate_code_edit_result_uses_runtime_and_collects_changes():
    code_edit_input = CodeEditInput(
        model=SupportedModels(name="qwen3.5-flash", enable_thinking=True),
        prompt="Update the workspace.",
        files=[
            WorkspaceFile(
                path="protocol.aimd",
                content="# Protocol\n\n{{step|sample,1}} Collect sample once.\n",
                type="aimd",
            )
        ],
    )

    result = await generate_code_edit_result(code_edit_input, runtime=FakeRuntime())

    assert result.runtime == "opencode"
    assert "Updated the protocol step" in result.message
    assert [change.path for change in result.changed_files] == [
        "helper.py",
        "protocol.aimd",
    ]
    assert result.edit_status == "changed"
    assert any("enable_thinking" in warning for warning in result.warnings)
    assert any("Created OpenCode session" in line for line in result.execution_log)


@pytest.mark.asyncio
async def test_generate_code_edit_result_marks_no_changes():
    code_edit_input = CodeEditInput(
        model=SupportedModels(name="qwen3.5-flash", enable_thinking=False),
        prompt="Explain whether the protocol needs edits.",
        files=[
            WorkspaceFile(
                path="protocol.aimd",
                content="# Protocol\n\n{{step|sample,1}} Collect sample once.\n",
                type="aimd",
            )
        ],
    )

    result = await generate_code_edit_result(
        code_edit_input,
        runtime=FakeNoChangeRuntime(),
    )

    assert result.edit_status == "no_changes"
    assert result.changed_files == []
    assert "no change was necessary" in result.message
    assert any("no supported workspace files changed" in line for line in result.execution_log)
