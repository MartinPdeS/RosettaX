# -*- coding: utf-8 -*-

import dash


def register_callbacks(section) -> None:
    """
    Register callbacks for the scattering s00_header section.
    """
    @dash.callback(
        dash.Output(section.page.ids.State.workflow_progress, "children"),
        dash.Input(section.page.ids.State.page_state_store, "data"),
        dash.Input(section.page.ids.Parameters.detector_configuration_preset, "value"),
        dash.Input(section.page.ids.Parameters.detector_configuration_model, "value"),
        dash.Input(section.page.ids.Parameters.detector_configuration_type, "value"),
        prevent_initial_call=False,
    )
    def update_workflow_progress(
        page_state_payload,
        detector_configuration_preset,
        detector_configuration_model,
        detector_configuration_type,
    ):
        return section.build_progress_content(
            page_state_payload,
            detector_configuration_values=(
                detector_configuration_preset,
                detector_configuration_model,
                detector_configuration_type,
            ),
        )
