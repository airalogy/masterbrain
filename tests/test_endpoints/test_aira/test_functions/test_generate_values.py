import pytest

from masterbrain.endpoints.aira.logic.functions.generate_values import generate_values
from masterbrain.endpoints.aira.types import SupportedModels
from masterbrain.endpoints.aira.types.steps import ValuesData
from masterbrain.endpoints.aira.types.workflow_data import WorkflowData


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_generate_values(
    workflow_info_json, protocols_info_json, path_data_waiting_for_values_json, model
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_values_json,
    )
    result = await generate_values(workflow_data, model=model)
    assert isinstance(result, ValuesData)
