__all__ = ["workspace_router"]

from fastapi import APIRouter, HTTPException, Query, Request, Response

from masterbrain.workspace_manager import workspace_manager

from .types import (
    CreateWorkspaceFolderInput,
    OpenWorkspaceInput,
    RenameWorkspaceFileInput,
    RenameWorkspaceFileOutput,
    WorkspaceState,
    WriteWorkspaceFileInput,
)

workspace_router = APIRouter()


def _workspace_state() -> WorkspaceState:
    return WorkspaceState.model_validate(workspace_manager.snapshot())


@workspace_router.get("/workspace", response_model=WorkspaceState)
async def get_workspace_state() -> WorkspaceState:
    return _workspace_state()


@workspace_router.post("/workspace/open", response_model=WorkspaceState)
async def open_workspace(payload: OpenWorkspaceInput) -> WorkspaceState:
    try:
        workspace_manager.set_root(payload.path)
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.post("/workspace/select", response_model=WorkspaceState)
async def select_workspace() -> WorkspaceState:
    try:
        workspace_manager.select_root()
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


@workspace_router.put("/workspace/file", response_model=WorkspaceState)
async def write_workspace_file(payload: WriteWorkspaceFileInput) -> WorkspaceState:
    try:
        workspace_manager.write_file(payload.path, payload.content)
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.post("/workspace/file", response_model=WorkspaceState)
async def create_workspace_file(payload: WriteWorkspaceFileInput) -> WorkspaceState:
    try:
        workspace_manager.create_file(payload.path, payload.content)
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.delete("/workspace/file", response_model=WorkspaceState)
async def delete_workspace_file(path: str = Query(...)) -> WorkspaceState:
    try:
        workspace_manager.delete_file(path)
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.post("/workspace/rename", response_model=RenameWorkspaceFileOutput)
async def rename_workspace_file(
    payload: RenameWorkspaceFileInput,
) -> RenameWorkspaceFileOutput:
    try:
        new_path = workspace_manager.rename_file(payload.old_path, payload.new_name)
        return RenameWorkspaceFileOutput(path=new_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.post("/workspace/folder", response_model=WorkspaceState)
async def create_workspace_folder(payload: CreateWorkspaceFolderInput) -> WorkspaceState:
    try:
        workspace_manager.create_folder(payload.path)
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.post("/workspace/import-zip", response_model=WorkspaceState)
async def import_workspace_zip(request: Request) -> WorkspaceState:
    try:
        payload = await request.body()
        if not payload:
            raise ValueError("ZIP upload body is empty.")
        workspace_manager.import_zip_bytes(payload)
        return _workspace_state()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@workspace_router.get("/workspace/export-zip")
async def export_workspace_zip() -> Response:
    try:
        filename, payload = workspace_manager.export_zip_bytes()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=payload, media_type="application/zip", headers=headers)
