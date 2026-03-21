import pytest

from masterbrain.endpoints.aira.logic.functions.generate_final_conclusion import (
    generate_final_conclusion,
)
from masterbrain.endpoints.aira.types import SupportedModels
from masterbrain.endpoints.aira.types.steps import ConclusionData
from masterbrain.endpoints.aira.types.workflow_data import WorkflowData


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_generate_final_conclusion(
    workflow_info_json,
    protocols_info_json,
    path_data_waiting_for_final_conclusion_json,
    model,
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_final_conclusion_json,
    )
    result = await generate_final_conclusion(workflow_data, model=model)
    assert isinstance(result, ConclusionData)
    assert result.conclusion != ""
