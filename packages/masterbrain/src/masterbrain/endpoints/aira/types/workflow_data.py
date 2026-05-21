from pydantic import BaseModel, model_validator

from .path_data import PathData
from .protocol_info import ProtocolInfo
from .workflow_info import WorkflowInfo


class WorkflowData(BaseModel):
    """
    Represents the data for a Airalogy Protocol Workflow, including the Workflow information,
    the information for each protocol in the Workflow, and the Path data for the Workflow.
    """

    workflow_info: WorkflowInfo
    """
    The information for the Airalogy Protocol Workflow.
    """
    protocols_info: list[ProtocolInfo]
    """
    Dictionary of information for each protocol in the Airalogy Protocol Workflow.
    """
    path_data: PathData
    """
    The data for the Path of the Airalogy Protocol Workflow.
    """

    @model_validator(mode="after")
    def validate_protocol_ids_consistency(self):
        """
        Ensure `protocols_info.*.airalogy_protocol_id` matches exactly the set of
        `workflow_info.protocols.*.airalogy_protocol_id`.
        """
        # Collect IDs preserving potential duplicates
        info_ids_list = [p.airalogy_protocol_id for p in self.protocols_info]
        wf_ids_list = [n.airalogy_protocol_id for n in self.workflow_info.protocols]

        # Check 1 ##############################################################
        # Ensure there are no duplicate IDs in protocols_info
        dup_info = sorted(
            {pid for pid in info_ids_list if info_ids_list.count(pid) > 1}
        )
        if dup_info:
            raise ValueError(
                f"Duplicate airalogy_protocol_id in protocols_info: {dup_info}"
            )

        # Check 2 ##############################################################
        # Ensure the sets of IDs match exactly (order-independent)
        set_info = set(info_ids_list)
        set_wf = set(wf_ids_list)
        extra_in_info = sorted(set_info - set_wf)
        missing_in_info = sorted(set_wf - set_info)
        if extra_in_info or missing_in_info:
            details = []
            if missing_in_info:
                details.append(f"missing in protocols_info: {missing_in_info}")
            if extra_in_info:
                details.append(f"extra in protocols_info: {extra_in_info}")
            raise ValueError(
                "Mismatch between protocols_info.airalogy_protocol_id and workflow_info.protocols.airalogy_protocol_id; "
                + "; ".join(details)
            )

        return self
