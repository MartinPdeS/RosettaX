import dash
import dash_bootstrap_components as dbc
from RosettaX.ui import (
    WorkflowHeader,
    WorkflowStep,
)


class Header:
    def __init__(
        self,
        page,
        card_color: str = "green",
        *,
        workflow_steps: list[WorkflowStep] | None = None,
    ) -> None:
        self.page = page
        self.card_color = card_color
        if workflow_steps is None:
            from .services import SECTION_TYPES

            workflow_steps = [section_type.workflow_step for section_type in SECTION_TYPES]
        self.workflow_header = WorkflowHeader(
            title="Apply calibration",
            description=(
                "Use this page when you already have a saved calibration and want to apply it to one or more FCS files. Select the calibration payload, upload the target files, choose the relevant detector mapping, and export calibrated outputs."
            ),
            steps=workflow_steps,
            card_color=card_color,
            column_kwargs={"lg": 4},
        )

    def get_layout(self) -> dbc.Card:
        return self.workflow_header.build_header(
            component_id=self.page.ids.Header.container,
            progress_id=self.page.ids.Header.workflow_progress,
            step_target_page_name=self.page.ids.page_name,
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
            return self.workflow_header.build_progress(
                completed_count=completed,
                page_name=self.page.ids.page_name,
            )
