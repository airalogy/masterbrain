from typing import Literal

from pydantic import BaseModel, Field


class WorkspaceFile(BaseModel):
    name: str
    path: str
    content: str
    type: Literal["aimd", "py", "other"]


class WorkspaceState(BaseModel):
    mode: Literal["directory"] = "directory"
    has_workspace: bool
    root_path: str | None = None
    files: list[WorkspaceFile] = Field(default_factory=list)
    folders: list[str] = Field(default_factory=list)
    entry_count: int = 0
    can_select_directory: bool = True


class OpenWorkspaceInput(BaseModel):
    path: str = Field(description="Absolute or user-expanded directory path")


class WriteWorkspaceFileInput(BaseModel):
    path: str
    content: str = ""


class RenameWorkspaceFileInput(BaseModel):
    old_path: str
    new_name: str


class CreateWorkspaceFolderInput(BaseModel):
    path: str


class RenameWorkspaceFileOutput(BaseModel):
    path: str
