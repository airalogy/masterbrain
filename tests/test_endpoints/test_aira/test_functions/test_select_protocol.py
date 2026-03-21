import pytest

from masterbrain.endpoints.aira.logic.functions.select_protocol import select_protocol
from masterbrain.endpoints.aira.types import SupportedModels
from masterbrain.endpoints.aira.types.steps import NextProtocolData
from masterbrain.endpoints.aira.types.workflow_data import WorkflowData


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_select_protocol(
    workflow_info_json, protocols_info_json, path_data_waiting_for_protocol_json, model
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_protocol_json,
    )
    result = await select_protocol(workflow_data, model=model)
    assert isinstance(result, NextProtocolData)
    assert result.end_path is False
    assert result.protocol_index == 1


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_select_protocol_end_path(
    workflow_info_json,
    protocols_info_json,
    path_data_waiting_for_protocol_end_path_json,
    model,
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_protocol_end_path_json,
    )
    result = await select_protocol(workflow_data, model=model)
    assert isinstance(result, NextProtocolData)
    assert result.end_path is True
    assert result.protocol_index is None
