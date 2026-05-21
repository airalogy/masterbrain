"""
FastAPI Router for AIRA (AI Research Automation) endpoint.
"""

__all__ = [
    "aira_router",
]

from fastapi import APIRouter

from masterbrain.configs import DEBUG
from masterbrain.endpoints.aira.logic.functions import (
    generate_final_conclusion,
    generate_goal,
    generate_phased_conclusion,
    generate_strategy,
    generate_values,
    select_protocol,
)
from masterbrain.endpoints.aira.types import AiraInput, AiraOutput
from masterbrain.endpoints.aira.types.steps import (
    AddFinalResearchConclusion,
    AddInitialValuesForFieldsInNextProtocol,
    AddNextProtocol,
    AddPhasedResearchConclusion,
    AddResearchGoal,
    AddResearchStrategy,
)
from masterbrain.utils.print import print_with_border

aira_router = APIRouter()


@aira_router.post("/aira")
async def post_aira(aira_input: AiraInput) -> AiraOutput:
    model = aira_input.model
    workflow_data = aira_input.workflow_data

    if DEBUG:
        print_with_border("FastAPI Router (aira) workflow_data:\n", workflow_data)

    async def execute_function():
        last_path_index = (
            workflow_data.path_data.steps[-1].path_index
            if workflow_data.path_data.steps
            else 0
        )
        match workflow_data.path_data.path_status:
            case "waiting_for_research_goal":
                return AddResearchGoal(
                    path_index=last_path_index,
                    mode="ai",
                    data=await generate_goal(
                        workflow_data=workflow_data,
                        model=model,
                    ),
                )

            case "waiting_for_research_strategy":
                return AddResearchStrategy(
                    path_index=last_path_index,
                    mode="ai",
                    data=await generate_strategy(
                        workflow_data=workflow_data,
                        model=model,
                    ),
                )
            case "waiting_for_next_protocol":
                return AddNextProtocol(
                    path_index=last_path_index + 1,
                    mode="ai",
                    data=await select_protocol(
                        workflow_data=workflow_data,
                        model=model,
                    ),
                )
            case "waiting_for_initial_values_for_fields_in_next_protocol":
                return AddInitialValuesForFieldsInNextProtocol(
                    path_index=last_path_index,
                    mode="ai",
                    data=await generate_values(
                        workflow_data=workflow_data,
                        model=model,
                    ),
                )
            case "waiting_for_phased_research_conclusion":
                return AddPhasedResearchConclusion(
                    path_index=last_path_index,
                    mode="ai",
                    data=await generate_phased_conclusion(
                        workflow_data=workflow_data,
                        model=model,
                    ),
                )
            case "waiting_for_final_research_conclusion":
                return AddFinalResearchConclusion(
                    path_index=last_path_index,
                    mode="ai",
                    data=await generate_final_conclusion(
                        workflow_data=workflow_data,
                        model=model,
                    ),
                )
            case _:
                raise ValueError(
                    f"Invalid path status for AIRA endpoint: {workflow_data.path_data.path_status}"
                )

    response = await execute_function()

    if DEBUG:
        print_with_border(f"\nFastAPI Router (aira) response:\n{response}")

    return response
