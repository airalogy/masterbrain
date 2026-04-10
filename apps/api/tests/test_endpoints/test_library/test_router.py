"""Router tests for the local library endpoints."""

import json
from pathlib import Path

from airalogy.archive import pack_protocol_archive, pack_records_archive
from fastapi.testclient import TestClient


def _build_protocol_dir(root: Path, *, name: str) -> Path:
    protocol_dir = root / name
    protocol_dir.mkdir()
    (protocol_dir / "protocol.aimd").write_text(
        "# Cell Growth\n\n{{step|seed}}\nMeasure cells.\n",
        encoding="utf-8",
    )
    (protocol_dir / "model.py").write_text(
        "from pydantic import BaseModel\n\nclass Record(BaseModel):\n    cells: int\n",
        encoding="utf-8",
    )
    (protocol_dir / "protocol.toml").write_text(
        """
[airalogy_protocol]
id = "airalogy.id.demo.protocol"
version = "0.0.1"
name = "Cell Growth"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return protocol_dir


def test_import_protocol_archive_preview_and_load_workspace(
    client: TestClient,
    library_db_path,
    workspace_root: Path,
    tmp_path: Path,
):
    protocol_dir = _build_protocol_dir(tmp_path, name="cell_growth")
    archive_path = pack_protocol_archive(protocol_dir, tmp_path / "cell_growth.aira")

    response = client.post(
        "/api/endpoints/library/import-path",
        json={"path": str(archive_path)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["duplicate"] is False
    assert payload["result"]["kind"] == "protocol"
    assert payload["state"]["archive_count"] == 1
    assert payload["state"]["protocol_count"] == 1
    assert payload["state"]["record_count"] == 0

    protocol_id = payload["state"]["protocols"][0]["id"]
    preview_response = client.get(
        f"/api/endpoints/library/protocol/{protocol_id}/preview"
    )

    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["protocol"]["protocol_name"] == "Cell Growth"
    assert sorted(file["path"] for file in preview["files"]) == [
        "model.py",
        "protocol.aimd",
        "protocol.toml",
    ]

    load_response = client.post(
        f"/api/endpoints/library/protocol/{protocol_id}/load-workspace"
    )
    assert load_response.status_code == 200
    assert (workspace_root / "protocol.aimd").read_text(encoding="utf-8").startswith(
        "# Cell Growth"
    )
    assert (workspace_root / "model.py").exists()


def test_import_records_archive_and_read_record_detail(
    client: TestClient,
    library_db_path,
    tmp_path: Path,
):
    protocol_dir = _build_protocol_dir(tmp_path, name="embedded_protocol")
    record_path = tmp_path / "record.json"
    record_path.write_text(
        json.dumps(
            {
                "record_id": "airalogy.id.demo.record",
                "record_version": "0.0.2",
                "metadata": {
                    "protocol_id": "airalogy.id.demo.protocol",
                    "protocol_version": "0.0.1",
                    "sha1": "abc123",
                },
                "fields": {"cells": 42},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    archive_path = pack_records_archive(
        [record_path],
        tmp_path / "records.aira",
        protocol_dirs=[protocol_dir],
    )

    import_response = client.post(
        f"/api/endpoints/library/import-aira?source_name={archive_path.name}&source_path={archive_path}",
        content=archive_path.read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )

    assert import_response.status_code == 200
    imported = import_response.json()
    assert imported["result"]["kind"] == "records"
    assert imported["state"]["archive_count"] == 1
    assert imported["state"]["protocol_count"] == 1
    assert imported["state"]["record_count"] == 1

    protocol_id = imported["state"]["protocols"][0]["id"]
    preview_response = client.get(
        f"/api/endpoints/library/protocol/{protocol_id}/preview"
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert any(file["path"] == "protocol.aimd" for file in preview["files"])

    record_id = imported["state"]["records"][0]["id"]
    detail_response = client.get(f"/api/endpoints/library/record/{record_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["record"]["record_id"] == "airalogy.id.demo.record"
    assert detail["payload"]["fields"]["cells"] == 42
