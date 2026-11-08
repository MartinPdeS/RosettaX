import dash_bootstrap_components as dbc
from RosettaX.ui import WorkflowHeader, WorkflowStep

CALIBRATION_WORKFLOW = WorkflowHeader(
    title="Fluorescence calibration",
    description=(
        "Convert arbitrary units of fluorescence intensity into standard units "
        "(ABC, ERF, or MESF)."
    ),
    steps=(
        WorkflowStep(
            title="Upload bead FCS file",
            description="Load the FSC file of fluorescent reference beads. This FCS file becomes the source for parameter selection and detection of fluorescence peaks.",
        ),
        WorkflowStep(
            title="Detect fluorescence peaks",
            description="Select the parameter to calibrate, inspect the event distribution, and detect the fluorescence bead populations from the uploaded FCS file.",
        ),
        WorkflowStep(
            title="Add standard units to calibration table",
            description="Add standard units (ABC, ERF, MESF) to the calibration table. The provided values define the calibrated fluorescence scale.",
        ),
        WorkflowStep(
            title="Create calibration",
            description="Relate arbitrary units of fluorescence intensity to standard units by fitting the calibration table data.",
        ),
        WorkflowStep(
            title="Save calibration",
            description="Save the calibration for later reuse when applying it to uncalibrated FCS files.",
        ),
    ),
    column_kwargs={"xl": True},
)


def get_layout(section) -> dbc.Card:
    """Build the fluorescence calibration workflow header."""
    page_ids = getattr(getattr(section, "page", None), "ids", None)
    state_ids = getattr(page_ids, "State", None)
    return CALIBRATION_WORKFLOW.build_header(
        progress_id=getattr(state_ids, "workflow_progress", None),
        step_target_page_name=getattr(page_ids, "page_name", None),
        card_color=section.card_color,
        description_tooltip_target_id=state_ids.description_tooltip_target,
        description_tooltip_id=state_ids.description_tooltip,
    )
