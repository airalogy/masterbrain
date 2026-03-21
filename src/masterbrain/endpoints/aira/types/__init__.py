__all__ = [
    "AiraInput",
    "AiraOutput",
]


from typing import Literal

from pydantic import BaseModel

from .steps import AddStep
from .workflow_data import WorkflowData

SupportedModels = Literal["qwen3.5-flash", "qwen3.5-plus", "qwen3-max"]
DEFAULT_MODEL = "qwen3.5-flash"


class AiraInput(BaseModel):
    """
    AIRA endpoint input data model.
    """

    model: SupportedModels = DEFAULT_MODEL
    workflow_data: WorkflowData


type AiraOutput = AddStep
