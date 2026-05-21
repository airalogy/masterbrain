from pydantic import BaseModel

from ..configs import DEFAULT_MODEL


class Model(BaseModel):
    """
    The data model for the model.
    """

    name: str = DEFAULT_MODEL
    """
    The name of the model to use.
    E.g. "qwen3.5-flash"
    """
    enable_thinking: bool = False
    """
    If true, the model will think before answering.
    """
