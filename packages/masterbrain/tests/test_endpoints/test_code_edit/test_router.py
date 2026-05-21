"""Router tests for the code edit endpoint."""

from fastapi.testclient import TestClient

from masterbrain.endpoints.code_edit.types import CodeEditOutput


def test_code_edit_endpoint_returns_expected_structure(
    client: TestClient,
    sample_code_edit_input: dict,
    monkeypatch,
):
    async def fake_generate_code_edit_result(_payload):
        return CodeEditOutput(
            message="Changed one file.",
            edit_status="changed",
            changed_files=[
                {
                    "path": "protocol.aimd",
                    "name": "protocol.aimd",
                    "type": "aimd",
                    "status": "modified",
                    "content": "# Updated protocol",
                    "diff": "--- a/protocol.aimd\n+++ b/protocol.aimd\n@@\n-# Old\n+# Updated protocol",
                }
            ],
            warnings=[],
            execution_log=[
                "Created OpenCode session session-123.",
                "Detected 1 supported file change(s): protocol.aimd (modified).",
            ],
        )

    monkeypatch.setattr(
        "masterbrain.endpoints.code_edit.router.generate_code_edit_result",
        fake_generate_code_edit_result,
    )

    response = client.post("/api/endpoints/code_edit", json=sample_code_edit_input)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["runtime"] == "opencode"
    assert response_data["message"] == "Changed one file."
    assert response_data["edit_status"] == "changed"
    assert len(response_data["changed_files"]) == 1
    assert response_data["changed_files"][0]["path"] == "protocol.aimd"
    assert response_data["warnings"] == []
    assert len(response_data["execution_log"]) == 2
