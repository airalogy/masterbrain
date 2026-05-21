"""Local archive library for protocol and record imports."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import shutil
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
from typing import Any, Iterator

from airalogy.archive import ArchiveError, read_archive_manifest, unpack_archive

from masterbrain.workspace_manager import detect_type, workspace_manager

MAX_PREVIEW_FILE_SIZE_BYTES = 1_000_000


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _resolve_default_library_db_path() -> Path:
    override = os.getenv("MASTERBRAIN_LIBRARY_DB")
    if override:
        return Path(override).expanduser().resolve()

    if os.name == "nt":
        base_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return (base_dir / "Masterbrain" / "library.db").resolve()

    if sys.platform == "darwin":
        return (Path.home() / "Library" / "Application Support" / "Masterbrain" / "library.db").resolve()

    xdg_home = os.getenv("XDG_DATA_HOME")
    base_dir = Path(xdg_home).expanduser() if xdg_home else Path.home() / ".local" / "share"
    return (base_dir / "masterbrain" / "library.db").resolve()


def _looks_like_text_file(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_PREVIEW_FILE_SIZE_BYTES:
            return False
        with path.open("rb") as handle:
            sample = handle.read(2048)
    except OSError:
        return False

    return b"\x00" not in sample


class LibraryStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._db_path: Path | None = None

    def get_db_path(self) -> Path:
        with self._lock:
            if self._db_path is None:
                self._db_path = _resolve_default_library_db_path()
            path = self._db_path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def set_db_path(self, path_like: str | Path) -> Path:
        path = Path(path_like).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._db_path = path
        return path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.get_db_path())
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        self._ensure_schema(connection)
        try:
            yield connection
        finally:
            connection.close()

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha256 TEXT NOT NULL UNIQUE,
                source_name TEXT NOT NULL,
                source_path TEXT,
                kind TEXT NOT NULL CHECK (kind IN ('protocol', 'records')),
                imported_at TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                payload BLOB NOT NULL
            );

            CREATE TABLE IF NOT EXISTS protocols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archive_id INTEGER NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
                protocol_id TEXT,
                protocol_version TEXT,
                protocol_name TEXT NOT NULL,
                entrypoint TEXT NOT NULL,
                archive_root TEXT,
                file_count INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL,
                imported_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archive_id INTEGER NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
                record_id TEXT,
                record_version TEXT,
                protocol_id TEXT,
                protocol_version TEXT,
                sha1 TEXT,
                source_path TEXT,
                source_index INTEGER NOT NULL,
                embedded_protocol_root TEXT,
                payload_json TEXT NOT NULL,
                imported_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_protocols_archive_id ON protocols(archive_id);
            CREATE INDEX IF NOT EXISTS idx_protocols_lookup ON protocols(protocol_id, protocol_version);
            CREATE INDEX IF NOT EXISTS idx_records_archive_id ON records(archive_id);
            CREATE INDEX IF NOT EXISTS idx_records_lookup ON records(protocol_id, protocol_version);
            """
        )
        conn.commit()

    def _parse_archive_payload(self, payload: bytes) -> dict[str, Any]:
        with TemporaryDirectory(prefix="masterbrain-aira-") as temp_dir:
            temp_root = Path(temp_dir)
            archive_path = temp_root / "import.aira"
            archive_path.write_bytes(payload)
            manifest = read_archive_manifest(archive_path)
            unpack_dir, manifest = unpack_archive(
                archive_path,
                temp_root / "unpacked",
            )

            protocol_rows: list[dict[str, Any]] = []
            record_rows: list[dict[str, Any]] = []

            if manifest["kind"] == "protocol":
                protocol = manifest["protocol"]
                protocol_rows.append(
                    {
                        "protocol_id": protocol.get("protocol_id"),
                        "protocol_version": protocol.get("protocol_version"),
                        "protocol_name": protocol.get("protocol_name") or "Protocol",
                        "entrypoint": protocol.get("entrypoint") or "protocol.aimd",
                        "archive_root": None,
                        "file_count": len(protocol.get("files") or []),
                        "metadata_json": _json_dumps(protocol),
                    }
                )
            else:
                for protocol in manifest.get("protocols", []):
                    protocol_rows.append(
                        {
                            "protocol_id": protocol.get("protocol_id"),
                            "protocol_version": protocol.get("protocol_version"),
                            "protocol_name": protocol.get("protocol_name") or "Protocol",
                            "entrypoint": protocol.get("entrypoint") or "protocol.aimd",
                            "archive_root": protocol.get("archive_root"),
                            "file_count": len(protocol.get("files") or []),
                            "metadata_json": _json_dumps(protocol),
                        }
                    )

                for record in manifest.get("records", []):
                    record_path = unpack_dir / record["path"]
                    try:
                        payload_json = json.loads(record_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError) as exc:
                        raise ArchiveError(
                            f"Record payload '{record_path}' inside archive is not valid JSON."
                        ) from exc

                    record_rows.append(
                        {
                            "record_id": record.get("record_id"),
                            "record_version": record.get("record_version"),
                            "protocol_id": record.get("protocol_id"),
                            "protocol_version": record.get("protocol_version"),
                            "sha1": record.get("sha1"),
                            "source_path": record.get("source_path"),
                            "source_index": int(record.get("source_index") or 0),
                            "embedded_protocol_root": record.get("embedded_protocol_root"),
                            "payload_json": _json_dumps(payload_json),
                        }
                    )

            return {
                "manifest": manifest,
                "protocol_rows": protocol_rows,
                "record_rows": record_rows,
            }

    def import_archive_bytes(
        self,
        payload: bytes,
        *,
        source_name: str,
        source_path: str | None = None,
    ) -> dict[str, Any]:
        if not payload:
            raise ValueError("Archive payload is empty.")

        sha256 = hashlib.sha256(payload).hexdigest()
        parsed = self._parse_archive_payload(payload)
        imported_at = _utc_now_iso()

        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT id, kind, imported_at FROM archives WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
            if existing is not None:
                conn.execute(
                    """
                    UPDATE archives
                    SET source_name = ?, source_path = ?
                    WHERE id = ?
                    """,
                    (source_name, source_path, existing["id"]),
                )
                conn.commit()
                return self._build_import_response(
                    conn,
                    archive_id=int(existing["id"]),
                    duplicate=True,
                )

            cursor = conn.execute(
                """
                INSERT INTO archives (
                    sha256, source_name, source_path, kind, imported_at, manifest_json, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sha256,
                    source_name,
                    source_path,
                    parsed["manifest"]["kind"],
                    imported_at,
                    _json_dumps(parsed["manifest"]),
                    payload,
                ),
            )
            archive_id = int(cursor.lastrowid)

            for protocol in parsed["protocol_rows"]:
                conn.execute(
                    """
                    INSERT INTO protocols (
                        archive_id,
                        protocol_id,
                        protocol_version,
                        protocol_name,
                        entrypoint,
                        archive_root,
                        file_count,
                        metadata_json,
                        imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        archive_id,
                        protocol["protocol_id"],
                        protocol["protocol_version"],
                        protocol["protocol_name"],
                        protocol["entrypoint"],
                        protocol["archive_root"],
                        protocol["file_count"],
                        protocol["metadata_json"],
                        imported_at,
                    ),
                )

            for record in parsed["record_rows"]:
                conn.execute(
                    """
                    INSERT INTO records (
                        archive_id,
                        record_id,
                        record_version,
                        protocol_id,
                        protocol_version,
                        sha1,
                        source_path,
                        source_index,
                        embedded_protocol_root,
                        payload_json,
                        imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        archive_id,
                        record["record_id"],
                        record["record_version"],
                        record["protocol_id"],
                        record["protocol_version"],
                        record["sha1"],
                        record["source_path"],
                        record["source_index"],
                        record["embedded_protocol_root"],
                        record["payload_json"],
                        imported_at,
                    ),
                )

            conn.commit()
            return self._build_import_response(
                conn,
                archive_id=archive_id,
                duplicate=False,
            )

    def import_archive_path(self, path_like: str | Path) -> dict[str, Any]:
        path = Path(path_like).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Archive file does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"Archive path must be a file: {path}")
        return self.import_archive_bytes(
            path.read_bytes(),
            source_name=path.name,
            source_path=str(path),
        )

    def _build_import_response(
        self,
        conn: sqlite3.Connection,
        *,
        archive_id: int,
        duplicate: bool,
    ) -> dict[str, Any]:
        archive_row = conn.execute(
            """
            SELECT
                a.id,
                a.source_name,
                a.source_path,
                a.kind,
                a.sha256,
                a.imported_at,
                (
                    SELECT COUNT(*)
                    FROM protocols p
                    WHERE p.archive_id = a.id
                ) AS protocol_count,
                (
                    SELECT COUNT(*)
                    FROM records r
                    WHERE r.archive_id = a.id
                ) AS record_count
            FROM archives a
            WHERE a.id = ?
            """,
            (archive_id,),
        ).fetchone()

        if archive_row is None:
            raise ValueError(f"Imported archive row {archive_id} was not found.")

        return {
            "result": {
                "archive_id": int(archive_row["id"]),
                "duplicate": duplicate,
                "source_name": archive_row["source_name"],
                "source_path": archive_row["source_path"],
                "kind": archive_row["kind"],
                "sha256": archive_row["sha256"],
                "imported_at": archive_row["imported_at"],
                "protocol_count": int(archive_row["protocol_count"]),
                "record_count": int(archive_row["record_count"]),
            },
            "state": self.get_state(limit=50, conn=conn),
        }

    def get_state(
        self,
        *,
        limit: int = 50,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._get_state_from_connection(conn, limit=limit)
        with self._connect() as local_conn:
            return self._get_state_from_connection(local_conn, limit=limit)

    def _get_state_from_connection(
        self,
        conn: sqlite3.Connection,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:
        archive_count = int(
            conn.execute("SELECT COUNT(*) FROM archives").fetchone()[0]
        )
        protocol_count = int(
            conn.execute("SELECT COUNT(*) FROM protocols").fetchone()[0]
        )
        record_count = int(
            conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        )

        archive_rows = conn.execute(
            """
            SELECT
                a.id,
                a.source_name,
                a.source_path,
                a.kind,
                a.sha256,
                a.imported_at,
                (
                    SELECT COUNT(*)
                    FROM protocols p
                    WHERE p.archive_id = a.id
                ) AS protocol_count,
                (
                    SELECT COUNT(*)
                    FROM records r
                    WHERE r.archive_id = a.id
                ) AS record_count
            FROM archives a
            ORDER BY a.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        protocol_rows = conn.execute(
            """
            SELECT
                p.id,
                p.archive_id,
                p.protocol_id,
                p.protocol_version,
                p.protocol_name,
                p.entrypoint,
                p.archive_root,
                p.file_count,
                p.imported_at
            FROM protocols p
            ORDER BY p.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        record_rows = conn.execute(
            """
            SELECT
                r.id,
                r.archive_id,
                r.record_id,
                r.record_version,
                r.protocol_id,
                r.protocol_version,
                r.sha1,
                r.source_path,
                r.source_index,
                r.embedded_protocol_root,
                r.imported_at
            FROM records r
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return {
            "db_path": str(self.get_db_path()),
            "archive_count": archive_count,
            "protocol_count": protocol_count,
            "record_count": record_count,
            "archives": [
                {
                    "id": int(row["id"]),
                    "source_name": row["source_name"],
                    "source_path": row["source_path"],
                    "kind": row["kind"],
                    "sha256": row["sha256"],
                    "imported_at": row["imported_at"],
                    "protocol_count": int(row["protocol_count"]),
                    "record_count": int(row["record_count"]),
                }
                for row in archive_rows
            ],
            "protocols": [
                {
                    "id": int(row["id"]),
                    "archive_id": int(row["archive_id"]),
                    "protocol_id": row["protocol_id"],
                    "protocol_version": row["protocol_version"],
                    "protocol_name": row["protocol_name"],
                    "entrypoint": row["entrypoint"],
                    "archive_root": row["archive_root"],
                    "file_count": int(row["file_count"]),
                    "imported_at": row["imported_at"],
                }
                for row in protocol_rows
            ],
            "records": [
                {
                    "id": int(row["id"]),
                    "archive_id": int(row["archive_id"]),
                    "record_id": row["record_id"],
                    "record_version": row["record_version"],
                    "protocol_id": row["protocol_id"],
                    "protocol_version": row["protocol_version"],
                    "sha1": row["sha1"],
                    "source_path": row["source_path"],
                    "source_index": int(row["source_index"]),
                    "embedded_protocol_root": row["embedded_protocol_root"],
                    "imported_at": row["imported_at"],
                }
                for row in record_rows
            ],
        }

    @contextmanager
    def _materialize_protocol_archive(
        self,
        protocol_row_id: int,
    ) -> Iterator[tuple[sqlite3.Row, Path]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    p.id,
                    p.archive_id,
                    p.protocol_id,
                    p.protocol_version,
                    p.protocol_name,
                    p.entrypoint,
                    p.archive_root,
                    p.file_count,
                    p.imported_at,
                    a.kind AS archive_kind,
                    a.payload
                FROM protocols p
                JOIN archives a ON a.id = p.archive_id
                WHERE p.id = ?
                """,
                (protocol_row_id,),
            ).fetchone()

            if row is None:
                raise ValueError(f"Protocol {protocol_row_id} was not found in the local library.")

            payload = bytes(row["payload"])

        with TemporaryDirectory(prefix="masterbrain-protocol-") as temp_dir:
            temp_root = Path(temp_dir)
            archive_path = temp_root / "protocol.aira"
            archive_path.write_bytes(payload)
            unpack_dir, _ = unpack_archive(
                archive_path,
                temp_root / "unpacked",
            )

            if row["archive_kind"] == "protocol":
                protocol_root = unpack_dir
                metadata_dir = protocol_root / "_airalogy_archive"
                if metadata_dir.exists():
                    shutil.rmtree(metadata_dir)
            else:
                archive_root = row["archive_root"]
                if not archive_root:
                    raise ValueError(
                        f"Embedded protocol {protocol_row_id} does not declare an archive root."
                    )
                protocol_root = unpack_dir / archive_root

            if not protocol_root.exists() or not protocol_root.is_dir():
                raise ValueError(
                    f"Protocol files for library item {protocol_row_id} could not be materialized."
                )

            yield row, protocol_root

    def get_protocol_preview(self, protocol_row_id: int) -> dict[str, Any]:
        with self._materialize_protocol_archive(protocol_row_id) as (row, protocol_root):
            files: list[dict[str, Any]] = []
            binary_file_count = 0
            total_file_count = 0

            for path in sorted(protocol_root.rglob("*")):
                if not path.is_file():
                    continue
                total_file_count += 1
                rel_path = path.relative_to(protocol_root).as_posix()
                if not _looks_like_text_file(path):
                    binary_file_count += 1
                    continue
                files.append(
                    {
                        "name": path.name,
                        "path": rel_path,
                        "content": path.read_text(encoding="utf-8", errors="ignore"),
                        "type": detect_type(path.name),
                    }
                )

            return {
                "protocol": {
                    "id": int(row["id"]),
                    "archive_id": int(row["archive_id"]),
                    "protocol_id": row["protocol_id"],
                    "protocol_version": row["protocol_version"],
                    "protocol_name": row["protocol_name"],
                    "entrypoint": row["entrypoint"],
                    "archive_root": row["archive_root"],
                    "file_count": int(row["file_count"]),
                    "imported_at": row["imported_at"],
                },
                "files": files,
                "binary_file_count": binary_file_count,
                "total_file_count": total_file_count,
            }

    def load_protocol_into_workspace(self, protocol_row_id: int) -> None:
        with self._materialize_protocol_archive(protocol_row_id) as (_, protocol_root):
            workspace_manager.replace_with_directory(protocol_root)

    def get_record_detail(self, record_row_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id,
                    archive_id,
                    record_id,
                    record_version,
                    protocol_id,
                    protocol_version,
                    sha1,
                    source_path,
                    source_index,
                    embedded_protocol_root,
                    payload_json,
                    imported_at
                FROM records
                WHERE id = ?
                """,
                (record_row_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Record {record_row_id} was not found in the local library.")

        return {
            "record": {
                "id": int(row["id"]),
                "archive_id": int(row["archive_id"]),
                "record_id": row["record_id"],
                "record_version": row["record_version"],
                "protocol_id": row["protocol_id"],
                "protocol_version": row["protocol_version"],
                "sha1": row["sha1"],
                "source_path": row["source_path"],
                "source_index": int(row["source_index"]),
                "embedded_protocol_root": row["embedded_protocol_root"],
                "imported_at": row["imported_at"],
            },
            "payload": json.loads(row["payload_json"]),
        }


library_store = LibraryStore()
