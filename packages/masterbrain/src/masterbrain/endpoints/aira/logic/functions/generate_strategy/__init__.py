__all__ = ["generate_strategy"]

from pathlib import Path
from string import Template

from masterbrain.configs import DASHSCOPE_CLIENT, DEBUG
from masterbrain.endpoints.aira.types import DEFAULT_MODEL, WorkflowData
from masterbrain.endpoints.aira.types.steps import StrategyData
from masterbrain.utils.print import print_with_border

CURRENT_DIR = Path(__file__).resolve().parent

PROMPT_PATH = CURRENT_DIR / "prompt.md"

PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


async def generate_strategy(
    workflow_data: WorkflowData, model: str = DEFAULT_MODEL, debug: bool = DEBUG
) -> StrategyData:
    assert workflow_data.path_data.path_status == "waiting_for_research_strategy", (
        "Workflow path status must be 'waiting_for_research_strategy'."
    )
    # assert last step is "add_research_goal"
    assert workflow_data.path_data.steps[-1].step == "add_research_goal", (
        "Last step must be 'add_research_goal'."
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
        print_with_border(f"Generated strategy data:\n{content}")
    assert isinstance(content, str), "Expected content to be a string."

    strategy_data = StrategyData.model_validate_json(content)

    return strategy_data
