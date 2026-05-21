from typing import Literal

from pydantic import BaseModel, Field


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
    type: Literal["aimd", "py", "other"] = Field(
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
    type: Literal["aimd", "py"]
    status: Literal["created", "modified", "deleted"]
    content: str = Field(
        default="",
        description="Latest file content. Empty when the file was deleted.",
    )
    diff: str = Field(description="Unified diff against the incoming workspace state")


class CodeEditOutput(BaseModel):
    """Response payload for opencode-backed code editing."""

    runtime: Literal["opencode"] = "opencode"
    message: str
    edit_status: Literal["changed", "no_changes"] = "no_changes"
    changed_files: list[CodeEditChangedFile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    execution_log: list[str] = Field(default_factory=list)
