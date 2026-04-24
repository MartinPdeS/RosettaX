# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils import styling
from RosettaX.utils import plottings
from RosettaX.utils.runtime_config import RuntimeConfig

from RosettaX.peak_script import DEFAULT_PROCESS_NAME

from . import services


logger = logging.getLogger(__name__)


class Peaks:
    """
    Render and manage scattering peak detection.

    Design
    ------
    This section discovers peak process scripts dynamically from
    RosettaX/peak_script.

    Each process script owns:
    - its detector channel dropdowns
    - its local control UI
    - its action buttons
    - its graph click behavior when relevant
    - its optional process specific settings

    Adding a new process should only require adding a new file under
    RosettaX/peak_script.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized Scattering section with page=%r", page)

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_show_graphs(self) -> bool:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_show_graphs(
            default=True,
        )

    def _get_default_n_bins_for_plots(self) -> int:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        )

    def _get_default_histogram_scale(self) -> str:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_str(
            "calibration.histogram_scale",
            default="log",
        )

    def get_layout(self) -> dbc.Card:
        logger.debug("Building Scattering layout.")
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("2. Scattering peak detection")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_process_selector(),
                dash.html.Br(),
                self._build_process_controls(),
                dash.html.Br(),
                self._build_graph_toggle_switch(),
                dash.html.Br(),
                self._build_graph_controls_container(),
            ]
        )

    def _build_process_selector(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    "Peak detection process:",
                    style={
                        "marginBottom": "6px",
                        "fontWeight": 500,
                    },
                ),
                dash.dcc.Dropdown(
                    id=self.page.ids.Scattering.process_dropdown,
                    options=services.build_process_options(),
                    value=DEFAULT_PROCESS_NAME,
                    clearable=False,
                    searchable=False,
                    persistence=True,
                    persistence_type="session",
                    style={
                        "width": "500px",
                    },
                ),
            ],
            style=styling.CARD,
        )

    def _build_process_controls(self) -> dash.html.Div:
        return dash.html.Div(
            [
                process.build_controls(
                    ids=self.page.ids.Scattering,
                )
                for process in services.get_peak_processes()
            ]
        )

    def _build_graph_toggle_switch(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Scattering.graph_toggle_switch,
                    options=[
                        {
                            "label": "Show graph",
                            "value": "enabled",
                        }
                    ],
                    value=["enabled"] if self._get_default_show_graphs() else [],
                    switch=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def _build_graph_controls_container(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_graph(),
                dash.html.Br(),
                dash.html.Div(
                    [
                        self._build_yscale_switch(),
                        self._build_nbins_input(),
                    ],
                    id=self.page.ids.Scattering.histogram_controls_container,
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "16px",
                        "flexWrap": "wrap",
                    },
                ),
            ],
            id=self.page.ids.Scattering.graph_toggle_container,
            style={
                "display": "none",
            },
        )

    def _build_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Scattering.graph_hist,
                style=styling.PAGE["graph"],
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "doubleClick": "reset",
                    "responsive": True,
                },
            ),
            type="default",
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        histogram_scale = self._get_default_histogram_scale()

        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[
                {
                    "label": "Log scale",
                    "value": "log",
                }
            ],
            value=["log"] if histogram_scale == "log" else [],
            switch=True,
            style={
                "display": "block",
            },
            persistence=True,
            persistence_type="session",
        )

    def _build_nbins_input(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    "Number of bins:",
                    style={
                        "marginRight": "8px",
                    },
                ),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=self._get_default_n_bins_for_plots(),
                    style={
                        "width": "160px",
                    },
                    debounce=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
            },
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering Scattering callbacks.")
        self._register_peak_script_detector_dropdowns_callback()
        self._register_runtime_sync_callback()
        self._register_process_visibility_callback()
        self._register_manual_process_graph_visibility_callback()
        self._register_graph_visibility_callback()
        self._register_histogram_controls_visibility_callback()
        self._register_peak_context_reset_callback()
        self._register_graph_callback()
        self._register_manual_click_callback()
        self._register_process_action_callback()

    def _register_peak_script_detector_dropdowns_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "options",
            ),
            dash.Output(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            prevent_initial_call=False,
        )
        def populate_peak_script_detector_dropdowns(
            uploaded_fcs_path: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            current_detector_values: list[Any],
        ) -> tuple[list[list[dict[str, Any]]], list[Any]]:
            logger.debug(
                "populate_peak_script_detector_dropdowns called with "
                "uploaded_fcs_path=%r detector_dropdown_ids=%r "
                "current_detector_values=%r",
                uploaded_fcs_path,
                detector_dropdown_ids,
                current_detector_values,
            )

            return services.populate_peak_script_detector_dropdowns(
                uploaded_fcs_path=uploaded_fcs_path,
                detector_dropdown_ids=detector_dropdown_ids,
                current_detector_values=current_detector_values,
                logger=logger,
            )

    def _register_runtime_sync_callback(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Scattering.peak_count_input, "value"),
            dash.Output(self.page.ids.Scattering.nbins_input, "value"),
            dash.Output(self.page.ids.Scattering.graph_toggle_switch, "value"),
            dash.Output(self.page.ids.Scattering.yscale_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(
            runtime_config_data: Any,
        ) -> tuple[Any, Any, Any, Any]:
            logger.debug(
                "sync_controls_from_runtime_store called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            histogram_scale = runtime_config.get_str(
                "calibration.histogram_scale",
                default="log",
            )

            resolved_values = (
                runtime_config.get_int(
                    "calibration.peak_count",
                    default=3,
                ),
                runtime_config.get_int(
                    "calibration.n_bins_for_plots",
                    default=100,
                ),
                ["enabled"] if runtime_config.get_show_graphs(default=True) else [],
                ["log"] if histogram_scale == "log" else [],
            )

            logger.debug(
                "sync_controls_from_runtime_store returning resolved_values=%r",
                resolved_values,
            )

            return resolved_values

    def _register_process_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Scattering.process_controls_container_pattern(),
                "style",
            ),
            dash.Input(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(
                self.page.ids.Scattering.process_controls_container_pattern(),
                "id",
            ),
            prevent_initial_call=False,
        )
        def toggle_process_controls(
            process_name: Any,
            process_container_ids: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            logger.debug(
                "toggle_process_controls called with process_name=%r "
                "process_container_ids=%r",
                process_name,
                process_container_ids,
            )

            return services.build_process_visibility_styles(
                process_name=process_name,
                process_container_ids=process_container_ids,
            )

    def _register_manual_process_graph_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Scattering.graph_toggle_switch,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(self.page.ids.Scattering.graph_toggle_switch, "value"),
            prevent_initial_call=True,
        )
        def force_graph_visible_for_manual_process(
            process_name: Any,
            current_graph_toggle_value: Any,
        ) -> Any:
            logger.debug(
                "force_graph_visible_for_manual_process called with "
                "process_name=%r current_graph_toggle_value=%r",
                process_name,
                current_graph_toggle_value,
            )

            return services.resolve_graph_toggle_for_process(
                process_name=process_name,
                current_graph_toggle_value=current_graph_toggle_value,
            )

    def _register_graph_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_toggle_container, "style"),
            dash.Input(self.page.ids.Scattering.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_graph_container(
            graph_toggle_value: Any,
        ) -> dict[str, str]:
            graph_enabled = services.is_enabled(graph_toggle_value)

            logger.debug(
                "toggle_scattering_graph_container called with graph_toggle_value=%r "
                "graph_enabled=%r",
                graph_toggle_value,
                graph_enabled,
            )

            return {"display": "block"} if graph_enabled else {"display": "none"}

    def _register_histogram_controls_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Scattering.histogram_controls_container,
                "style",
            ),
            dash.Input(self.page.ids.Scattering.process_dropdown, "value"),
            prevent_initial_call=False,
        )
        def toggle_histogram_controls(
            process_name: Any,
        ) -> dict[str, Any]:
            process = services.get_process_instance_for_name(
                process_name=process_name,
            )

            if process is not None and process.graph_type == "1d_histogram":
                return {
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                    "flexWrap": "wrap",
                }

            return {
                "display": "none",
            }

    def _register_peak_context_reset_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Scattering.peak_lines_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Scattering.process_status_pattern(),
                "children",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.process_dropdown, "value"),
            dash.Input(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.State(
                self.page.ids.Scattering.process_status_pattern(),
                "id",
            ),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(
            uploaded_fcs_path: Any,
            process_name: Any,
            detector_dropdown_values: list[Any],
            status_component_ids: list[dict[str, Any]],
        ) -> tuple[dict[str, list[Any]], list[str]]:
            logger.debug(
                "clear_peak_lines_on_context_change called with uploaded_fcs_path=%r "
                "process_name=%r detector_dropdown_values=%r",
                uploaded_fcs_path,
                process_name,
                detector_dropdown_values,
            )

            return (
                services.build_empty_peak_lines_payload(),
                [
                    ""
                    for _ in (status_component_ids or [])
                ],
            )

    def _register_graph_callback(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_hist, "figure"),
            dash.Input(self.page.ids.Scattering.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Scattering.yscale_switch, "value"),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input(self.page.ids.Scattering.peak_lines_store, "data"),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.Input(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(
                self.page.ids.Scattering.process_setting_pattern(),
                "id",
            ),
            dash.Input(
                self.page.ids.Scattering.process_setting_pattern(),
                "value",
            ),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def update_scattering_graph(
            graph_toggle_value: Any,
            yscale_selection: Any,
            uploaded_fcs_path: Any,
            scattering_nbins: Any,
            peak_lines: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            process_name: Any,
            process_setting_ids: list[dict[str, Any]],
            process_setting_values: list[Any],
            max_events_for_plots: Any,
            runtime_config_data: Any,
        ) -> go.Figure:
            logger.debug(
                "update_scattering_graph called with graph_toggle_value=%r "
                "yscale_selection=%r uploaded_fcs_path=%r scattering_nbins=%r "
                "peak_lines=%r detector_dropdown_ids=%r detector_dropdown_values=%r "
                "process_name=%r process_setting_ids=%r process_setting_values=%r "
                "max_events_for_plots=%r",
                graph_toggle_value,
                yscale_selection,
                uploaded_fcs_path,
                scattering_nbins,
                peak_lines,
                detector_dropdown_ids,
                detector_dropdown_values,
                process_name,
                process_setting_ids,
                process_setting_values,
                max_events_for_plots,
            )

            try:
                return services.build_scattering_graph_figure(
                    backend=self.page.backend,
                    uploaded_fcs_path=uploaded_fcs_path,
                    process_name=process_name,
                    detector_dropdown_ids=detector_dropdown_ids,
                    detector_dropdown_values=detector_dropdown_values,
                    process_setting_ids=process_setting_ids,
                    process_setting_values=process_setting_values,
                    graph_toggle_value=graph_toggle_value,
                    yscale_selection=yscale_selection,
                    scattering_nbins=scattering_nbins,
                    peak_lines_payload=peak_lines,
                    max_events_for_plots=max_events_for_plots,
                    runtime_config_data=runtime_config_data,
                )
            except Exception as exc:
                logger.exception("Failed to build scattering graph.")
                return plottings._make_info_figure(
                    f"{type(exc).__name__}: {exc}"
                )

    def _register_manual_click_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Scattering.peak_lines_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Scattering.process_status_pattern(),
                "children",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Scattering.graph_hist, "clickData"),
            dash.State(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.State(self.page.ids.Scattering.peak_lines_store, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(
                self.page.ids.Scattering.process_status_pattern(),
                "id",
            ),
            prevent_initial_call=True,
        )
        def add_manual_peak_from_graph_click(
            click_data: Any,
            process_name: Any,
            uploaded_fcs_path: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            peak_lines: Any,
            table_data: Optional[list[dict[str, Any]]],
            mie_model: Any,
            status_component_ids: list[dict[str, Any]],
        ) -> tuple[Any, Any, list[Any]]:
            logger.debug(
                "add_manual_peak_from_graph_click called with click_data=%r "
                "process_name=%r uploaded_fcs_path=%r detector_dropdown_ids=%r "
                "detector_dropdown_values=%r table_rows=%r mie_model=%r",
                click_data,
                process_name,
                uploaded_fcs_path,
                detector_dropdown_ids,
                detector_dropdown_values,
                None if table_data is None else len(table_data),
                mie_model,
            )

            table_result, peak_lines_result, status = services.resolve_manual_peak_click(
                click_data=click_data,
                process_name=process_name,
                uploaded_fcs_path=uploaded_fcs_path,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                peak_lines_payload=peak_lines,
                table_data=table_data,
                mie_model=mie_model,
                logger=logger,
            )

            status_children = services.build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=services.resolve_process_name(process_name),
                status=status,
            )

            if table_result is None:
                return dash.no_update, dash.no_update, status_children

            return table_result, peak_lines_result, status_children

    def _register_process_action_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Scattering.peak_lines_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Scattering.process_status_pattern(),
                "children",
                allow_duplicate=True,
            ),
            dash.Input(
                self.page.ids.Scattering.process_action_button_pattern(),
                "n_clicks",
            ),
            dash.State(
                self.page.ids.Scattering.process_action_button_pattern(),
                "id",
            ),
            dash.State(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.State(self.page.ids.Scattering.peak_count_input, "value"),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State("runtime-config-store", "data"),
            dash.State(
                self.page.ids.Scattering.process_status_pattern(),
                "id",
            ),
            prevent_initial_call=True,
        )
        def run_process_action(
            action_clicks: list[Any],
            action_ids: list[dict[str, Any]],
            process_name: Any,
            uploaded_fcs_path: Optional[str],
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            peak_count: Any,
            max_events_for_plots: Any,
            table_data: Optional[list[dict[str, Any]]],
            mie_model: Any,
            runtime_config_data: Any,
            status_component_ids: list[dict[str, Any]],
        ) -> tuple[Any, Any, list[Any]]:
            del action_clicks
            del action_ids

            triggered_action_id = dash.ctx.triggered_id

            logger.debug(
                "run_process_action called with triggered_action_id=%r "
                "process_name=%r uploaded_fcs_path=%r detector_dropdown_ids=%r "
                "detector_dropdown_values=%r peak_count=%r max_events_for_plots=%r",
                triggered_action_id,
                process_name,
                uploaded_fcs_path,
                detector_dropdown_ids,
                detector_dropdown_values,
                peak_count,
                max_events_for_plots,
            )

            table_result, peak_lines_result, status, target_process_name = (
                services.resolve_process_action(
                    triggered_action_id=triggered_action_id,
                    backend=self.page.backend,
                    process_name=process_name,
                    uploaded_fcs_path=uploaded_fcs_path,
                    detector_dropdown_ids=detector_dropdown_ids,
                    detector_dropdown_values=detector_dropdown_values,
                    peak_count=peak_count,
                    max_events_for_plots=max_events_for_plots,
                    table_data=table_data,
                    mie_model=mie_model,
                    runtime_config_data=runtime_config_data,
                    logger=logger,
                )
            )

            status_children = services.build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=target_process_name,
                status=status,
            )

            if table_result is None:
                return dash.no_update, dash.no_update, status_children

            return table_result, peak_lines_result, status_children