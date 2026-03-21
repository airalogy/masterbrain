from typing import Literal

from pydantic import BaseModel

from .steps import AddStep


class PathData(BaseModel):
    """
    Main model for the path data.
    """

    path_status: Literal[
        "completed",
        "waiting_for_research_goal",
        "waiting_for_research_strategy",
        "end_after_generating_research_strategy",
        "waiting_for_next_protocol",
        "end_after_selecting_next_protocol",
        "waiting_for_initial_values_for_fields_in_next_protocol",
        "waiting_for_record",
        "waiting_for_phased_research_conclusion",
        "waiting_for_final_research_conclusion",
    ]

    steps: list[AddStep]
