# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from . import registry
from . import services


logger = logging.getLogger(__name__)


class Peaks:
    """
    Fluorescence peak section.

    This section reuses the same peak scripts as the scattering peak section.
    It adapts the selected fluorescence peak x coordinate into column ``col2``
    of the fluorescence calibration table.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Fluorescence
        self.scripts = registry.load_peak_scripts()
        self.script_map = registry.build_script_map(
            self.scripts,
        )
        self.default_script_name = registry.get_default_script_name(
            self.scripts,
        )

        logger.debug(
            "Initialized fluorescence Peaks section with shared scripts=%r default_script_name=%r",
            list(self.script_map),
            self.default_script_name,
        )

    def _get_default_runtime_config(self) -> RuntimeConfig:
        return RuntimeConfig.from_default_profile()

    def _get_default_show_graphs(self) -> bool:
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_show_graphs(
            default=False,
        )

    def _get_default_n_bins_for_plots(self) -> int:
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        )

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self.build_header(),
                self.build_body(),
            ]
        )

    def build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("3. Fluorescence channel")

    def build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_stores(),
                dash.html.Br(),
                self._build_process_dropdown(),
                dash.html.Br(),
                self._build_script_controls(),
                dash.html.Br(),
                self._build_script_status(),
                dash.html.Br(),
                self._build_graph_toggle_switch(),
                dash.html.Br(),
                self._build_graph_controls_container(),
            ]
        )

    def _build_stores(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.dcc.Store(
                    id=self.ids.peak_lines_store,
                    data=services.clear_peak_lines_payload(),
                    storage_type="session",
                ),
                dash.dcc.Store(
                    id=self.ids.source_channel_store,
                    data=None,
                    storage_type="session",
                ),
                dash.dcc.Store(
                    id=self.ids.hist_store,
                    data=None,
                    storage_type="session",
                ),
            ]
        )

    def _build_process_dropdown(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Peak detection script:"),
                dash.dcc.Dropdown(
                    id=self.ids.process_dropdown,
                    options=[
                        script.get_process_option()
                        for script in self.scripts
                    ],
                    value=self.default_script_name,
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

    def _build_script_controls(self) -> dash.html.Div:
        return dash.html.Div(
            [
                services.build_controls_for_script(
                    script=script,
                    ids=self.ids,
                )
                for script in self.scripts
            ]
        )

    def _build_script_status(self) -> dash.html.Div:
        return dash.html.Div(
            id=self.ids.script_status,
            style={
                "opacity": 0.8,
            },
        )

    def _build_graph_toggle_switch(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.ids.graph_toggle_switch,
                    options=[
                        {
                            "label": "Show graph",
                            "value": "enabled",
                        }
                    ],
                    value=[
                        "enabled"
                    ]
                    if self._get_default_show_graphs()
                    else [],
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
                dash.html.Br(),
                self._build_histogram_graph(),
                dash.html.Div(
                    [
                        dash.html.Br(),
                        self._build_xscale_switch(),
                        dash.html.Br(),
                        self._build_yscale_switch(),
                        dash.html.Br(),
                        self._build_nbins_input(),
                    ],
                    id=self.ids.histogram_controls_container,
                ),
            ],
            id=self.ids.graph_toggle_container,
            style={
                "display": "none",
            },
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.ids.graph_hist,
                style=styling.PAGE["graph"],
            ),
            type="default",
        )

    def _build_xscale_switch(self) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.ids.xscale_switch,
            options=[
                {
                    "label": "Log scale x",
                    "value": "log",
                }
            ],
            value=[],
            switch=True,
            persistence=True,
            persistence_type="session",
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        runtime_config = self._get_default_runtime_config()
        histogram_scale = runtime_config.get_str(
            "calibration.histogram_scale",
            default="log",
        )

        return dbc.Checklist(
            id=self.ids.yscale_switch,
            options=[
                {
                    "label": "Log scale y",
                    "value": "log",
                }
            ],
            value=[
                "log"
            ]
            if histogram_scale == "log"
            else [],
            switch=True,
            persistence=True,
            persistence_type="session",
        )

    def _build_nbins_input(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.ids.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=self._get_default_n_bins_for_plots(),
                    style={
                        "width": "160px",
                    },
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering fluorescence Peaks callbacks.")
        self._register_runtime_sync_callbacks()
        self._register_script_visibility_callback()
        self._register_detector_dropdown_population_callback()
        self._register_graph_visibility_callbacks()
        self._register_context_reset_callback()
        self._register_source_channel_lock_callback()
        self._register_graph_store_callback()
        self._register_graph_render_callback()
        self._register_graph_click_callback()
        self._register_script_action_callback()

    def _get_script(self, selected_process_name: Any) -> Any:
        return self.script_map.get(
            services.clean_optional_string(selected_process_name),
        )

    def _is_selected_script_two_dimensional(self, selected_process_name: Any) -> bool:
        script = self._get_script(
            selected_process_name,
        )

        if script is None:
            return False

        return services.script_uses_two_dimensional_graph(
            script,
        )

    def _register_runtime_sync_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.ids.nbins_input, "value"),
            dash.Output(self.ids.yscale_switch, "value"),
            dash.Output(self.ids.graph_toggle_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(
            runtime_config_data: Any,
        ) -> tuple[Any, list[str], list[str]]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            nbins_value = runtime_config.get_int(
                "calibration.n_bins_for_plots",
                default=100,
            )
            histogram_scale = runtime_config.get_str(
                "calibration.histogram_scale",
                default="log",
            )
            show_graphs = runtime_config.get_show_graphs(
                default=False,
            )

            return (
                nbins_value,
                ["log"] if histogram_scale == "log" else [],
                ["enabled"] if show_graphs else [],
            )

    def _register_script_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.controls_container_pattern(),
                "style",
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            prevent_initial_call=False,
        )
        def toggle_script_controls(
            selected_process_name: Any,
        ) -> list[dict[str, Any]]:
            return [
                services.build_visibility_style_for_script(
                    script=script,
                    selected_process_name=selected_process_name,
                )
                for script in self.scripts
            ]

    def _register_detector_dropdown_population_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.detector_dropdown_pattern(),
                "options",
            ),
            dash.Output(
                self.ids.detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.State(
                self.ids.detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.ids.detector_dropdown_pattern(),
                "value",
            ),
            prevent_initial_call=False,
        )
        def populate_script_detector_dropdowns(
            uploaded_fcs_path: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            current_detector_values: list[Any],
        ) -> tuple[list[list[dict[str, Any]]], list[Any]]:
            options = services.build_fluorescence_detector_options(
                uploaded_fcs_path=uploaded_fcs_path,
                logger=logger,
            )

            values = services.resolve_detector_dropdown_values(
                detector_dropdown_ids=detector_dropdown_ids,
                current_detector_values=current_detector_values,
                options=options,
                logger=logger,
            )

            return (
                [
                    options
                    for _ in detector_dropdown_ids
                ],
                values,
            )

    def _register_graph_visibility_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_toggle_container, "style"),
            dash.Input(self.ids.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_graph_container(
            graph_toggle_value: Any,
        ) -> dict[str, str]:
            return {
                "display": "block",
            } if services.is_enabled(graph_toggle_value) else {
                "display": "none",
            }

        @dash.callback(
            dash.Output(
                self.ids.graph_toggle_switch,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.State(self.ids.graph_toggle_switch, "value"),
            prevent_initial_call=True,
        )
        def force_graph_visibility_for_selected_script(
            selected_process_name: Any,
            current_graph_toggle_value: Any,
        ) -> Any:
            script = self._get_script(
                selected_process_name,
            )

            if script is None:
                return dash.no_update

            if services.script_should_force_graph_visible(script):
                return ["enabled"]

            return current_graph_toggle_value

    def _register_context_reset_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.peak_lines_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.script_status,
                "children",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.Input(
                self.ids.detector_dropdown_pattern(),
                "value",
            ),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(
            selected_process_name: Any,
            fcs_path: Any,
            detector_dropdown_values: list[Any],
        ) -> tuple[dict[str, list[Any]], str]:
            del selected_process_name
            del fcs_path
            del detector_dropdown_values

            return (
                services.clear_peak_lines_payload(),
                "",
            )

    def _register_source_channel_lock_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.source_channel_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.Input(
                self.ids.detector_dropdown_pattern(),
                "value",
            ),
            dash.State(
                self.ids.detector_dropdown_pattern(),
                "id",
            ),
            dash.State(self.ids.source_channel_store, "data"),
            prevent_initial_call=True,
        )
        def lock_source_channel(
            selected_process_name: Any,
            detector_dropdown_values: list[Any],
            detector_dropdown_ids: list[dict[str, Any]],
            current_locked: Optional[str],
        ) -> Any:
            fluorescence_channel = services.resolve_primary_channel(
                selected_process_name=selected_process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
            )

            if not fluorescence_channel:
                return dash.no_update

            if isinstance(current_locked, str) and current_locked.strip():
                return dash.no_update

            return fluorescence_channel

    def _register_graph_store_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.hist_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.Input(
                self.ids.detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(self.ids.nbins_input, "value"),
            dash.State(
                self.ids.detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            prevent_initial_call=True,
        )
        def refresh_graph_store(
            graph_toggle_value: Any,
            fcs_path: Any,
            selected_process_name: Any,
            detector_dropdown_values: list[Any],
            nbins: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            max_events_for_plots: Any,
        ) -> Any:
            script = self._get_script(
                selected_process_name,
            )

            if script is None:
                return dash.no_update

            channel_values = services.resolve_detector_channel_values(
                selected_process_name=selected_process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
            )

            should_refresh, fcs_path_clean = services.should_refresh_graph_store(
                graph_toggle_value=graph_toggle_value,
                fcs_path=fcs_path,
                channel_values=channel_values,
                logger=logger,
            )

            if not should_refresh:
                return dash.no_update

            if services.script_uses_two_dimensional_graph(script):
                x_channel = channel_values.get("x")
                y_channel = channel_values.get("y")

                if not x_channel or not y_channel:
                    return dash.no_update

                return services.build_fluorescence_2d_figure_dict(
                    fcs_path=fcs_path_clean,
                    x_channel=x_channel,
                    y_channel=y_channel,
                    nbins=nbins,
                    max_events_for_plots=max_events_for_plots,
                )

            fluorescence_channel = services.resolve_primary_channel(
                selected_process_name=selected_process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
            )

            if not fluorescence_channel:
                return dash.no_update

            return services.build_fluorescence_1d_figure_dict(
                fcs_path=fcs_path_clean,
                fluorescence_channel=fluorescence_channel,
                nbins=nbins,
                max_events_for_plots=max_events_for_plots,
            )

    def _register_graph_render_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_hist, "figure"),
            dash.Input(self.ids.graph_toggle_switch, "value"),
            dash.Input(self.ids.yscale_switch, "value"),
            dash.Input(self.ids.xscale_switch, "value"),
            dash.Input(self.ids.hist_store, "data"),
            dash.Input(self.ids.peak_lines_store, "data"),
            dash.Input(self.ids.process_dropdown, "value"),
            prevent_initial_call=False,
        )
        def update_graph(
            graph_toggle_value: Any,
            yscale_selection: Any,
            xscale_selection: Any,
            stored_figure: Any,
            peak_lines: Any,
            selected_process_name: Any,
        ) -> go.Figure:
            return services.rebuild_fluorescence_graph_figure(
                graph_toggle_value=graph_toggle_value,
                yscale_selection=yscale_selection,
                xscale_selection=xscale_selection,
                stored_figure=stored_figure,
                peak_lines=peak_lines,
                is_two_dimensional=self._is_selected_script_two_dimensional(
                    selected_process_name,
                ),
                logger=logger,
            )

    def _register_graph_click_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.peak_lines_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.script_status,
                "children",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.graph_hist, "clickData"),
            dash.State(self.ids.process_dropdown, "value"),
            dash.State(self.ids.peak_lines_store, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def handle_graph_click(
            click_data: Any,
            selected_process_name: Any,
            existing_peak_lines_payload: Any,
            table_data: Any,
        ) -> tuple[Any, Any, Any]:
            script = self._get_script(
                selected_process_name,
            )

            if script is None:
                return dash.no_update, dash.no_update, dash.no_update

            if not services.script_uses_manual_click(script):
                return dash.no_update, dash.no_update, dash.no_update

            clicked_x_position = services.extract_x_position_from_click_data(
                click_data,
            )

            if clicked_x_position is None:
                return dash.no_update, dash.no_update, dash.no_update

            existing_x_positions = services.extract_x_positions_from_peak_payload(
                existing_peak_lines_payload,
            )
            next_x_positions = sorted(
                [
                    *existing_x_positions,
                    float(clicked_x_position),
                ]
            )

            peak_payload = services.build_peak_payload_from_x_positions(
                x_positions=next_x_positions,
                prefix="Manual peak",
            )
            table_rows = services.write_x_positions_to_calibration_table(
                table_data=table_data,
                x_positions=next_x_positions,
            )

            return (
                table_rows,
                peak_payload,
                (
                    f"Added peak at x={float(clicked_x_position):.6g}. "
                    f"{len(next_x_positions)} peak(s) selected."
                ),
            )

    def _register_script_action_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.peak_lines_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.script_status,
                "children",
                allow_duplicate=True,
            ),
            dash.Input(
                self.ids.action_button_pattern(),
                "n_clicks",
            ),
            dash.Input(
                self.ids.find_peaks_btn,
                "n_clicks",
                allow_optional=True,
            ),
            dash.Input(
                self.ids.clear_manual_peaks_btn,
                "n_clicks",
                allow_optional=True,
            ),
            dash.Input(
                self.ids.clear_manual_2d_peaks_btn,
                "n_clicks",
                allow_optional=True,
            ),
            dash.State(self.ids.process_dropdown, "value"),
            dash.State(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.State(
                self.ids.detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.ids.detector_dropdown_pattern(),
                "value",
            ),
            dash.State(
                self.ids.setting_pattern(),
                "id",
            ),
            dash.State(
                self.ids.setting_pattern(),
                "value",
            ),
            dash.State(
                self.ids.peak_count_input,
                "value",
                allow_optional=True,
            ),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def handle_script_action(
            pattern_action_n_clicks: list[Any],
            legacy_find_peaks_n_clicks: Any,
            legacy_clear_manual_peaks_n_clicks: Any,
            legacy_clear_manual_2d_peaks_n_clicks: Any,
            selected_process_name: Any,
            fcs_path: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            setting_ids: list[dict[str, Any]],
            setting_values: list[Any],
            legacy_peak_count: Any,
            max_events_for_plots: Any,
            table_data: Any,
        ) -> tuple[Any, Any, Any]:
            del pattern_action_n_clicks
            del legacy_find_peaks_n_clicks
            del legacy_clear_manual_peaks_n_clicks
            del legacy_clear_manual_2d_peaks_n_clicks

            triggered_id = dash.callback_context.triggered_id

            action_name = None

            if isinstance(triggered_id, dict):
                if triggered_id.get("process") != selected_process_name:
                    return dash.no_update, dash.no_update, dash.no_update

                action_name = triggered_id.get("action")

            elif triggered_id == self.ids.find_peaks_btn:
                action_name = "find_peaks"

            elif triggered_id in {
                self.ids.clear_manual_peaks_btn,
                self.ids.clear_manual_2d_peaks_btn,
            }:
                action_name = "clear_peaks"

            else:
                return dash.no_update, dash.no_update, dash.no_update

            if action_name == "clear_peaks":
                return (
                    services.clear_measured_peak_positions_from_table(
                        table_data=table_data,
                    ),
                    services.clear_peak_lines_payload(),
                    "Cleared fluorescence peaks.",
                )

            if action_name != "find_peaks":
                return dash.no_update, dash.no_update, dash.no_update

            fcs_path_clean = services.clean_optional_string(
                fcs_path,
            )
            fluorescence_channel = services.resolve_primary_channel(
                selected_process_name=selected_process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
            )

            if not fcs_path_clean or not fluorescence_channel:
                return (
                    dash.no_update,
                    dash.no_update,
                    "Select an FCS file and a fluorescence detector first.",
                )

            peak_count = services.resolve_setting_value(
                selected_process_name=selected_process_name,
                setting_name="peak_count",
                setting_ids=setting_ids,
                setting_values=setting_values,
                fallback_value=legacy_peak_count,
            )

            table_rows, peak_payload, status = services.run_automatic_peak_finding(
                fcs_path=fcs_path_clean,
                fluorescence_channel=fluorescence_channel,
                peak_count=peak_count,
                max_events_for_plots=max_events_for_plots,
                table_data=table_data,
            )

            return table_rows, peak_payload, status