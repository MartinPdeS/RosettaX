# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import plotly.graph_objs as go

from RosettaX.pages.p02_fluorescence.state import FluorescencePageState
from RosettaX.workflow.calibration import fluorescence as services


logger = logging.getLogger(__name__)


def register_callbacks(section) -> None:
    """
    Register calibration callbacks.
    """
    logger.debug("Registering calibration callbacks.")

    _register_graph_render_callback(section)
    _register_calibration_workflow_callback(section)


def _register_graph_render_callback(section) -> None:
    """
    Register the graph rendering callback.
    """

    @dash.callback(
        dash.Output(section.ids.graph_calibration, "figure"),
        dash.Input(section.ids.graph_store, "data"),
        prevent_initial_call=False,
    )
    def update_calibration_graph(
        stored_figure: Any,
    ) -> go.Figure:
        logger.debug(
            "update_calibration_graph called with stored_figure_type=%s",
            type(stored_figure).__name__,
        )

        figure = services.rebuild_calibration_graph(
            stored_figure=stored_figure,
            empty_message="Create a calibration first.",
            failure_message="Failed to render calibration graph.",
            logger=logger,
        )

        return _finalize_figure_size(figure=figure)


def _finalize_figure_size(
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Apply the section graph layout and legend placement.

    The graph height is controlled by the Dash component CSS style, not by
    Plotly layout height. Axis automargins are disabled so long axis titles
    cannot shrink the plotting area unpredictably.
    """
    figure.update_layout(
        height=None,
        autosize=True,
        title={
            "text": "",
        },
        margin={
            "l": 92,
            "r": 28,
            "t": 18,
            "b": 78,
        },
        legend={
            "x": 0.98,
            "y": 0.98,
            "xanchor": "right",
            "yanchor": "top",
            "bgcolor": "rgba(255,255,255,0.65)",
            "bordercolor": "rgba(0,0,0,0.15)",
            "borderwidth": 1,
        },
    )

    figure.update_xaxes(
        automargin=False,
        title_standoff=10,
    )

    figure.update_yaxes(
        automargin=False,
        title_standoff=10,
    )

    return figure


def _get_fluorescence_detector_dropdown_pattern(section) -> Any:
    """
    Return the pattern matching ID for fluorescence detector dropdowns.

    This supports both the newer reusable peak workflow naming and older
    aliases if they still exist in the page IDs.
    """
    fluorescence_ids = section.page.ids.Fluorescence

    if hasattr(
        fluorescence_ids,
        "process_detector_dropdown_pattern",
    ):
        return fluorescence_ids.process_detector_dropdown_pattern()

    if hasattr(
        fluorescence_ids,
        "detector_dropdown_pattern",
    ):
        return fluorescence_ids.detector_dropdown_pattern()

    raise AttributeError(
        "Fluorescence IDs must expose process_detector_dropdown_pattern() "
        "or detector_dropdown_pattern()."
    )


def _resolve_active_fluorescence_channel(
    *,
    selected_process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
) -> Optional[str]:
    """
    Resolve the active fluorescence detector channel.

    Resolution order
    ----------------
    - primary, for 1D processes.
    - x_axis, for 2D processes using the newer generic axis naming.
    - x, for older 2D processes.
    - first available channel value.
    """
    selected_process_name_clean = (
        ""
        if selected_process_name is None
        else str(selected_process_name)
    )

    channel_values: dict[str, str] = {}

    for dropdown_id, dropdown_value in zip(
        detector_dropdown_ids or [],
        detector_dropdown_values or [],
        strict=False,
    ):
        if not isinstance(dropdown_id, dict):
            continue

        if dropdown_id.get("process") != selected_process_name_clean:
            continue

        channel_name = dropdown_id.get("channel")
        channel_value = "" if dropdown_value is None else str(dropdown_value).strip()

        if not channel_name:
            continue

        if not channel_value or channel_value.lower() == "none":
            continue

        channel_values[str(channel_name)] = channel_value

    logger.debug(
        "Resolved fluorescence channel_values=%r for selected_process_name=%r",
        channel_values,
        selected_process_name_clean,
    )

    if "primary" in channel_values:
        return channel_values["primary"]

    if "x_axis" in channel_values:
        return channel_values["x_axis"]

    if "x" in channel_values:
        return channel_values["x"]

    return next(
        iter(channel_values.values()),
        None,
    )


def _register_calibration_workflow_callback(section) -> None:
    """
    Register the calibration workflow callback.
    """

    @dash.callback(
        dash.Output(section.ids.graph_store, "data"),
        dash.Output(section.ids.calibration_store, "data"),
        dash.Output(section.ids.slope_out, "children"),
        dash.Output(section.ids.intercept_out, "children"),
        dash.Output(section.ids.r_squared_out, "children"),
        dash.Output(section.ids.apply_status, "children"),
        dash.Input(section.ids.calibrate_btn, "n_clicks"),
        dash.State(section.page.ids.State.page_state_store, "data"),
        dash.State(section.ids.bead_table, "data"),
        dash.State(section.page.ids.Fluorescence.process_dropdown, "value"),
        dash.State(_get_fluorescence_detector_dropdown_pattern(section), "id"),
        dash.State(_get_fluorescence_detector_dropdown_pattern(section), "value"),
        prevent_initial_call=True,
    )
    def calibrate_and_apply(
        n_clicks: int,
        page_state_payload: Any,
        table_data: list[dict[str, Any]] | None,
        selected_fluorescence_process_name: Any,
        fluorescence_detector_dropdown_ids: list[dict[str, Any]],
        fluorescence_detector_dropdown_values: list[Any],
    ) -> tuple:
        page_state = FluorescencePageState.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

        detector_column = _resolve_active_fluorescence_channel(
            selected_process_name=selected_fluorescence_process_name,
            detector_dropdown_ids=fluorescence_detector_dropdown_ids,
            detector_dropdown_values=fluorescence_detector_dropdown_values,
        )

        logger.debug(
            "calibrate_and_apply called with n_clicks=%r bead_file_path=%r "
            "table_row_count=%r selected_fluorescence_process_name=%r "
            "detector_column=%r",
            n_clicks,
            page_state.uploaded_fcs_path,
            None if table_data is None else len(table_data),
            selected_fluorescence_process_name,
            detector_column,
        )

        del n_clicks

        result = services.run_calibration_workflow(
            bead_file_path=page_state.uploaded_fcs_path,
            table_data=table_data,
            detector_column=detector_column,
            scattering_detector_column=None,
            scattering_threshold=None,
            logger=logger,
        )

        return result.to_tuple()
