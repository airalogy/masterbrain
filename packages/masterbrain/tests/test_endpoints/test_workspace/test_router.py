"""Router tests for the workspace endpoint."""

import io
import zipfile

from fastapi.testclient import TestClient


def _build_zip_payload() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("protocol.aimd", "step x")
        archive.writestr("assets/sample.bin", b"\x00\x01\x02")
        archive.writestr("empty/", b"")
    return buffer.getvalue()


def test_workspace_state_reports_selected_directory(
    client: TestClient,
    workspace_root,
):
    response = client.get("/api/endpoints/workspace")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "directory"
    assert payload["has_workspace"] is True
    assert payload["root_path"] == str(workspace_root)
    assert payload["entry_count"] == 0
    assert payload["files"] == []
    assert payload["folders"] == []


def test_workspace_zip_import_and_export_round_trip(
    client: TestClient,
    workspace_root,
):
    import_response = client.post(
        "/api/endpoints/workspace/import-zip",
        content=_build_zip_payload(),
        headers={"Content-Type": "application/zip"},
    )

    assert import_response.status_code == 200
    imported = import_response.json()
    assert imported["entry_count"] == 4
    assert imported["folders"] == ["assets", "empty"]
    assert [item["path"] for item in imported["files"]] == ["protocol.aimd"]

    export_response = client.get("/api/endpoints/workspace/export-zip")

    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "application/zip"
    assert "filename=" in export_response.headers["content-disposition"]

    archive = zipfile.ZipFile(io.BytesIO(export_response.content))
    assert sorted(archive.namelist()) == [
        "assets/sample.bin",
        "empty/",
        "protocol.aimd",
    ]
