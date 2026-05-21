from typing import Any, Literal

from pydantic import BaseModel, model_validator

type AiUser = Literal["ai", "user"]


# Research Goal ################################################################
class GoalData(BaseModel):
    thought: str = ""
    goal: str


class AddResearchGoal(BaseModel):
    step: Literal["add_research_goal"] = "add_research_goal"
    path_index: int = 0
    mode: AiUser
    data: GoalData


# Research Strategy ############################################################
class StrategyData(BaseModel):
    thought: str = ""
    researchable: bool
    strategy: str


class AddResearchStrategy(BaseModel):
    step: Literal["add_research_strategy"] = "add_research_strategy"
    path_index: int = 0
    mode: AiUser
    data: StrategyData


# Next Protocol ################################################################
class NextProtocolData(BaseModel):
    thought: str = ""
    end_path: bool
    protocol_index: int | None

    # If `end_path` is True, `protocol_index` should be None; if `end_path` is False, `protocol_index` should not be None
    @model_validator(mode="after")
    def check_end_path_and_protocol_index(self):
        # If end_path is True, protocol_index must be None
        if self.end_path and self.protocol_index is not None:
            raise ValueError("protocol_index must be None if end_path is True")
        # If end_path is False, protocol_index must not be None
        if not self.end_path and self.protocol_index is None:
            raise ValueError("protocol_index must be provided if end_path is False")
        return self


class AddNextProtocol(BaseModel):
    step: Literal["add_next_protocol"] = "add_next_protocol"
    path_index: int
    mode: AiUser
    data: NextProtocolData


# Values for Fields in Next Protocol ###########################################
class ValuesData(BaseModel):
    thought: str
    values: dict[str, Any]


class AddInitialValuesForFieldsInNextProtocol(BaseModel):
    step: Literal["add_initial_values_for_fields_in_next_protocol"] = (
        "add_initial_values_for_fields_in_next_protocol"
    )
    path_index: int
    mode: AiUser
    data: ValuesData


# Record #######################################################################
class RecordProtocolData(BaseModel):
    protocol_index: int
    airalogy_record_id: str
    record_data: dict
    """
    Note: This field will not be saved in the database record of a Workflow's Record. This is because the corresponding Record data can be retrieved from the database using `airalogy_record_id`, so there is no need to store it again. The reason for defining this field in Masterbrain is to make it convenient for AI methods in AIRA to directly access the Record data. Therefore, when passing AIRA's Input from the Airalogy platform to this endpoint, the Record data retrieved using `airalogy_record_id` must be pre-filled into this field.
    """


class AddProtocol(BaseModel):
    step: Literal["add_record"] = "add_record"
    path_index: int
    mode: AiUser
    data: RecordProtocolData


# Phased Research Conclusion ###################################################
class ConclusionData(BaseModel):
    conclusion: str


class AddPhasedResearchConclusion(BaseModel):
    step: Literal["add_phased_research_conclusion"] = "add_phased_research_conclusion"
    path_index: int
    mode: AiUser
    data: ConclusionData


# Final Research Conclusion ###################################################
class AddFinalResearchConclusion(BaseModel):
    step: Literal["add_final_research_conclusion"] = "add_final_research_conclusion"
    path_index: int
    mode: AiUser
    data: ConclusionData


# AddStep ######################################################################

type AddStep = (
    AddResearchGoal
    | AddResearchStrategy
    | AddNextProtocol
    | AddInitialValuesForFieldsInNextProtocol
    | AddProtocol
    | AddPhasedResearchConclusion
    | AddFinalResearchConclusion
)
