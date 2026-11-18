import dash_bootstrap_components as dbc
from RosettaX.ui import WorkflowHeader, WorkflowStep


def build_workflow(*, workflow_steps: list[WorkflowStep]) -> WorkflowHeader:
    """Build the fluorescence header from its ordered sections."""
    return WorkflowHeader(
        title="Fluorescence calibration",
        description=(
            "Convert arbitrary units of fluorescence intensity into standard units "
            "(ABC, ERF, or MESF)."
        ),
        steps=workflow_steps,
        column_kwargs={"xl": True},
    )

def get_layout(section) -> dbc.Card:
    """Build the fluorescence calibration workflow header."""
    page_ids = getattr(getattr(section, "page", None), "ids", None)
    state_ids = getattr(page_ids, "State", None)
    workflow_header = getattr(section, "workflow_header", None)
    if workflow_header is None:
        from ..services import SECTION_TYPES

        workflow_header = build_workflow(
            workflow_steps=[section_type.workflow_step for section_type in SECTION_TYPES],
        )
    return workflow_header.build_header(
        progress_id=getattr(state_ids, "workflow_progress", None),
        step_target_page_name=getattr(page_ids, "page_name", None),
        card_color=section.card_color,
        description_tooltip_target_id=getattr(
            state_ids,
            "description_tooltip_target",
            None,
        ),
        description_tooltip_id=getattr(state_ids, "description_tooltip", None),
    )
