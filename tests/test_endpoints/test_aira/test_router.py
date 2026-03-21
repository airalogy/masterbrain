import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from masterbrain.endpoints.aira.router import aira_router

AIRAINPUT_DIR = Path(__file__).parent / "json" / "aira_input"


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(aira_router, prefix="/api/endpoints", tags=["AIRA"])
    return TestClient(app)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


CLIENT = _build_client()


@pytest.mark.qwen
def test_aira_input_for_goal():
    payload = _load(AIRAINPUT_DIR / "aira_input_for_goal.json")

    wf = payload["workflow_data"]
    status = wf["path_data"]["path_status"]
    assert status == "waiting_for_research_goal"
    steps = wf["path_data"].get("steps", [])
    last_path_index = steps[-1]["path_index"] if steps else 0

    resp = CLIENT.post("/api/endpoints/aira", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["step"] == "add_research_goal"
    assert body["mode"] == "ai"
    assert body["path_index"] == last_path_index
    assert isinstance(body["data"].get("goal"), str) and body["data"]["goal"].strip()


@pytest.mark.qwen
def test_aira_input_for_strategy():
    payload = _load(AIRAINPUT_DIR / "aira_input_for_strategy.json")

    wf = payload["workflow_data"]
    status = wf["path_data"]["path_status"]
    assert status == "waiting_for_research_strategy"
    steps = wf["path_data"].get("steps", [])
    last_path_index = steps[-1]["path_index"] if steps else 0

    resp = CLIENT.post("/api/endpoints/aira", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["step"] == "add_research_strategy"
    assert body["mode"] == "ai"
    assert body["path_index"] == last_path_index
    assert (
        isinstance(body["data"].get("strategy"), str)
        and body["data"]["strategy"].strip()
    )
    assert isinstance(body["data"].get("researchable"), bool)


@pytest.mark.qwen
def test_aira_input_for_protocol():
    payload = _load(AIRAINPUT_DIR / "aira_input_for_protocol.json")

    wf = payload["workflow_data"]
    status = wf["path_data"]["path_status"]
    assert status == "waiting_for_next_protocol"
    steps = wf["path_data"].get("steps", [])
    last_path_index = steps[-1]["path_index"] if steps else 0

    resp = CLIENT.post("/api/endpoints/aira", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["step"] == "add_next_protocol"
    assert body["mode"] == "ai"
    assert body["path_index"] == last_path_index + 1
    end_path = body["data"].get("end_path")
    if end_path:
        assert body["data"].get("protocol_index") is None
    else:
        assert isinstance(body["data"].get("protocol_index"), int)


@pytest.mark.qwen
def test_aira_input_for_values():
    payload = _load(AIRAINPUT_DIR / "aira_input_for_values.json")

    wf = payload["workflow_data"]
    status = wf["path_data"]["path_status"]
    assert status == "waiting_for_initial_values_for_fields_in_next_protocol"
    steps = wf["path_data"].get("steps", [])
    last_path_index = steps[-1]["path_index"] if steps else 0

    resp = CLIENT.post("/api/endpoints/aira", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["step"] == "add_initial_values_for_fields_in_next_protocol"
    assert body["mode"] == "ai"
    assert body["path_index"] == last_path_index
    assert isinstance(body["data"].get("values"), dict)


@pytest.mark.qwen
def test_aira_input_for_phased_conclusion():
    payload = _load(AIRAINPUT_DIR / "aira_input_for_phased_conclusion.json")

    wf = payload["workflow_data"]
    status = wf["path_data"]["path_status"]
    assert status == "waiting_for_phased_research_conclusion"
    steps = wf["path_data"].get("steps", [])
    last_path_index = steps[-1]["path_index"] if steps else 0

    resp = CLIENT.post("/api/endpoints/aira", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["step"] == "add_phased_research_conclusion"
    assert body["mode"] == "ai"
    assert body["path_index"] == last_path_index
    assert (
        isinstance(body["data"].get("conclusion"), str)
        and body["data"]["conclusion"].strip()
    )


@pytest.mark.qwen
def test_aira_input_for_final_conclusion():
    payload = _load(AIRAINPUT_DIR / "aira_input_for_final_conclusion.json")

    wf = payload["workflow_data"]
    status = wf["path_data"]["path_status"]
    assert status == "waiting_for_final_research_conclusion"
    steps = wf["path_data"].get("steps", [])
    last_path_index = steps[-1]["path_index"] if steps else 0

    resp = CLIENT.post("/api/endpoints/aira", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["step"] == "add_final_research_conclusion"
    assert body["mode"] == "ai"
    assert body["path_index"] == last_path_index
    assert (
        isinstance(body["data"].get("conclusion"), str)
        and body["data"]["conclusion"].strip()
    )
