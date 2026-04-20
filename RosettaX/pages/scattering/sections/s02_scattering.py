from dataclasses import dataclass
from typing import Any, Optional, Tuple
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages import styling
from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.plottings import add_vertical_lines, _make_info_figure
from RosettaX.utils.casting import _as_int
from RosettaX.utils.service import build_channel_options_from_file


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScatteringCallbackInputs:
    """
    Parsed callback inputs for the scattering histogram section.
    """

    graph_enabled: bool
    scattering_channel: str
    nbins: int
    max_events: int
    yscale_selection: Any


class Scattering:
    """
    Render and manage the scattering detector histogram section.

    Responsibilities
    ----------------
    - Populate the scattering detector dropdown from the uploaded FCS file.
    - Render histogram and peak finding controls.
    - Build a histogram preview for the selected detector.
    - Detect histogram peaks and populate the scattering calibration table.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ScatteringSection with page=%r", page)

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
        runtime_config = RuntimeConfig()

        peak_count_input = dash.dcc.Input(
            id=self.page.ids.Scattering.peak_count_input,
            type="number",
            min=1,
            step=1,
            value=runtime_config.Default.peak_count,
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
                    value=[],
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
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.Default.n_bins_for_plots,
                    style={"width": "160px"},
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering scattering callbacks.")

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
        ) -> tuple:
            return self._populate_scattering_detector_dropdown(
                uploaded_fcs_path=uploaded_fcs_path,
                current_detector_value=current_detector_value,
            )

        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_toggle_container, "style"),
            dash.Input(self.page.ids.Scattering.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_graph_container(graph_toggle_value: Any) -> dict:
            graph_enabled = self._is_enabled(graph_toggle_value)

            logger.debug(
                "toggle_scattering_graph_container called with graph_toggle_value=%r resolved graph_enabled=%r",
                graph_toggle_value,
                graph_enabled,
            )

            return {"display": "block"} if graph_enabled else {"display": "none"}

        @dash.callback(
            dash.Output(self.page.ids.Scattering.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(
            scattering_channel: Any,
            fcs_path: Any,
        ) -> dict:
            logger.debug(
                "clear_peak_lines_on_context_change called with scattering_channel=%r fcs_path=%r",
                scattering_channel,
                fcs_path,
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

            if not uploaded_fcs_path:
                return _make_info_figure("Upload an FCS file first.")

            if not callback_inputs.scattering_channel:
                return _make_info_figure("Select a scattering detector first.")

            try:
                scattering_backend = BackEnd(
                    fcs_file_path=str(uploaded_fcs_path),
                    detector_column=str(callback_inputs.scattering_channel),
                )

                histogram_result = scattering_backend.build_histogram(
                    n_bins_for_plots=int(callback_inputs.nbins),
                    max_events_for_analysis=int(callback_inputs.max_events),
                )

                line_positions: list = []
                line_labels: list = []

                if isinstance(peak_lines, dict):
                    line_positions = peak_lines.get("positions") or []
                    line_labels = peak_lines.get("labels") or []

                figure = scattering_backend.build_histogram_figure(
                    histogram_result=histogram_result,
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
                    uploaded_fcs_path,
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
            dash.State(self.page.ids.Scattering.nbins_input, "value"),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def find_peaks_and_update_table(
            n_clicks: int,
            uploaded_fcs_path: Optional[str],
            scattering_channel: Optional[str],
            peak_count: Any,
            scattering_nbins: Any,
            max_events_for_plots: Any,
            table_data: Optional[list[dict]],
        ) -> tuple[Any, Any]:
            logger.debug(
                "find_peaks_and_update_table called with n_clicks=%r uploaded_fcs_path=%r scattering_channel=%r peak_count=%r scattering_nbins=%r max_events_for_plots=%r table_rows=%r",
                n_clicks,
                uploaded_fcs_path,
                scattering_channel,
                peak_count,
                scattering_nbins,
                max_events_for_plots,
                None if table_data is None else len(table_data),
            )

            if not n_clicks:
                return dash.no_update, dash.no_update

            uploaded_fcs_path_clean = self._clean_optional_string(uploaded_fcs_path)
            scattering_channel_clean = self._clean_optional_string(scattering_channel)

            if not uploaded_fcs_path_clean or not scattering_channel_clean:
                return dash.no_update, dash.no_update

            resolved_peak_count = _as_int(peak_count, default=3, min_value=1, max_value=50)
            resolved_nbins = _as_int(scattering_nbins, default=100, min_value=10, max_value=5000)
            resolved_max_events = _as_int(max_events_for_plots, default=10000, min_value=1, max_value=5_000_000)

            try:
                scattering_backend = BackEnd(
                    fcs_file_path=uploaded_fcs_path_clean,
                    detector_column=scattering_channel_clean,
                )

                histogram_result = scattering_backend.build_histogram(
                    n_bins_for_plots=resolved_nbins,
                    max_events_for_analysis=resolved_max_events,
                )

                peak_detection_result = scattering_backend.find_histogram_peaks(
                    histogram_result=histogram_result,
                    peak_count=resolved_peak_count,
                )

                updated_table_data = self._inject_peak_positions_into_table(
                    table_data=table_data,
                    peak_positions=peak_detection_result.peak_positions,
                )

                peak_lines_payload = {
                    "positions": [
                        float(value) for value in peak_detection_result.peak_positions.tolist()
                    ],
                    "labels": [
                        f"Peak {index + 1}"
                        for index in range(len(peak_detection_result.peak_positions))
                    ],
                }

                logger.debug(
                    "Scattering peak finding succeeded. peak_positions=%r updated_table_rows=%r",
                    peak_lines_payload["positions"],
                    None if updated_table_data is None else len(updated_table_data),
                )

                return updated_table_data, peak_lines_payload

            except Exception:
                logger.exception(
                    "Failed to find scattering peaks for uploaded_fcs_path=%r scattering_channel=%r peak_count=%r scattering_nbins=%r max_events_for_plots=%r",
                    uploaded_fcs_path_clean,
                    scattering_channel_clean,
                    resolved_peak_count,
                    resolved_nbins,
                    resolved_max_events,
                )
                raise

    def _populate_scattering_detector_dropdown(
        self,
        *,
        uploaded_fcs_path: Any,
        current_detector_value: Any,
    ) -> tuple:
        if not uploaded_fcs_path:
            logger.debug("No uploaded FCS path available. Returning empty dropdown.")
            return [], None

        try:
            channels = build_channel_options_from_file(
                uploaded_fcs_path,
                preferred_scatter=current_detector_value,
            )
        except Exception:
            logger.exception(
                "Failed to extract scattering channels from uploaded_fcs_path=%r",
                uploaded_fcs_path,
            )
            return [], None

        scattering_detector_options = list(channels.scatter_options or [])
        scattering_detector_value = channels.scatter_value

        logger.debug(
            "Resolved scattering detector dropdown with %r options and value=%r",
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
        runtime_config = RuntimeConfig()

        parsed_inputs = ScatteringCallbackInputs(
            graph_enabled=self._is_enabled(graph_toggle_value),
            scattering_channel=self._clean_optional_string(scattering_channel),
            nbins=_as_int(
                scattering_nbins,
                default=runtime_config.Default.n_bins_for_plots,
                min_value=10,
                max_value=5000,
            ),
            max_events=_as_int(
                max_events_for_plots,
                default=runtime_config.Default.max_events_for_analysis,
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

    def _inject_peak_positions_into_table(
        self,
        *,
        table_data: Optional[list[dict]],
        peak_positions: Any,
    ) -> list[dict]:
        existing_rows = [dict(row) for row in (table_data or [])]
        if peak_positions is None:
            peak_positions = []
        else:
            peak_positions = list(peak_positions)

        required_row_count = max(len(existing_rows), len(peak_positions))
        while len(existing_rows) < required_row_count:
            existing_rows.append({"col1": "", "col2": "", "col3": ""})

        for index, peak_position in enumerate(peak_positions):
            existing_rows[index]["col2"] = f"{float(peak_position):.6g}"

        return existing_rows

    def _is_enabled(self, value: Any) -> bool:
        return isinstance(value, list) and ("enabled" in value)

    def _clean_optional_string(self, value: Any) -> str:
        if value is None:
            return ""

        cleaned_value = str(value).strip()
        if cleaned_value.lower() == "none":
            return ""

        return cleaned_value