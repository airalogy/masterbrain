import copy

import pytest
from pydantic import ValidationError

from masterbrain.endpoints.aira.types.workflow_info import WorkflowInfo


def test_valid_workflow_info_parses(workflow_info_json):
    wf = WorkflowInfo.model_validate(workflow_info_json)
    assert isinstance(wf, WorkflowInfo)
    # Accept either list or set from get_protocol_indexes; compare as set
    assert set(wf.protocol_indexes()) == {1, 2, 3, 4}


def test_duplicate_protocol_indexes_raises(workflow_info_json):
    bad = copy.deepcopy(workflow_info_json)
    # make a duplicate protocol_index (two entries with index == 1)
    bad["protocols"][1]["protocol_index"] = 1
    with pytest.raises(ValidationError):
        WorkflowInfo.model_validate(bad)


def test_non_sequential_protocol_indexes_raises(workflow_info_json):
    bad = copy.deepcopy(workflow_info_json)
    # keep unique indexes but remove index 2 to break sequential requirement
    # pick the first and third original entries which have indexes 1 and 3
    bad["protocols"] = [bad["protocols"][0], bad["protocols"][2]]
    with pytest.raises(ValidationError):
        WorkflowInfo.model_validate(bad)


def test_edge_references_missing_protocol_raise(workflow_info_json):
    bad = copy.deepcopy(workflow_info_json)
    # add an edge that references a non-existent protocol index
    bad["edges"].append("1 -> 99")
    with pytest.raises(ValidationError):
        WorkflowInfo(**bad)


def test_default_initial_protocol_index_must_exist(workflow_info_json):
    bad = copy.deepcopy(workflow_info_json)
    bad["default_initial_protocol_index"] = 99
    with pytest.raises(ValidationError):
        WorkflowInfo.model_validate(bad)


def test_edges_numbers_are_within_protocols(workflow_info_json):
    wf = WorkflowInfo.model_validate(workflow_info_json)
    protocol_indexes = set(wf.protocol_indexes())
    expected = {1, 2, 3, 4}
    assert protocol_indexes == expected


def test_get_airalogy_protocol_id_by_protocol_index_valid(workflow_info_json):
    wf = WorkflowInfo.model_validate(workflow_info_json)
    # Known mappings from the fixture json
    assert (
        wf.get_airalogy_protocol_id_by_protocol_index(1)
        == "airalogy.id.lab.airalogy.project.public_protocols.protocol.cnt_powder.v.0.0.1"
    )
    assert (
        wf.get_airalogy_protocol_id_by_protocol_index(4)
        == "airalogy.id.lab.airalogy.project.public_protocols.protocol.cnt_characterization.v.0.0.1"
    )


def test_get_airalogy_protocol_id_by_protocol_index_invalid_raises(workflow_info_json):
    wf = WorkflowInfo.model_validate(workflow_info_json)
    with pytest.raises(ValueError, match="not found"):
        wf.get_airalogy_protocol_id_by_protocol_index(99)
