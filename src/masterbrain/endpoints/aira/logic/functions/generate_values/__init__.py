__all__ = ["generate_values"]

from pathlib import Path
from string import Template

from masterbrain.configs import DASHSCOPE_CLIENT, DEBUG
from masterbrain.endpoints.aira.types import DEFAULT_MODEL, WorkflowData
from masterbrain.endpoints.aira.types.steps import AddNextProtocol, ValuesData
from masterbrain.utils.print import print_with_border

CURRENT_DIR = Path(__file__).resolve().parent

PROMPT_PATH = CURRENT_DIR / "prompt.md"

PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


async def generate_values(
    workflow_data: WorkflowData, model: str = DEFAULT_MODEL, debug: bool = DEBUG
) -> ValuesData:
    assert (
        workflow_data.path_data.path_status
        == "waiting_for_initial_values_for_fields_in_next_protocol"
    ), (
        "Workflow path status must be 'waiting_for_initial_values_for_fields_in_next_protocol'."
    )
    last_step = workflow_data.path_data.steps[-1]
    assert isinstance(last_step, AddNextProtocol), (
        "Last step must be an AddNextProtocol."
    )
    next_protocol_index = last_step.data.protocol_index
    assert next_protocol_index is not None, "Next protocol index must be an integer."
    airalogy_protocol_id = (
        workflow_data.workflow_info.get_airalogy_protocol_id_by_protocol_index(
            next_protocol_index
        )
    )

    prompt = Template(PROMPT_TEMPLATE).substitute(
        workflow_data=workflow_data.model_dump_json(),
        airalogy_protocol_id=airalogy_protocol_id,
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
        print_with_border(f"Values data:\n{content}")
    assert isinstance(content, str), "Expected content to be a string."

    values_data = ValuesData.model_validate_json(content)

    return values_data
