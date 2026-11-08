import dash
import dash_bootstrap_components as dbc
import logging
from . import callbacks
from RosettaX.ui import (
    WorkflowHeader,
    WorkflowStep,
)
from typing import Any

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
        self.workflow_header = WorkflowHeader(
            title="Scattering calibration",
            description=(
                "Create a scattering calibration from bead FCS data by detecting bead populations, configuring the Mie model, computing coupling values, fitting the response, and saving the result for reuse."
            ),
            steps=self._build_steps(),
            card_color=card_color,
            column_kwargs={"xs": 12, "md": 6, "lg": 4, "xl": 2},
        )

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
        return self.workflow_header.build_header(
            progress_id=getattr(state_ids, "workflow_progress", None),
            step_target_page_name=getattr(page_ids, "page_name", None),
            description_tooltip_target_id=page_ids.State.description_tooltip_target,
            description_tooltip_id=page_ids.State.description_tooltip,
        )

    def register_callbacks(self) -> None:
        """
        Register the live workflow progress callback.
        """
        callbacks.register_callbacks(self)

    def _build_steps(self) -> list[WorkflowStep]:
        """
        Build the workflow step metadata.
        """
        return [
            WorkflowStep(
                title="Upload bead FCS",
                description=(
                    "Load the scattering bead file acquired on the instrument. "
                    "This file becomes the source for detector selection and peak detection."
                ),
            ),
            WorkflowStep(
                title="Detect peaks",
                description=(
                    "Select the scattering detector channel, inspect the event distribution, "
                    "and detect the bead population peaks from the uploaded FCS file."
                ),
            ),
            WorkflowStep(
                title="Configure detector",
                description=(
                    "Choose the scattering detector channel used for the calibration workflow."
                ),
            ),
            WorkflowStep(
                title="Compute coupling",
                description=(
                    "Enter the particle diameters and compute the expected scattering "
                    "coupling from the selected Mie model."
                ),
            ),
            WorkflowStep(
                title="Create calibration",
                description=(
                    "Match detected peak positions to the computed coupling values and fit "
                    "the scattering calibration relation."
                ),
            ),
            WorkflowStep(
                title="Save calibration",
                description=(
                    "Save the fitted calibration so it can be reused later when applying "
                    "calibration to experimental FCS files."
                ),
            ),
        ]

    def build_progress_content(
        self,
        page_state_payload: Any,
        *,
        detector_configuration_values: Any = None,
    ) -> dash.html.Div:
        """Build progress content from the serialized scattering page state."""
        state = page_state_payload if isinstance(page_state_payload, dict) else {}
        completed_count = 0
        if state.get("uploaded_fcs_path"):
            completed_count = 1
        peak_payload = self._find_completed_peak_payload(state)
        if (
            completed_count == 1
            and isinstance(peak_payload, dict)
            and peak_payload.get("positions")
        ):
            completed_count = 2
        detector_configured = _has_complete_detector_configuration(
            detector_configuration_values,
        )
        if completed_count == 2 and detector_configured:
            completed_count = 3
        if completed_count == 3 and (
            state.get("calibration_model_graph_payload")
            or state.get("calibration_graph_payload")
        ):
            completed_count = 4
        if completed_count == 4 and state.get("calibration_payload"):
            completed_count = 5
        if completed_count == 5 and state.get("calibration_saved"):
            completed_count = 6

        return self.workflow_header.build_progress(
            completed_count=completed_count,
            page_name=self.page.ids.page_name,
        )

    @staticmethod
    def _find_completed_peak_payload(state: dict) -> dict:
        """Return the first scattering peak payload containing positions."""
        for field_name in (
            "scattering_peak_lines_payload",
            "peak_lines_payload",
        ):
            payload = state.get(field_name)
            if isinstance(payload, dict) and payload.get("positions"):
                return payload
        return {}


def _has_complete_detector_configuration(values: Any) -> bool:
    """Return whether the preset, model, and detector type are all filled."""
    if not isinstance(values, (list, tuple)):
        return False
    return len(values) == 3 and all(str(value or "").strip() for value in values)
