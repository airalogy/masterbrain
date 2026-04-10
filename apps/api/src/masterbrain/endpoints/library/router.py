__all__ = ["library_router"]

from fastapi import APIRouter, HTTPException, Query, Request

from masterbrain.library_store import library_store

from .types import (
    LibraryImportPathInput,
    LibraryImportResponse,
    LibraryProtocolPreview,
    LibraryRecordDetail,
    LibraryState,
)

library_router = APIRouter()


@library_router.get("/library", response_model=LibraryState)
async def get_library_state(
    limit: int = Query(50, ge=1, le=200),
) -> LibraryState:
    return LibraryState.model_validate(library_store.get_state(limit=limit))


@library_router.post("/library/import-aira", response_model=LibraryImportResponse)
async def import_library_aira(
    request: Request,
    source_name: str = Query(..., min_length=1),
    source_path: str | None = Query(default=None),
) -> LibraryImportResponse:
    try:
        payload = await request.body()
        if not payload:
            raise ValueError("Archive upload body is empty.")
        result = library_store.import_archive_bytes(
            payload,
            source_name=source_name,
            source_path=source_path,
        )
        return LibraryImportResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@library_router.post("/library/import-path", response_model=LibraryImportResponse)
async def import_library_path(
    payload: LibraryImportPathInput,
) -> LibraryImportResponse:
    try:
        result = library_store.import_archive_path(payload.path)
        return LibraryImportResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@library_router.get(
    "/library/protocol/{protocol_id}/preview",
    response_model=LibraryProtocolPreview,
)
async def preview_library_protocol(protocol_id: int) -> LibraryProtocolPreview:
    try:
        result = library_store.get_protocol_preview(protocol_id)
        return LibraryProtocolPreview.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@library_router.post("/library/protocol/{protocol_id}/load-workspace")
async def load_library_protocol_into_workspace(protocol_id: int) -> LibraryState:
    try:
        library_store.load_protocol_into_workspace(protocol_id)
        return LibraryState.model_validate(library_store.get_state())
    except ValueError as exc:
        status = 404 if "not found in the local library" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@library_router.get(
    "/library/record/{record_id}",
    response_model=LibraryRecordDetail,
)
async def get_library_record(record_id: int) -> LibraryRecordDetail:
    try:
        result = library_store.get_record_detail(record_id)
        return LibraryRecordDetail.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
