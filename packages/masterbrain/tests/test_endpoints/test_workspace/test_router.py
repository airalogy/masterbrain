"""Router tests for the workspace endpoint."""

import io
import hashlib
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


def test_workspace_mutations_apply_as_one_change_set(
    client: TestClient,
    workspace_root,
):
    protocol = workspace_root / "protocol.aimd"
    protocol.write_text("# Before", encoding="utf-8")
    response = client.post(
        "/api/endpoints/workspace/mutations",
        json={
            "change_set_id": "sha256:test",
            "operation": "apply",
            "mutations": [
                {
                    "path": "protocol.aimd",
                    "type": "aimd",
                    "status": "modified",
                    "content": "# After",
                    "expected_hash": hashlib.sha256(b"# Before").hexdigest(),
                },
                {
                    "path": "model.py",
                    "type": "py",
                    "status": "created",
                    "content": "value = 1\n",
                    "expected_hash": None,
                },
            ],
        },
    )

    assert response.status_code == 200
    assert protocol.read_text(encoding="utf-8") == "# After"
    assert (workspace_root / "model.py").read_text(encoding="utf-8") == "value = 1\n"


def test_workspace_mutations_reject_stale_hash_without_partial_writes(
    client: TestClient,
    workspace_root,
):
    protocol = workspace_root / "protocol.aimd"
    protocol.write_text("# Local change", encoding="utf-8")
    response = client.post(
        "/api/endpoints/workspace/mutations",
        json={
            "operation": "apply",
            "mutations": [
                {
                    "path": "model.py",
                    "type": "py",
                    "status": "created",
                    "content": "value = 1\n",
                    "expected_hash": None,
                },
                {
                    "path": "protocol.aimd",
                    "type": "aimd",
                    "status": "modified",
                    "content": "# AI change",
                    "expected_hash": hashlib.sha256(b"# Request snapshot").hexdigest(),
                },
            ],
        },
    )

    assert response.status_code == 409
    assert protocol.read_text(encoding="utf-8") == "# Local change"
    assert not (workspace_root / "model.py").exists()


def test_workspace_mutations_reject_modifying_a_missing_file(
    client: TestClient,
    workspace_root,
):
    response = client.post(
        "/api/endpoints/workspace/mutations",
        json={
            "operation": "apply",
            "mutations": [
                {
                    "path": "model.py",
                    "type": "py",
                    "status": "modified",
                    "content": "value = 1\n",
                    "expected_hash": None,
                },
            ],
        },
    )

    assert response.status_code == 409
    assert not (workspace_root / "model.py").exists()


def test_workspace_mutations_reject_creating_an_existing_file(
    client: TestClient,
    workspace_root,
):
    model = workspace_root / "model.py"
    model.write_text("value = 1\n", encoding="utf-8")
    response = client.post(
        "/api/endpoints/workspace/mutations",
        json={
            "operation": "apply",
            "mutations": [
                {
                    "path": "model.py",
                    "type": "py",
                    "status": "created",
                    "content": "value = 2\n",
                    "expected_hash": hashlib.sha256(b"value = 1\n").hexdigest(),
                },
            ],
        },
    )

    assert response.status_code == 409
    assert model.read_text(encoding="utf-8") == "value = 1\n"
