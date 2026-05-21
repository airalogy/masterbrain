import re
from typing import Annotated, Optional

from pydantic import BaseModel, Field, model_validator

EdgeInt = Annotated[str, Field(pattern=r"^\d+( -> | <-> )\d+$")]
"""
Custom type for EdgeStr that represents a directed edge between two protocols.
The format is "from_protocol_index -> to_protocol_index" or "from_protocol_index <-> to_protocol_index".
"""


# Define the model for nodes, containing a snake_case-compliant ID and a name
class ProtocolIndexNameId(BaseModel):
    """
    Represents a protocol within the workflow, with an ID that must follow snake_case format
    and a descriptive name for the protocol.
    """

    protocol_index: int = Field(ge=1, description="int, start from 1")
    """
    The first protocol in the workflow, start from 1.
    """

    protocol_name: str
    """
    A descriptive name for the protocol.
    """

    airalogy_protocol_id: str
    """
    The global unique Airalogy Protocol ID for the Protocol.
    """


# Define the Workflow information model
class WorkflowInfo(BaseModel):
    """
    Represents the information for a Airalogy Protocol Workflow.
    """

    id: str
    """
    A unique identifier for the workflow.
    """

    title: str
    """
    Title for the Airalogy Protocol Workflow.
    """

    protocols: list[ProtocolIndexNameId]
    """
    list of Airalogy Protocol Nodes that make up the Airalogy Protocol Workflow.
    """

    edges: list[EdgeInt]
    """
    list of directed edges representing transitions between Airalogy Protocols.
    """

    logic: str
    """
    A description of the logical rules for the Airalogy Protocol Workflow.
    """

    default_initial_protocol_index: Optional[int] = None
    """
    The default initial protocol for the Airalogy Protocol Workflow.
    """

    default_research_goal: Optional[str] = None
    """
    The default research purpose for the Airalogy Protocol Workflow.
    """

    default_research_strategy: Optional[str] = None
    """
    The default research strategy for the Airalogy Protocol Workflow.
    """

    @model_validator(mode="after")
    def check_protocol_indexes(self):
        """
        Validates the protocol indexes in the `edges` are present in the `protocols` list.
        """
        protocol_indexes = {
            protocol.protocol_index for protocol in self.protocols
        }  # Use self to access protocols and edges after validation

        # Check 1 ##############################################################
        # Ensure protocol indexes in protocols are unique
        if len(protocol_indexes) != len(self.protocols):
            raise ValueError("Protocol indexes in protocols must be unique.")

        # Check 2 ##############################################################
        # Ensure protocol indexes are sequential starting from 1
        if not all(
            index in protocol_indexes for index in range(1, len(protocol_indexes) + 1)
        ):
            raise ValueError(
                "Protocol indexes in protocols must be sequential starting from 1."
            )

        # Check 3 ##############################################################
        # Ensure all protocols in edges exist in the protocol list
        for edge in self.edges:
            from_protocol, to_protocol = re.split(r" -> | <-> ", edge)
            if (
                int(from_protocol) not in protocol_indexes
                or int(to_protocol) not in protocol_indexes
            ):
                raise ValueError(
                    f"Edge contains protocols not found in protocols list: {edge}"
                )

        # Check 4 ##############################################################
        # Ensure default_initial_protocol_index exists in protocols
        if (
            self.default_initial_protocol_index
            and self.default_initial_protocol_index not in protocol_indexes
        ):
            raise ValueError(
                f"default_initial_protocol_index '{self.default_initial_protocol_index}' is not in protocols list."
            )

        # Return ###############################################################
        return self

    def protocol_indexes(self) -> set[int]:
        """
        Returns a set of protocol indexes in the workflow.
        """
        return {protocol.protocol_index for protocol in self.protocols}

    def get_airalogy_protocol_id_by_protocol_index(self, protocol_index: int) -> str:
        """
        Returns the Airalogy Protocol ID for a given protocol index.
        If the protocol index does not exist, returns None.
        """
        protocol_indexes = self.protocol_indexes()
        if protocol_index not in protocol_indexes:
            raise ValueError(f"Protocol index '{protocol_index}' not found.")

        for protocol in self.protocols:
            if protocol.protocol_index == protocol_index:
                return protocol.airalogy_protocol_id

        raise ValueError(
            f"Airalogy Protocol ID not found for protocol index '{protocol_index}'."
        )
