# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import plotly.graph_objs as go

from RosettaX.peak_workflow.core import graphing
from RosettaX.utils import plottings


logger = logging.getLogger(__name__)


def register_graph_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: Any,
    page_state_store_id: str,
    max_events_input_id: Any,
    runtime_config_store_id: str,
) -> None:
    """
    Register the main peak workflow graph callback.
    """
    state_components: list[Any] = [
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(
            ids.process_setting_pattern(),
            "id",
        ),
    ]

    if max_events_input_id is not None:
        state_components.append(
            dash.State(
                max_events_input_id,
                "value",
                allow_optional=True,
            )
        )

    state_components.append(
        dash.State(runtime_config_store_id, "data"),
    )

    @dash.callback(
        dash.Output(ids.graph_hist, "figure"),
        dash.Input(ids.graph_toggle_switch, "value"),
        dash.Input(ids.xscale_switch, "value"),
        dash.Input(ids.yscale_switch, "value"),
        dash.Input(page_state_store_id, "data"),
        dash.Input(ids.nbins_input, "value"),
        dash.Input(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.Input(ids.process_dropdown, "value"),
        dash.Input(
            ids.process_setting_pattern(),
            "value",
        ),
        *state_components,
        prevent_initial_call=False,
    )
    def update_graph(
        graph_toggle_value: Any,
        xscale_selection: Any,
        yscale_selection: Any,
        page_state_payload: Any,
        nbins: Any,
        detector_dropdown_values: list[Any],
        process_name: Any,
        process_setting_values: list[Any],
        detector_dropdown_ids: list[dict[str, Any]],
        process_setting_ids: list[dict[str, Any]],
        *state_values: Any,
    ) -> go.Figure:
        if max_events_input_id is not None:
            max_events_for_plots = state_values[0]
            runtime_config_data = state_values[1] if len(state_values) > 1 else None

        else:
            max_events_for_plots = None
            runtime_config_data = state_values[0] if state_values else None

        page_state = adapter.get_page_state_from_payload(
            page_state_payload,
        )

        uploaded_fcs_path = adapter.get_uploaded_fcs_path(
            page_state=page_state,
        )

        peak_lines_payload = adapter.get_peak_lines_payload(
            page_state=page_state,
        )

        backend = adapter.get_backend(
            page=page,
            uploaded_fcs_path=uploaded_fcs_path,
        )

        try:
            return graphing.build_peak_workflow_graph_figure(
                backend=backend,
                uploaded_fcs_path=uploaded_fcs_path,
                process_name=process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                process_setting_ids=process_setting_ids,
                process_setting_values=process_setting_values,
                graph_toggle_value=graph_toggle_value,
                xscale_selection=xscale_selection,
                yscale_selection=yscale_selection,
                nbins=nbins,
                peak_lines_payload=peak_lines_payload,
                max_events_for_plots=max_events_for_plots,
                runtime_config_data=runtime_config_data,
            )

        except Exception as exc:
            logger.exception("Failed to build peak workflow graph.")

            return plottings._make_info_figure(
                f"{type(exc).__name__}: {exc}",
            )