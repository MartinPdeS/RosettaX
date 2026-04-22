# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.plottings import add_vertical_lines, _make_info_figure
from RosettaX.utils.casting import _as_int
from RosettaX.utils.service import build_channel_options_from_file


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScatteringCallbackInputs:
    graph_enabled: bool
    scattering_channel: str
    nbins: int
    max_events: int
    yscale_selection: Any


class Scattering:
    """
    Render and manage the scattering detector histogram section.

    Design
    ------
    - The upload section owns backend creation.
    - This section only reuses self.page.backend.
    - The backend is file bound.
    - The detector channel is supplied at call time.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.runtime_config = RuntimeConfig()
        logger.debug("Initialized ScatteringSection with page=%r", page)

    def _refresh_runtime(self) -> RuntimeConfig:
        self.runtime_config = RuntimeConfig()
        return self.runtime_config

    def _get_default_peak_count(self) -> int:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_int("calibration.peak_count", default=3)

    def _get_default_show_graphs(self) -> bool:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_show_graphs(default=False)

    def _get_default_n_bins_for_plots(self) -> int:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_int("calibration.n_bins_for_plots", default=100)

    def _get_default_max_events_for_analysis(self) -> int:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_int("calibration.max_events_for_analysis", default=10000)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("2. Scattering channel")

    def _build_body(self) -> dbc.CardBody:
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

    def _build_detector_dropdown(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Scattering detector:"),
                dash.dcc.Dropdown(
                    id=self.page.ids.Scattering.detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def _build_peak_controls(self) -> dash.html.Div:
        peak_count_input = dash.dcc.Input(
            id=self.page.ids.Scattering.peak_count_input,
            type="number",
            min=1,
            step=1,
            value=self._get_default_peak_count(),
            style={"width": "120px"},
            persistence=True,
            persistence_type="session",
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
            id=self.page.ids.Scattering.find_peaks_btn,
            n_clicks=0,
            style={"marginLeft": "16px"},
        )

        return dash.html.Div(
            [peak_count_row, find_peaks_button],
            style={"display": "flex", "alignItems": "center"},
        )

    def _build_graph_toggle_switch(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Scattering.graph_toggle_switch,
                    options=[{"label": "Show histogram", "value": "enabled"}],
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
                dash.html.Br(),
                self._build_histogram_graph(),
                dash.html.Br(),
                self._build_yscale_switch(),
                dash.html.Br(),
                self._build_nbins_input(),
            ],
            id=self.page.ids.Scattering.graph_toggle_container,
            style={"display": "none"},
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Scattering.graph_hist,
                style=self.page.style["graph"],
            ),
            type="default",
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "block"},
            persistence=True,
            persistence_type="session",
        )

    def _build_nbins_input(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=self._get_default_n_bins_for_plots(),
                    style={"width": "160px"},
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering ScatteringSection callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Scattering.detector_dropdown, "options"),
            dash.Output(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            prevent_initial_call=False,
        )
        def populate_scattering_detector_dropdown(
            uploaded_fcs_path: Any,
            current_detector_value: Any,
        ) -> tuple[list[dict[str, Any]], Any]:
            return self._populate_scattering_detector_dropdown(
                uploaded_fcs_path=uploaded_fcs_path,
                current_detector_value=current_detector_value,
            )

        @dash.callback(
            dash.Output(self.page.ids.Scattering.peak_count_input, "value"),
            dash.Output(self.page.ids.Scattering.nbins_input, "value"),
            dash.Output(self.page.ids.Scattering.graph_toggle_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(runtime_config_data: Any) -> tuple[Any, Any, Any]:
            logger.debug(
                "sync_controls_from_runtime_store called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = self._refresh_runtime()

            if isinstance(runtime_config_data, dict):
                runtime_config.Default.load_dict(runtime_config_data)

            peak_count_value = runtime_config.get_int("calibration.peak_count", default=3)
            n_bins_for_plots_value = runtime_config.get_int("calibration.n_bins_for_plots", default=100)
            show_graphs_value = runtime_config.get_show_graphs(default=False)

            logger.debug(
                "Resolved scattering controls from runtime store peak_count=%r n_bins_for_plots=%r show_graphs=%r",
                peak_count_value,
                n_bins_for_plots_value,
                show_graphs_value,
            )

            return (
                peak_count_value,
                n_bins_for_plots_value,
                ["enabled"] if show_graphs_value else [],
            )

        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_toggle_container, "style"),
            dash.Input(self.page.ids.Scattering.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_graph_container(graph_toggle_value: Any) -> dict[str, str]:
            graph_enabled = self._is_enabled(graph_toggle_value)

            logger.debug(
                "toggle_scattering_graph_container called with graph_toggle_value=%r resolved_graph_enabled=%r",
                graph_toggle_value,
                graph_enabled,
            )

            return {"display": "block"} if graph_enabled else {"display": "none"}

        @dash.callback(
            dash.Output(self.page.ids.Scattering.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(
            uploaded_fcs_path: Any,
            scattering_channel: Any,
        ) -> dict[str, list[Any]]:
            logger.debug(
                "clear_peak_lines_on_context_change called with uploaded_fcs_path=%r scattering_channel=%r",
                uploaded_fcs_path,
                scattering_channel,
            )
            return {"positions": [], "labels": []}

        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_hist, "figure"),
            dash.Input(self.page.ids.Scattering.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Scattering.yscale_switch, "value"),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input(self.page.ids.Scattering.peak_lines_store, "data"),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            prevent_initial_call=False,
        )
        def update_scattering_histogram(
            graph_toggle_value: Any,
            yscale_selection: Any,
            uploaded_fcs_path: Any,
            scattering_channel: Any,
            scattering_nbins: Any,
            peak_lines: Any,
            max_events_for_plots: Any,
        ) -> go.Figure:
            callback_inputs = self._parse_scattering_histogram_callback_inputs(
                graph_toggle_value=graph_toggle_value,
                scattering_channel=scattering_channel,
                scattering_nbins=scattering_nbins,
                yscale_selection=yscale_selection,
                max_events_for_plots=max_events_for_plots,
            )

            logger.debug(
                "update_scattering_histogram called with callback_inputs=%r peak_lines=%r uploaded_fcs_path=%r",
                callback_inputs,
                peak_lines,
                uploaded_fcs_path,
            )

            if not callback_inputs.graph_enabled:
                return _make_info_figure("Histogram is hidden.")

            uploaded_fcs_path_clean = self._clean_optional_string(uploaded_fcs_path)
            if not uploaded_fcs_path_clean:
                return _make_info_figure("Upload an FCS file first.")

            if not callback_inputs.scattering_channel:
                return _make_info_figure("Select a scattering detector first.")

            if self.page.backend is None:
                return _make_info_figure("Backend is not initialized. Upload an FCS file again.")

            try:
                line_positions: list[float] = []
                line_labels: list[str] = []

                if isinstance(peak_lines, dict):
                    line_positions = [
                        float(value)
                        for value in (peak_lines.get("positions") or [])
                    ]
                    line_labels = [
                        str(value)
                        for value in (peak_lines.get("labels") or [])
                    ]

                histogram_result = self.page.backend.build_histogram(
                    detector_column=callback_inputs.scattering_channel,
                    n_bins_for_plots=callback_inputs.nbins,
                    max_events_for_analysis=callback_inputs.max_events,
                )

                logger.debug(
                    "update_scattering_histogram using line_positions=%r line_labels=%r",
                    line_positions,
                    line_labels,
                )

                figure = self.page.backend.build_histogram_figure(
                    histogram_result=histogram_result,
                    detector_column=callback_inputs.scattering_channel,
                    use_log_counts=isinstance(callback_inputs.yscale_selection, list)
                    and ("log" in callback_inputs.yscale_selection),
                    peak_positions=line_positions,
                )

                figure = add_vertical_lines(
                    fig=figure,
                    line_positions=line_positions,
                    line_labels=line_labels,
                )
                figure.update_layout(separators=".,")

                return figure

            except Exception as exc:
                logger.exception(
                    "Failed to build scattering histogram for uploaded_fcs_path=%r channel=%r nbins=%r max_events=%r",
                    uploaded_fcs_path_clean,
                    callback_inputs.scattering_channel,
                    callback_inputs.nbins,
                    callback_inputs.max_events,
                )
                return _make_info_figure(f"{type(exc).__name__}: {exc}")

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Output(self.page.ids.Scattering.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Scattering.find_peaks_btn, "n_clicks"),
            dash.State(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.page.ids.Scattering.peak_count_input, "value"),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            prevent_initial_call=True,
        )
        def find_peaks_and_update_table(
            n_clicks: int,
            uploaded_fcs_path: Optional[str],
            scattering_channel: Optional[str],
            peak_count: Any,
            max_events_for_plots: Any,
            table_data: Optional[list[dict[str, Any]]],
            mie_model: Any,
        ) -> tuple[Any, Any]:
            logger.debug(
                "find_peaks_and_update_table called with n_clicks=%r uploaded_fcs_path=%r scattering_channel=%r peak_count=%r max_events_for_plots=%r table_rows=%r mie_model=%r",
                n_clicks,
                uploaded_fcs_path,
                scattering_channel,
                peak_count,
                max_events_for_plots,
                None if table_data is None else len(table_data),
                mie_model,
            )

            if not n_clicks:
                logger.debug("Find peaks button not clicked yet. Returning no_update.")
                return dash.no_update, dash.no_update

            uploaded_fcs_path_clean = self._clean_optional_string(uploaded_fcs_path)
            scattering_channel_clean = self._clean_optional_string(scattering_channel)
            resolved_mie_model = self._resolve_mie_model(mie_model)

            if not uploaded_fcs_path_clean or not scattering_channel_clean:
                logger.debug(
                    "Missing required peak-finding context uploaded_fcs_path_clean=%r scattering_channel_clean=%r",
                    uploaded_fcs_path_clean,
                    scattering_channel_clean,
                )
                return dash.no_update, dash.no_update

            if self.page.backend is None:
                logger.debug("Backend is not initialized. Returning no_update.")
                return dash.no_update, dash.no_update

            resolved_peak_count = _as_int(
                peak_count,
                default=self._get_default_peak_count(),
                min_value=1,
                max_value=50,
            )
            resolved_max_events = _as_int(
                max_events_for_plots,
                default=self._get_default_max_events_for_analysis(),
                min_value=1,
                max_value=5_000_000,
            )

            try:
                peak_detection_result = self.page.backend.find_scattering_peaks(
                    detector_column=scattering_channel_clean,
                    max_peaks=resolved_peak_count,
                    max_events_for_analysis=resolved_max_events,
                    debug=False,
                )

                peak_positions = [
                    float(value)
                    for value in peak_detection_result.peak_positions.tolist()
                ]

                peak_lines_payload = {
                    "positions": peak_positions,
                    "labels": [f"Peak {index + 1}" for index in range(len(peak_positions))],
                }

                updated_table_data = self._write_measured_peaks_into_table(
                    table_data=table_data,
                    peak_positions=peak_positions,
                    mie_model=resolved_mie_model,
                )

                logger.debug(
                    "Peak finding succeeded with peak_positions=%r updated_table_rows=%r updated_table_data=%r",
                    peak_positions,
                    len(updated_table_data),
                    updated_table_data,
                )

                return updated_table_data, peak_lines_payload

            except Exception:
                logger.exception(
                    "Failed to find scattering peaks for uploaded_fcs_path=%r scattering_channel=%r peak_count=%r max_events_for_plots=%r",
                    uploaded_fcs_path_clean,
                    scattering_channel_clean,
                    resolved_peak_count,
                    resolved_max_events,
                )
                raise

    def _populate_scattering_detector_dropdown(
        self,
        *,
        uploaded_fcs_path: Any,
        current_detector_value: Any,
    ) -> tuple[list[dict[str, Any]], Any]:
        uploaded_fcs_path_clean = self._clean_optional_string(uploaded_fcs_path)

        if not uploaded_fcs_path_clean:
            logger.debug("No uploaded FCS path available. Returning empty detector dropdown.")
            return [], None

        try:
            channels = build_channel_options_from_file(
                uploaded_fcs_path_clean,
                preferred_scatter=current_detector_value,
            )
        except Exception:
            logger.exception(
                "Failed to extract scattering channels from uploaded_fcs_path=%r",
                uploaded_fcs_path_clean,
            )
            return [], None

        scattering_detector_options = list(channels.scatter_options or [])
        scattering_detector_value = channels.scatter_value

        logger.debug(
            "Resolved scattering detector dropdown with option_count=%r value=%r",
            len(scattering_detector_options),
            scattering_detector_value,
        )

        return scattering_detector_options, scattering_detector_value

    def _parse_scattering_histogram_callback_inputs(
        self,
        *,
        graph_toggle_value: Any,
        scattering_channel: Any,
        scattering_nbins: Any,
        yscale_selection: Any,
        max_events_for_plots: Any,
    ) -> ScatteringCallbackInputs:
        runtime_config = self._refresh_runtime()

        parsed_inputs = ScatteringCallbackInputs(
            graph_enabled=self._is_enabled(graph_toggle_value),
            scattering_channel=self._clean_optional_string(scattering_channel),
            nbins=_as_int(
                scattering_nbins,
                default=runtime_config.get_int("calibration.n_bins_for_plots", default=100),
                min_value=10,
                max_value=5000,
            ),
            max_events=_as_int(
                max_events_for_plots,
                default=runtime_config.get_int("calibration.max_events_for_analysis", default=10000),
                min_value=1,
                max_value=5_000_000,
            ),
            yscale_selection=yscale_selection,
        )

        logger.debug(
            "Parsed scattering histogram callback inputs=%r",
            parsed_inputs,
        )

        return parsed_inputs

    def _write_measured_peaks_into_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        peak_positions: list[float],
        mie_model: str,
    ) -> list[dict[str, str]]:
        logger.debug(
            "_write_measured_peaks_into_table called with mie_model=%r peak_positions=%r existing_row_count=%r",
            mie_model,
            peak_positions,
            0 if table_data is None else len(table_data),
        )

        updated_rows = [dict(row) for row in (table_data or [])]
        required_row_count = max(len(updated_rows), len(peak_positions), 3)

        while len(updated_rows) < required_row_count:
            updated_rows.append(self._build_empty_row_for_model(mie_model))

        for row_index, row in enumerate(updated_rows):
            if mie_model == "Core/Shell Sphere":
                normalized_row = {
                    "core_diameter_nm": "" if row.get("core_diameter_nm") is None else str(row.get("core_diameter_nm")),
                    "shell_thickness_nm": "" if row.get("shell_thickness_nm") is None else str(row.get("shell_thickness_nm")),
                    "outer_diameter_nm": "" if row.get("outer_diameter_nm") is None else str(row.get("outer_diameter_nm")),
                    "measured_peak_position": "",
                    "expected_coupling": "" if row.get("expected_coupling") is None else str(row.get("expected_coupling")),
                }
            else:
                normalized_row = {
                    "particle_diameter_nm": "" if row.get("particle_diameter_nm") is None else str(row.get("particle_diameter_nm")),
                    "measured_peak_position": "",
                    "expected_coupling": "" if row.get("expected_coupling") is None else str(row.get("expected_coupling")),
                }

            if row_index < len(peak_positions):
                normalized_row["measured_peak_position"] = f"{float(peak_positions[row_index]):.6g}"

            updated_rows[row_index] = normalized_row

        logger.debug(
            "_write_measured_peaks_into_table returning row_count=%r rows=%r",
            len(updated_rows),
            updated_rows,
        )

        return updated_rows

    def _build_empty_row_for_model(self, mie_model: str) -> dict[str, str]:
        if mie_model == "Core/Shell Sphere":
            return {
                "core_diameter_nm": "",
                "shell_thickness_nm": "",
                "outer_diameter_nm": "",
                "measured_peak_position": "",
                "expected_coupling": "",
            }

        return {
            "particle_diameter_nm": "",
            "measured_peak_position": "",
            "expected_coupling": "",
        }

    def _resolve_mie_model(self, mie_model: Any) -> str:
        mie_model_string = self._clean_optional_string(mie_model)
        return "Core/Shell Sphere" if mie_model_string == "Core/Shell Sphere" else "Solid Sphere"

    def _is_enabled(self, value: Any) -> bool:
        return isinstance(value, list) and ("enabled" in value)

    def _clean_optional_string(self, value: Any) -> str:
        if value is None:
            return ""

        cleaned_value = str(value).strip()
        if cleaned_value.lower() == "none":
            return ""

        return cleaned_value