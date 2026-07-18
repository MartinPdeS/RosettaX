# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.ui import (
    WorkflowStep,
    build_workflow_page_header,
    build_workflow_progress_content,
)
from RosettaX.utils import styling

logger = logging.getLogger(__name__)


class Header:
    """
    Scattering calibration page header.

    Responsibilities
    ----------------
    - Explain the purpose of the scattering calibration page.
    - Show the calibration workflow before the user starts.
    - Clarify what each step produces.
    - Keep explanatory UX content separate from upload and processing logic.
    """

    def __init__(
        self,
        page: Any,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.card_color = card_color

        logger.debug(
            "Initialized Scattering Header section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering calibration header layout.
        """
        page_ids = getattr(self.page, "ids", None)
        state_ids = getattr(page_ids, "State", None)
        return build_workflow_page_header(
            title="Scattering calibration",
            description=(
                "Create a scattering calibration from bead FCS data by detecting bead populations, configuring the Mie model, computing coupling values, fitting the response, and saving the result for reuse."
            ),
            steps=self._build_steps(),
            progress_id=getattr(state_ids, "workflow_progress", None),
            card_color=self.card_color,
            column_kwargs={"xs": 12, "md": 6, "lg": 4, "xl": 2},
        )

    def register_callbacks(self) -> None:
        """
        Header section has no callbacks.
        """
        return None

    def _build_steps(self) -> list[WorkflowStep]:
        """
        Build the workflow step metadata.
        """
        return [
            WorkflowStep(
                "1", "Upload bead FCS",
                (
                    "Load the scattering bead file acquired on the instrument. "
                    "This file becomes the source for detector selection and peak detection."
                ),
                styling.get_workflow_section_color(1),
            ),
            WorkflowStep(
                "2", "Detect peaks",
                (
                    "Select the scattering detector channel, inspect the event distribution, "
                    "and detect the bead population peaks from the uploaded FCS file."
                ),
                styling.get_workflow_section_color(2),
            ),
            WorkflowStep(
                "3", "Define Mie model parameters",
                (
                    "Set the optical and particle model parameters, including wavelength, "
                    "medium refractive index, particle refractive index, and particle type."
                ),
                styling.get_workflow_section_color(3),
            ),
            WorkflowStep(
                "4", "Compute coupling",
                (
                    "Enter the particle diameters and compute the expected scattering "
                    "coupling from the selected Mie model."
                ),
                styling.get_workflow_section_color(4),
            ),
            WorkflowStep(
                "5", "Create calibration",
                (
                    "Match detected peak positions to the computed coupling values and fit "
                    "the scattering calibration relation."
                ),
                styling.get_workflow_section_color(5),
            ),
            WorkflowStep(
                "6", "Save calibration",
                (
                    "Save the fitted calibration so it can be reused later when applying "
                    "calibration to experimental FCS files."
                ),
                styling.get_workflow_section_color(6),
            ),
        ]

    def build_progress_content(self, page_state_payload: Any) -> dash.html.Div:
        """Build progress content from the serialized scattering page state."""
        state = page_state_payload if isinstance(page_state_payload, dict) else {}
        completed_count = 0
        if state.get("uploaded_fcs_path"):
            completed_count = 1
        peak_payload = state.get("scattering_peak_lines_payload") or state.get(
            "peak_lines_payload"
        )
        if completed_count == 1 and isinstance(peak_payload, dict) and peak_payload.get("positions"):
            completed_count = 2
        if completed_count == 2 and state.get("scattering_parameters_payload"):
            completed_count = 3
        if completed_count == 3 and state.get("calibration_graph_payload"):
            completed_count = 4
        if completed_count == 4 and state.get("calibration_payload"):
            completed_count = 5

        return build_workflow_progress_content(
            steps=self._build_steps(),
            completed_count=completed_count,
        )
