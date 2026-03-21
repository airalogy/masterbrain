import json
from pathlib import Path

import pytest

JSON_DIR = Path(__file__).parent / "json"


@pytest.fixture
def workflow_info_json():
    json_path = JSON_DIR / "workflow_info.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def protocols_info_json():
    json_path = JSON_DIR / "protocols_info.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_goal_json():
    json_path = JSON_DIR / "path_data_waiting_for_goal.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_strategy_researchable_json():
    json_path = JSON_DIR / "path_data_waiting_for_strategy_researchable.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_strategy_non_researchable_json():
    json_path = JSON_DIR / "path_data_waiting_for_strategy_non_researchable.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_protocol_json():
    json_path = JSON_DIR / "path_data_waiting_for_protocol.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_protocol_end_path_json():
    json_path = JSON_DIR / "path_data_waiting_for_protocol_end_path.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_values_json():
    json_path = JSON_DIR / "path_data_waiting_for_values.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_phased_conclusion_json():
    json_path = JSON_DIR / "path_data_waiting_for_phased_conclusion.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def path_data_waiting_for_final_conclusion_json():
    json_path = JSON_DIR / "path_data_waiting_for_final_conclusion.json"
    return json.loads(json_path.read_text(encoding="utf-8"))
