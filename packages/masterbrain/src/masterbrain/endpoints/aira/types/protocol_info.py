from typing import Optional

from pydantic import BaseModel


class ProtocolInfo(BaseModel):
    """
    Represents a single Airalogy Protocol's information in the Workflow.
    """

    airalogy_protocol_id: str
    """
    The ID of the Airalogy Protocol.
    """
    markdown: str
    """
    The Markdown for the Airalogy Protocol.
    """
    model: Optional[str] = None
    """
    The Model for the Airalogy Protocol.
    """
    assigner: Optional[str] = None
    """
    The Assigner for the Airalogy Protocol.
    """
    field_json_schema: Optional[dict] = None
    """
    The JSON Schema representing the Fields of the Airalogy Protocol, which can be generated from the Model.
    """
