# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash_bootstrap_components as dbc

from RosettaX.ui import WorkflowStep, build_workflow_page_header
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
        return build_workflow_page_header(
            title="Scattering calibration",
            description=(
                "Create a scattering calibration from bead FCS data by detecting bead populations, configuring the Mie model, computing coupling values, fitting the response, and saving the result for reuse."
            ),
            steps=self._build_steps(),
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
