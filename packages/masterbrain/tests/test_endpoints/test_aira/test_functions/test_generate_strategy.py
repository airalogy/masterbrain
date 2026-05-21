import pytest

from masterbrain.endpoints.aira.logic.functions.generate_strategy import (
    generate_strategy,
)
from masterbrain.endpoints.aira.types import SupportedModels
from masterbrain.endpoints.aira.types.steps import AddResearchStrategy, StrategyData
from masterbrain.endpoints.aira.types.workflow_data import WorkflowData


@pytest.mark.asyncio
async def test_generate_strategy_last_step_must_be_add_research_goal(
    workflow_info_json,
    protocols_info_json,
    path_data_waiting_for_strategy_researchable_json,
):
    with pytest.raises(AssertionError):
        workflow_data = WorkflowData(
            workflow_info=workflow_info_json,
            protocols_info=protocols_info_json,
            path_data=path_data_waiting_for_strategy_researchable_json,
        )
        workflow_data.path_data.steps.append(
            AddResearchStrategy(
                mode="user",
                data=StrategyData(thought="", researchable=True, strategy=""),
            )
        )
        await generate_strategy(workflow_data, debug=False)


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_generate_strategy_researchable(
    workflow_info_json,
    protocols_info_json,
    path_data_waiting_for_strategy_researchable_json,
    model,
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_strategy_researchable_json,
    )
    result = await generate_strategy(workflow_data, model=model)
    assert isinstance(result, StrategyData)
    assert result.researchable is True


@pytest.mark.asyncio
@pytest.mark.qwen
@pytest.mark.parametrize("model", SupportedModels.__args__)
async def test_generate_strategy_non_researchable(
    workflow_info_json,
    protocols_info_json,
    path_data_waiting_for_strategy_non_researchable_json,
    model,
):
    workflow_data = WorkflowData(
        workflow_info=workflow_info_json,
        protocols_info=protocols_info_json,
        path_data=path_data_waiting_for_strategy_non_researchable_json,
    )
    result = await generate_strategy(workflow_data, model=model)
    assert isinstance(result, StrategyData)
    assert result.researchable is False
