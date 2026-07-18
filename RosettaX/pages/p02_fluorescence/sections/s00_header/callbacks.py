# -*- coding: utf-8 -*-

import dash

from RosettaX.ui import build_workflow_progress_content
from .layout import _build_steps


def register_callbacks(section) -> None:
    """
    Register the fluorescence workflow progress callback.
    """
    @dash.callback(
        dash.Output(section.page.ids.State.workflow_progress, "children"),
        dash.Input(section.page.ids.State.page_state_store, "data"),
        prevent_initial_call=False,
    )
    def update_workflow_progress(page_state_payload):
        state = page_state_payload if isinstance(page_state_payload, dict) else {}
        completed_count = 0
        if state.get("uploaded_fcs_path"):
            completed_count = 1
        peak_payload = state.get("peak_lines_payload") or {}
        if completed_count == 1 and (
            state.get("fluorescence_peak_lines")
            or peak_payload.get("positions")
        ):
            completed_count = 2
        if completed_count == 2 and state.get("reference_table_rows"):
            completed_count = 3
        if completed_count == 3 and state.get("calibration_payload"):
            completed_count = 4

        return build_workflow_progress_content(
            steps=_build_steps(),
            completed_count=completed_count,
        )
