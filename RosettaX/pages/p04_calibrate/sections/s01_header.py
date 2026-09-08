# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
import dash

from RosettaX.ui import WorkflowStep, build_workflow_page_header, build_workflow_step_cards
from RosettaX.utils import styling


class Header:
    def __init__(
        self,
        page,
        card_color: str = "green",
    ) -> None:
        self.page = page
        self.card_color = card_color

    def get_layout(self) -> dbc.Card:
        return build_workflow_page_header(
            title="Apply calibration",
            description=(
                "Use this page when you already have a saved calibration and want to apply it to one or more FCS files. Select the calibration payload, upload the target files, choose the relevant detector mapping, and export calibrated outputs."
            ),
            steps=self._build_steps(),
            card_color=self.card_color,
            component_id=self.page.ids.Header.container,
            progress_id=self.page.ids.Header.workflow_progress,
            step_target_page_name=self.page.ids.page_name,
            column_kwargs={"lg": 4},
        )

    def register_callbacks(self) -> None:
        """
        Update the workflow cards from the shared apply-page state.
        """
        @dash.callback(
            dash.Output(self.page.ids.Header.workflow_progress, "children"),
            dash.Input(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=False,
        )
        def update_progress(state):
            data = state if isinstance(state, dict) else {}
            completed = 0
            if data.get("selected_calibration_path"):
                completed = 1
            if completed == 1 and data.get("uploaded_fcs_path"):
                completed = 2
            if completed == 2 and data.get("apply_result_payload"):
                completed = 3
            return build_workflow_step_cards(
                steps=self._build_steps(), completed_count=completed,
                page_name=self.page.ids.page_name, column_kwargs={"lg": 4},
            )

    def _build_steps(self) -> list[WorkflowStep]:
        """
        Build the apply calibration workflow step metadata.
        """
        return [
            WorkflowStep(
                "1", "Select calibration",
                (
                    "Choose the saved fluorescence or scattering calibration JSON "
                    "that will be applied to the uploaded data. For scattering "
                    "payloads, confirm the target particle model before continuing."
                ),
                styling.get_workflow_section_color(1),
            ),
            WorkflowStep(
                "2", "Upload input FCS",
                (
                    "Load one or more experimental FCS files that should receive "
                    "the calibrated output channels."
                ),
                styling.get_workflow_section_color(2),
            ),
            WorkflowStep(
                "3", "Apply and export",
                (
                    "Choose optional extra raw channels to preserve, run the "
                    "calibration, and download the calibrated export package."
                ),
                styling.get_workflow_section_color(3),
            ),
        ]
