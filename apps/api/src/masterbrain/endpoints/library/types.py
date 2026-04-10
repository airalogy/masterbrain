from typing import Any, Literal

from pydantic import BaseModel, Field


class LibraryArchiveSummary(BaseModel):
    id: int
    source_name: str
    source_path: str | None = None
    kind: Literal["protocol", "records"]
    sha256: str
    imported_at: str
    protocol_count: int = 0
    record_count: int = 0


class LibraryProtocolSummary(BaseModel):
    id: int
    archive_id: int
    protocol_id: str | None = None
    protocol_version: str | None = None
    protocol_name: str
    entrypoint: str
    archive_root: str | None = None
    file_count: int = 0
    imported_at: str


class LibraryRecordSummary(BaseModel):
    id: int
    archive_id: int
    record_id: str | None = None
    record_version: str | None = None
    protocol_id: str | None = None
    protocol_version: str | None = None
    sha1: str | None = None
    source_path: str | None = None
    source_index: int
    embedded_protocol_root: str | None = None
    imported_at: str


class LibraryState(BaseModel):
    db_path: str
    archive_count: int = 0
    protocol_count: int = 0
    record_count: int = 0
    archives: list[LibraryArchiveSummary] = Field(default_factory=list)
    protocols: list[LibraryProtocolSummary] = Field(default_factory=list)
    records: list[LibraryRecordSummary] = Field(default_factory=list)


class LibraryImportResult(BaseModel):
    archive_id: int
    duplicate: bool
    source_name: str
    source_path: str | None = None
    kind: Literal["protocol", "records"]
    sha256: str
    imported_at: str
    protocol_count: int = 0
    record_count: int = 0


class LibraryImportResponse(BaseModel):
    result: LibraryImportResult
    state: LibraryState


class LibraryImportPathInput(BaseModel):
    path: str = Field(description="Absolute or user-expanded archive path")


class LibraryFilePreview(BaseModel):
    name: str
    path: str
    content: str
    type: Literal["aimd", "py", "other"]


class LibraryProtocolPreview(BaseModel):
    protocol: LibraryProtocolSummary
    files: list[LibraryFilePreview] = Field(default_factory=list)
    binary_file_count: int = 0
    total_file_count: int = 0


class LibraryRecordDetailPayload(BaseModel):
    id: int
    archive_id: int
    record_id: str | None = None
    record_version: str | None = None
    protocol_id: str | None = None
    protocol_version: str | None = None
    sha1: str | None = None
    source_path: str | None = None
    source_index: int
    embedded_protocol_root: str | None = None
    imported_at: str


class LibraryRecordDetail(BaseModel):
    record: LibraryRecordDetailPayload
    payload: dict[str, Any]
