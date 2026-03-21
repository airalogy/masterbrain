import pytest

from masterbrain.endpoints.aira.logic.functions.generate_goal import generate_goal
from masterbrain.endpoints.aira.types import SupportedModels
from masterbrain.endpoints.aira.types.steps import GoalData
from masterbrain.endpoints.aira.types.workflow_data import WorkflowData


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_generate_goal(
    workflow_info_json, protocols_info_json, path_data_waiting_for_goal_json, model
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_goal_json,
    )
    result = await generate_goal(workflow_data, model=model)
    assert isinstance(result, GoalData)
