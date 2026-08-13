from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ChangeSetId = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]


class SupportedModels(BaseModel):
    """Supported model configurations for code editing."""

    name: Literal[
        "qwen3.5-flash",
        "qwen3.5-plus",
        "qwen3-max",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ]
    enable_thinking: bool = False


DEFAULT_MODEL = SupportedModels(
    name="qwen3.5-flash",
    enable_thinking=False,
)


class WorkspaceFile(BaseModel):
    """A frontend workspace file materialized on the backend for code editing."""

    path: str = Field(description="Relative workspace path, for example src/model.py")
    content: str = Field(description="Current file content")
    type: Literal["aimd", "py", "toml", "other"] = Field(
        default="other",
        description="Frontend file type hint",
    )


class ChatHistoryMessage(BaseModel):
    """A compact chat history item forwarded to the code-edit runtime."""

    role: Literal["user", "assistant"]
    content: str


class EditorSelection(BaseModel):
    """The current editor selection in the active file."""

    text: str
    start_offset: int = Field(description="Selection start byte offset in the file")
    end_offset: int = Field(description="Selection end byte offset in the file")


class CodeEditInput(BaseModel):
    """Request payload for opencode-backed code editing."""

    model: SupportedModels = DEFAULT_MODEL
    prompt: str = Field(description="The user's current request")
    workspace_id: str | None = Field(
        default=None,
        max_length=240,
        description="Stable editor workspace identifier used for managed runtime reuse.",
    )
    files: list[WorkspaceFile] = Field(default_factory=list)
    active_file_path: str | None = Field(
        default=None,
        description="Relative path of the file currently focused in the editor",
    )
    selection: EditorSelection | None = None
    chat_history: list[ChatHistoryMessage] = Field(default_factory=list)


class CodeEditChangedFile(BaseModel):
    """A file change returned from the code-edit runtime."""

    path: str
    name: str
    type: Literal["aimd", "py", "toml"]
    status: Literal["created", "modified", "deleted"]
    content: str = Field(
        default="",
        description="Latest file content. Empty when the file was deleted.",
    )
    diff: str = Field(description="Unified diff against the incoming workspace state")
    before_hash: Sha256 | None = Field(
        default=None,
        description="SHA-256 of the incoming content. Null when the file is created.",
    )
    after_hash: Sha256 | None = Field(
        default=None,
        description="SHA-256 of the resulting content. Null when the file is deleted.",
    )


class CodeEditRisk(BaseModel):
    """Host-facing recommendation for applying a returned change set."""

    level: Literal["safe", "warning", "destructive"] = "safe"
    reasons: list[str] = Field(default_factory=list)
    recommended_action: Literal["auto_apply", "review", "block"] = "auto_apply"


class CodeEditOutput(BaseModel):
    """Response payload for opencode-backed code editing."""

    runtime: Literal["opencode"] = "opencode"
    contract_version: Literal["1"] = "1"
    outcome: Literal["answer", "changed"] = "answer"
    change_set_id: ChangeSetId | None = Field(
        default=None,
        description="Stable content-derived identifier for the returned workspace changes.",
    )
    message: str
    edit_status: Literal["changed", "no_changes"] = "no_changes"
    changed_files: list[CodeEditChangedFile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    execution_log: list[str] = Field(default_factory=list)
    risk: CodeEditRisk = Field(default_factory=CodeEditRisk)

    @model_validator(mode="after")
    def validate_change_state(self) -> "CodeEditOutput":
        has_changes = bool(self.changed_files)
        if self.outcome != ("changed" if has_changes else "answer"):
            raise ValueError("outcome must match changed_files")
        if self.edit_status != ("changed" if has_changes else "no_changes"):
            raise ValueError("edit_status must match changed_files")
        if has_changes != (self.change_set_id is not None):
            raise ValueError("change_set_id must be present exactly when files changed")
        unsafe_to_auto_apply = (
            bool(self.warnings)
            or self.risk.level != "safe"
            or any(change.status == "deleted" for change in self.changed_files)
        )
        if unsafe_to_auto_apply and self.risk.recommended_action == "auto_apply":
            raise ValueError("unsafe changes cannot recommend auto_apply")
        return self
