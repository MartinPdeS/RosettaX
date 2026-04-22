from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.plottings import add_vertical_lines, _make_info_figure
from RosettaX.pages.fluorescence.backend import BackEnd

logger = logging.getLogger(__name__)


class Peaks:
    def __init__(self, page) -> None:
        self.page = page
        self.runtime_config = RuntimeConfig()

    def _refresh_runtime(self) -> RuntimeConfig:
        self.runtime_config = RuntimeConfig()
        return self.runtime_config

    def _get_default_show_graphs(self) -> bool:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_show_graphs(default=False)

    def _get_default_peak_count(self) -> int:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_int("calibration.peak_count", default=4)

    def _get_default_n_bins_for_plots(self) -> int:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_int("calibration.n_bins_for_plots", default=100)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self.build_header(),
                self.build_body(),
            ]
        )

    def build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("3. Fluorescence channel after thresholding")

    def build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                dash.html.Br(),
                self._build_detector_dropdown(),
                dash.html.Br(),
                self._build_peak_controls(),
                dash.html.Br(),
                self._build_graph_toggle_switch(),
                dash.html.Br(),
                self._build_graph_controls_container(),
            ]
        )

    def _build_graph_toggle_switch(self) -> dash.html.Div:
        default_show_graphs = self._get_default_show_graphs()

        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Fluorescence.graph_toggle_switch,
                    options=[{"label": "Show histogram", "value": "enabled"}],
                    value=["enabled"] if default_show_graphs else [],
                    switch=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_graph_controls_container(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Br(),
                self._build_histogram_graph(),
                dash.html.Br(),
                self._build_yscale_switch(),
                dash.html.Br(),
                self._build_nbins_input(),
            ],
            id=self.page.ids.Fluorescence.graph_toggle_container,
            style={"display": "none"},
        )

    def _build_detector_dropdown(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Fluorescence detector:"),
                dash.dcc.Dropdown(
                    id=self.page.ids.Fluorescence.detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_peak_controls(self) -> dash.html.Div:
        default_peak_count = self._get_default_peak_count()

        peak_count_input = dash.dcc.Input(
            id=self.page.ids.Fluorescence.peak_count_input,
            type="number",
            min=1,
            step=1,
            value=default_peak_count,
            style={"width": "120px"},
        )

        peak_count_row = dash.html.Div(
            [
                dash.html.Div("Number of peaks to look for:", style={"marginRight": "8px"}),
                peak_count_input,
            ],
            style={"display": "flex", "alignItems": "center"},
        )

        find_peaks_button = dash.html.Button(
            "Find peaks",
            id=self.page.ids.Fluorescence.find_peaks_btn,
            n_clicks=0,
            style={"marginLeft": "16px"},
        )

        return dash.html.Div(
            [peak_count_row, find_peaks_button],
            style={"display": "flex", "alignItems": "center"},
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Fluorescence.graph_hist,
                style=self.page.style["graph"],
            ),
            type="default",
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        runtime_config = self._refresh_runtime()
        histogram_scale = runtime_config.get_str("calibration.histogram_scale", default="log")

        return dbc.Checklist(
            id=self.page.ids.Fluorescence.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"] if histogram_scale == "log" else [],
            switch=True,
            style={"display": "block"},
        )

    def _build_nbins_input(self) -> dash.html.Div:
        default_n_bins_for_plots = self._get_default_n_bins_for_plots()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Fluorescence.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=default_n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.peak_count_input, "value"),
            dash.Output(self.page.ids.Fluorescence.nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(runtime_config_data: Any) -> tuple[Any, Any]:
            logger.debug(
                "sync_controls_from_runtime_store called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = self._refresh_runtime()

            if isinstance(runtime_config_data, dict):
                runtime_config.Default.load_dict(runtime_config_data)

            peak_count_value = runtime_config.get_int("calibration.peak_count", default=4)
            fluorescence_nbins_value = runtime_config.get_int("calibration.n_bins_for_plots", default=100)

            logger.debug(
                "Runtime config resolved to peak_count=%r fluorescence_nbins=%r",
                peak_count_value,
                fluorescence_nbins_value,
            )

            return peak_count_value, fluorescence_nbins_value

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.yscale_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_fluorescence_yscale_from_runtime_store(runtime_config_data: Any) -> list[str]:
            logger.debug(
                "sync_fluorescence_yscale_from_runtime_store called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = self._refresh_runtime()

            if isinstance(runtime_config_data, dict):
                runtime_config.Default.load_dict(runtime_config_data)

            histogram_scale = runtime_config.get_str("calibration.histogram_scale", default="log")

            logger.debug(
                "sync_fluorescence_yscale_from_runtime_store resolved histogram_scale=%r",
                histogram_scale,
            )

            return ["log"] if histogram_scale == "log" else []

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_graph_toggle_from_runtime_store(runtime_config_data: Any) -> list[str]:
            runtime_config = self._refresh_runtime()

            if isinstance(runtime_config_data, dict):
                runtime_config.Default.load_dict(runtime_config_data)

            resolved_show_graphs = runtime_config.get_show_graphs(default=False)

            logger.debug(
                "sync_graph_toggle_from_runtime_store resolved_show_graphs=%r from runtime_config_data=%r",
                resolved_show_graphs,
                runtime_config_data,
            )

            return ["enabled"] if resolved_show_graphs else []

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.graph_toggle_container, "style"),
            dash.Input(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_fluorescence_graph_container(graph_toggle_value: Any) -> dict:
            graph_enabled = self._is_enabled(graph_toggle_value)

            logger.debug(
                "toggle_fluorescence_graph_container called with graph_toggle_value=%r resolved graph_enabled=%r",
                graph_toggle_value,
                graph_enabled,
            )

            return {"display": "block"} if graph_enabled else {"display": "none"}

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(
            fluorescence_channel: Any,
            fcs_path: Any,
            scattering_channel: Any,
        ) -> dict:
            logger.debug(
                "clear_peak_lines_on_context_change called with fluorescence_channel=%r fcs_path=%r scattering_channel=%r",
                fluorescence_channel,
                fcs_path,
                scattering_channel,
            )

            return {"positions": [], "labels": []}

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.source_channel_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.source_channel_store, "data"),
            prevent_initial_call=True,
        )
        def lock_fluorescence_source_channel(
            fluorescence_channel: Optional[str],
            current_locked: Optional[str],
        ) -> Optional[str]:
            fluorescence_channel_clean = self._clean_optional_string(fluorescence_channel)

            logger.debug(
                "lock_fluorescence_source_channel called with fluorescence_channel=%r cleaned=%r current_locked=%r",
                fluorescence_channel,
                fluorescence_channel_clean,
                current_locked,
            )

            if not fluorescence_channel_clean:
                logger.debug("No valid fluorescence channel selected. Returning dash.no_update.")
                return dash.no_update

            if isinstance(current_locked, str) and current_locked.strip():
                logger.debug(
                    "Source channel already locked to %r. Returning dash.no_update.",
                    current_locked,
                )
                return dash.no_update

            logger.debug(
                "Locking fluorescence source channel to %r.",
                fluorescence_channel_clean,
            )

            return fluorescence_channel_clean

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.hist_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.Input(self.page.ids.Fluorescence.nbins_input, "value"),
            dash.Input(self.page.ids.Scattering.threshold_store, "data"),
            dash.Input(self.page.ids.Scattering.threshold_input, "value"),
            dash.State(self.page.ids.Upload.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=True,
        )
        def refresh_fluorescence_hist_store(
            graph_toggle_value: Any,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            fluorescence_channel: Optional[str],
            fluorescence_nbins: Any,
            threshold_payload: Optional[dict],
            threshold_input_value: Any,
            max_events_for_plots: Any,
        ) -> Any:
            graph_enabled = self._is_enabled(graph_toggle_value)
            fcs_path_clean = self._clean_optional_string(fcs_path)
            scattering_channel_clean = self._clean_optional_string(scattering_channel)
            fluorescence_channel_clean = self._clean_optional_string(fluorescence_channel)

            logger.debug(
                "refresh_fluorescence_hist_store called with graph_enabled=%r fcs_path=%r scattering_channel=%r fluorescence_channel=%r fluorescence_nbins=%r threshold_payload=%r threshold_input_value=%r max_events_for_plots=%r",
                graph_enabled,
                fcs_path_clean,
                scattering_channel_clean,
                fluorescence_channel_clean,
                fluorescence_nbins,
                threshold_payload,
                threshold_input_value,
                max_events_for_plots,
            )

            if not graph_enabled:
                logger.debug("Histogram graph is disabled. Returning dash.no_update.")
                return dash.no_update

            if not fcs_path_clean or not scattering_channel_clean or not fluorescence_channel_clean:
                logger.debug(
                    "Missing required input for fluorescence histogram build. "
                    "fcs_path_clean=%r scattering_channel_clean=%r fluorescence_channel_clean=%r. "
                    "Returning dash.no_update.",
                    fcs_path_clean,
                    scattering_channel_clean,
                    fluorescence_channel_clean,
                )
                return dash.no_update

            try:
                backend = BackEnd(fcs_path)
                figure_dict = backend.build_fluorescence_histogram_figure_dict(
                    scattering_channel=scattering_channel_clean,
                    fluorescence_channel=fluorescence_channel_clean,
                    fluorescence_nbins=fluorescence_nbins,
                    threshold_payload=threshold_payload,
                    threshold_input_value=threshold_input_value,
                    max_events_for_plots=max_events_for_plots,
                )

            except Exception:
                logger.exception(
                    "Failed to build fluorescence histogram figure dict for "
                    "fcs_path=%r scattering_channel=%r fluorescence_channel=%r "
                    "fluorescence_nbins=%r threshold_payload=%r threshold_input_value=%r "
                    "max_events_for_plots=%r",
                    fcs_path_clean,
                    scattering_channel_clean,
                    fluorescence_channel_clean,
                    fluorescence_nbins,
                    threshold_payload,
                    threshold_input_value,
                    max_events_for_plots,
                )
                raise

            if isinstance(figure_dict, dict):
                logger.debug(
                    "Fluorescence histogram figure dict built successfully with top level keys=%r",
                    list(figure_dict.keys()),
                )
            else:
                logger.debug(
                    "Fluorescence histogram figure built successfully with non-dict type=%s",
                    type(figure_dict).__name__,
                )

            return figure_dict

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.graph_hist, "figure"),
            dash.Input(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Fluorescence.yscale_switch, "value"),
            dash.Input(self.page.ids.Fluorescence.hist_store, "data"),
            dash.Input(self.page.ids.Fluorescence.peak_lines_store, "data"),
        )
        def update_fluorescence_yscale(
            graph_toggle_value: Any,
            yscale_selection: Any,
            stored_figure: Any,
            peak_lines: Any,
        ) -> go.Figure:
            graph_enabled = self._is_enabled(graph_toggle_value)

            logger.debug(
                "update_fluorescence_yscale called with graph_enabled=%r yscale_selection=%r stored_figure_type=%s peak_lines=%r",
                graph_enabled,
                yscale_selection,
                type(stored_figure).__name__,
                peak_lines,
            )

            if not graph_enabled:
                logger.debug("Histogram graph is hidden. Returning info figure.")
                return _make_info_figure("Histogram is hidden.")

            if not stored_figure:
                logger.debug("No stored figure available. Returning info figure.")
                return _make_info_figure("Select file and channels first.")

            try:
                figure = go.Figure(stored_figure)
            except Exception:
                logger.exception(
                    "Failed to reconstruct Plotly figure from stored_figure with type=%s value=%r",
                    type(stored_figure).__name__,
                    stored_figure,
                )
                raise

            line_positions: list = []
            line_labels: list = []

            if isinstance(peak_lines, dict):
                line_positions = peak_lines.get("positions") or []
                line_labels = peak_lines.get("labels") or []

            logger.debug(
                "Applying peak lines to fluorescence figure with line_positions=%r line_labels=%r",
                line_positions,
                line_labels,
            )

            figure = add_vertical_lines(
                fig=figure,
                line_positions=line_positions,
                line_labels=line_labels,
            )

            use_log_scale = isinstance(yscale_selection, list) and ("log" in yscale_selection)
            figure.update_yaxes(type="log" if use_log_scale else "linear")
            figure.update_layout(separators=".,")

            logger.debug(
                "Updated fluorescence figure y axis to %r scale.",
                "log" if use_log_scale else "linear",
            )

            return figure

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Output(self.page.ids.Fluorescence.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.find_peaks_btn, "n_clicks"),
            dash.State(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.peak_count_input, "value"),
            dash.State(self.page.ids.Upload.max_events_for_plots_input, "value", allow_optional=True),
            dash.State(self.page.ids.Scattering.threshold_store, "data"),
            dash.State(self.page.ids.Scattering.threshold_input, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def find_peaks_and_update_table(
            n_clicks: int,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            fluorescence_channel: Optional[str],
            fluorescence_peak_count: Any,
            max_events_for_plots: Any,
            scattering_threshold_payload: Optional[dict],
            scattering_threshold_input_value: Any,
            table_data: Optional[list[dict]],
        ) -> tuple[Any, Any]:
            logger.debug(
                "find_peaks_and_update_table called with n_clicks=%r fcs_path=%r scattering_channel=%r fluorescence_channel=%r fluorescence_peak_count=%r max_events_for_plots=%r scattering_threshold_payload=%r scattering_threshold_input_value=%r table_rows=%r",
                n_clicks,
                fcs_path,
                scattering_channel,
                fluorescence_channel,
                fluorescence_peak_count,
                max_events_for_plots,
                scattering_threshold_payload,
                scattering_threshold_input_value,
                None if table_data is None else len(table_data),
            )

            if not n_clicks:
                logger.debug("Find peaks button has not been clicked. Returning dash.no_update.")
                return dash.no_update, dash.no_update

            fcs_path_clean = self._clean_optional_string(fcs_path)
            scattering_channel_clean = self._clean_optional_string(scattering_channel)
            fluorescence_channel_clean = self._clean_optional_string(fluorescence_channel)

            if not fcs_path_clean or not scattering_channel_clean or not fluorescence_channel_clean:
                logger.debug(
                    "Missing required input for peak finding. "
                    "fcs_path_clean=%r scattering_channel_clean=%r fluorescence_channel_clean=%r. "
                    "Returning dash.no_update.",
                    fcs_path_clean,
                    scattering_channel_clean,
                    fluorescence_channel_clean,
                )
                return dash.no_update, dash.no_update

            try:
                backend = BackEnd(fcs_path)
                result = backend.find_fluorescence_peaks_and_prepare_outputs(
                    scattering_channel=scattering_channel_clean,
                    fluorescence_channel=fluorescence_channel_clean,
                    fluorescence_peak_count=fluorescence_peak_count,
                    max_events_for_plots=max_events_for_plots,
                    scattering_threshold_payload=scattering_threshold_payload,
                    scattering_threshold_input_value=scattering_threshold_input_value,
                    table_data=table_data,
                )
            except Exception:
                logger.exception(
                    "Failed to find fluorescence peaks for "
                    "fcs_path=%r scattering_channel=%r fluorescence_channel=%r "
                    "fluorescence_peak_count=%r max_events_for_plots=%r "
                    "scattering_threshold_payload=%r scattering_threshold_input_value=%r "
                    "table_data_length=%r",
                    fcs_path_clean,
                    scattering_channel_clean,
                    fluorescence_channel_clean,
                    fluorescence_peak_count,
                    max_events_for_plots,
                    scattering_threshold_payload,
                    scattering_threshold_input_value,
                    None if table_data is None else len(table_data),
                )
                raise

            logger.debug(
                "Peak finding succeeded. Updated table rows=%r peak_lines_payload=%r",
                None if result.updated_table_data is None else len(result.updated_table_data),
                result.peak_lines_payload,
            )

            return result.updated_table_data, result.peak_lines_payload

    def _is_enabled(self, value: Any) -> bool:
        return isinstance(value, list) and ("enabled" in value)

    def _clean_optional_string(self, value: Any) -> str:
        if value is None:
            return ""

        cleaned_value = str(value).strip()
        if cleaned_value.lower() == "none":
            return ""

        return cleaned_value