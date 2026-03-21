__all__ = ["select_protocol"]

from pathlib import Path
from string import Template

from masterbrain.configs import DASHSCOPE_CLIENT, DEBUG
from masterbrain.endpoints.aira.types import DEFAULT_MODEL, WorkflowData
from masterbrain.endpoints.aira.types.steps import NextProtocolData
from masterbrain.utils.print import print_with_border

CURRENT_DIR = Path(__file__).resolve().parent

PROMPT_PATH = CURRENT_DIR / "prompt.md"

PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


async def select_protocol(
    workflow_data: WorkflowData, model: str = DEFAULT_MODEL, debug: bool = DEBUG
) -> NextProtocolData:
    assert workflow_data.path_data.path_status == "waiting_for_next_protocol", (
        "Workflow path status must be 'waiting_for_next_protocol'."
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
        print_with_border(f"Selected next protocol data:\n{content}")
    assert isinstance(content, str), "Expected content to be a string."

    next_protocol_data = NextProtocolData.model_validate_json(content)

    return next_protocol_data
