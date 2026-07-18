# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc

from RosettaX.ui import WorkflowStep, build_workflow_page_header
from RosettaX.utils import styling


def get_layout(section) -> dbc.Card:
    """Build the fluorescence calibration workflow header."""
    page_ids = getattr(getattr(section, "page", None), "ids", None)
    state_ids = getattr(page_ids, "State", None)
    return build_workflow_page_header(
        title="Fluorescence calibration",
        description=(
            "Convert arbitrary units of fluorescence intensity into standard units (ABC, ERF, or MESF)."
        ),
        steps=_build_steps(),
        progress_id=getattr(state_ids, "workflow_progress", None),
        card_color=section.card_color,
        column_kwargs={"xl": True},
    )


def _build_steps() -> list[WorkflowStep]:
    """Build the fluorescence calibration workflow steps."""
    return [
        WorkflowStep(
            "1",
            "Upload bead FCS file",
            "Load the FSC file of fluorescent reference beads. This FCS file becomes the source for parameter selection and detection of fluorescence peaks.",
            styling.get_workflow_section_color(1),
        ),
        WorkflowStep(
            "2",
            "Detect fluorescence peaks",
            "Select the parameter to calibrate, inspect the event distribution, and detect the fluorescence bead populations from the uploaded FCS file.",
            styling.get_workflow_section_color(2),
        ),
        WorkflowStep(
            "3",
            "Add standard units to calibration table",
            "Add standard units (ABC, ERF, MESF) to the calibration table. The provided values define the calibrated fluorescence scale.",
            styling.get_workflow_section_color(3),
        ),
        WorkflowStep(
            "4",
            "Create calibration",
            "Relate arbitrary units of fluorescence intensity to standard units by fitting the calibration table data.",
            styling.get_workflow_section_color(4),
        ),
        WorkflowStep(
            "5",
            "Save calibration",
            "Save the calibration for later reuse when applying it to uncalibrated FCS files.",
            styling.get_workflow_section_color(5),
        ),
    ]
