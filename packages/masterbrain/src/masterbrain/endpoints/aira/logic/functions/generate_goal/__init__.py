__all__ = ["generate_goal"]

from pathlib import Path
from string import Template

from masterbrain.configs import DASHSCOPE_CLIENT, DEBUG
from masterbrain.endpoints.aira.types import DEFAULT_MODEL, WorkflowData
from masterbrain.endpoints.aira.types.steps import GoalData
from masterbrain.utils.print import print_with_border

CURRENT_DIR = Path(__file__).resolve().parent

PROMPT_PATH = CURRENT_DIR / "prompt.md"

PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


async def generate_goal(
    workflow_data: WorkflowData, model: str = DEFAULT_MODEL, debug: bool = DEBUG
) -> GoalData:
    assert workflow_data.path_data.path_status == "waiting_for_research_goal", (
        "Workflow path status must be 'waiting_for_research_goal'."
    )

    prompt = Template(PROMPT_TEMPLATE).substitute(
        workflow_data=workflow_data.model_dump_json(),
    )

    if debug:
        print_with_border(f"Prompt:\n{prompt}")

    completion = await DASHSCOPE_CLIENT.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content

    if debug:
        print_with_border(f"Generated goal data:\n{content}")
    assert isinstance(content, str), "Expected content to be a string."

    goal_data = GoalData.model_validate_json(content)

    return goal_data
