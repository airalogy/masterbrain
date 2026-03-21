__all__ = ["generate_final_conclusion"]

from pathlib import Path
from string import Template

from masterbrain.configs import DASHSCOPE_CLIENT, DEBUG
from masterbrain.endpoints.aira.types import DEFAULT_MODEL, WorkflowData
from masterbrain.endpoints.aira.types.steps import ConclusionData
from masterbrain.utils.print import print_with_border

CURRENT_DIR = Path(__file__).resolve().parent

PROMPT_PATH = CURRENT_DIR / "prompt.md"

PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


async def generate_final_conclusion(
    workflow_data: WorkflowData, model: str = DEFAULT_MODEL, debug: bool = DEBUG
) -> ConclusionData:
    assert (
        workflow_data.path_data.path_status == "waiting_for_final_research_conclusion"
    ), "Workflow path status must be 'waiting_for_final_research_conclusion'."

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
    )

    content = completion.choices[0].message.content

    if debug:
        print_with_border(f"Generated final conclusion data:\n{content}")
    assert isinstance(content, str), "Expected content to be a string."

    return ConclusionData(
        conclusion=content,
    )
