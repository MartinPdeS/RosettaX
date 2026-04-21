from dataclasses import dataclass
from typing import Any, Optional, Tuple
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines, _make_info_figure
from RosettaX.utils.casting import _as_float, _as_int


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScatteringCallbackInputs:
    triggered_id: Any
    debug_enabled: bool
    scattering_channel: str
    nbins: int
    max_events: int
    yscale_selection: Any
    manual_threshold: Optional[float]
    stored_threshold: Optional[float]
    must_estimate: bool


@dataclass
class ScatteringResult:
    figure: Any = dash.no_update
    scattering_threshold_store: Any = dash.no_update
    scattering_threshold_input_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.figure,
            self.scattering_threshold_store,
            self.scattering_threshold_input_value,
        )


class Scattering:
    def __init__(self, page) -> None:
        self.page = page
        self.runtime_config = RuntimeConfig()
        self.default = self.runtime_config.Default
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
                self._build_debug_store(),
                dash.html.Br(),
                self._build_detector_row(),
                dash.html.Br(),
                self._build_debug_switch_row(),
                dash.html.Br(),
                self._build_debug_controls_container(),
            ]
        )

    def _build_debug_store(self) -> dash.dcc.Store:
        return dash.dcc.Store(
            id=self.page.ids.Scattering.debug_store,
            data={"enabled": False},
        )

    def _build_detector_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Scattering detector:"),
                dash.dcc.Dropdown(
                    id=self.page.ids.Scattering.detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_switch_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Scattering.debug_switch,
                    options=[{"label": "Show graph", "value": "enabled"}],
                    value=["enabled"] if self.default.show_graphs else [],
                    switch=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_controls_container(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_estimate_and_threshold_row(),
                dash.html.Br(),
                self._build_histogram_graph(),
                dash.html.Br(),
                self._build_yscale_switch(),
                dash.html.Br(),
                self._build_nbins_row(),
            ],
            id=self.page.ids.Scattering.debug_container,
            style={"display": "none"},
        )

    def _build_nbins_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=self.default.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
        )

    def _build_estimate_and_threshold_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Estimate threshold",
                            id=self.page.ids.Scattering.find_threshold_btn,
                            n_clicks=0,
                            style={"display": "inline-block"},
                        )
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                dash.html.Div(
                    [
                        dash.html.Div("Threshold:", style={"marginRight": "8px"}),
                        dash.dcc.Input(
                            id=self.page.ids.Scattering.threshold_input,
                            type="text",
                            debounce=True,
                            value="",
                            disabled=False,
                            style={"width": "220px"},
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginLeft": "16px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center"},
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Scattering.graph_hist,
                style=self.page.style["graph"],
            ),
            type="default",
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering scattering callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Scattering.debug_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_scattering_graph_visibility_from_runtime_store(runtime_config_data: Any) -> list[str]:
            if not isinstance(runtime_config_data, dict):
                logger.debug(
                    "sync_scattering_graph_visibility_from_runtime_store received non-dict payload=%r. Using Default.show_graphs=%r",
                    runtime_config_data,
                    self.default.show_graphs,
                )
                return ["enabled"] if self.default.show_graphs else []

            resolved_show_graphs = bool(
                runtime_config_data.get("show_graphs", self.default.show_graphs)
            )
            logger.debug(
                "sync_scattering_graph_visibility_from_runtime_store resolved_show_graphs=%r from runtime_config_data=%r",
                resolved_show_graphs,
                runtime_config_data,
            )
            return ["enabled"] if resolved_show_graphs else []

        @dash.callback(
            dash.Output(self.page.ids.Scattering.debug_container, "style"),
            dash.Input(self.page.ids.Scattering.debug_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_debug(debug_switch_value: Any) -> dict:
            return self._toggle_debug_container(debug_switch_value)

        @dash.callback(
            dash.Output(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_scattering_nbins_from_runtime_store(runtime_config_data: Any) -> int:
            return self._resolve_nbins_from_runtime_store(runtime_config_data)

        @dash.callback(
            dash.Output(self.page.ids.Upload.max_events_for_plots_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_max_events_from_runtime_store(runtime_config_data: Any) -> int:
            return self._resolve_max_events_from_runtime_store(runtime_config_data)

        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_hist, "figure"),
            dash.Output(self.page.ids.Scattering.threshold_store, "data"),
            dash.Output(self.page.ids.Scattering.threshold_input, "value"),
            dash.Input(self.page.ids.Scattering.find_threshold_btn, "n_clicks"),
            dash.Input(self.page.ids.Scattering.threshold_input, "value"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input(self.page.ids.Scattering.yscale_switch, "value"),
            dash.Input(self.page.ids.Scattering.debug_switch, "value"),
            dash.State(self.page.ids.Scattering.threshold_store, "data", allow_optional=True),
            dash.State(self.page.ids.Upload.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=True,
        )
        def scattering_section(
            n_clicks_estimate: int,
            threshold_input_value: Any,
            scattering_channel: Any,
            scattering_nbins: Any,
            yscale_selection: Any,
            debug_switch_value: Any,
            scattering_threshold_store_data: Any,
            max_events_for_plots: Any,
        ) -> tuple:
            del n_clicks_estimate

            callback_inputs = self._parse_scattering_callback_inputs(
                threshold_input_value=threshold_input_value,
                scattering_channel=scattering_channel,
                scattering_nbins=scattering_nbins,
                yscale_selection=yscale_selection,
                debug_switch_value=debug_switch_value,
                scattering_threshold_store_data=scattering_threshold_store_data,
                max_events_for_plots=max_events_for_plots,
            )
            return self._run_scattering_callback(callback_inputs).to_tuple()

    def _toggle_debug_container(self, debug_switch_value: Any) -> dict:
        debug_enabled = self._is_switch_enabled(debug_switch_value)
        logger.debug(
            "_toggle_debug_container called with debug_switch_value=%r resolved debug_enabled=%r",
            debug_switch_value,
            debug_enabled,
        )
        return {"display": "block"} if debug_enabled else {"display": "none"}

    def _resolve_nbins_from_runtime_store(self, runtime_config_data: Any) -> int:
        if not isinstance(runtime_config_data, dict):
            logger.debug(
                "_resolve_nbins_from_runtime_store received non-dict payload=%r. Using Default.n_bins_for_plots=%r",
                runtime_config_data,
                self.default.n_bins_for_plots,
            )
            return self.default.n_bins_for_plots

        resolved_nbins = runtime_config_data.get(
            "n_bins_for_plots",
            self.default.n_bins_for_plots,
        )
        logger.debug(
            "_resolve_nbins_from_runtime_store resolved nbins=%r from runtime_config_data=%r",
            resolved_nbins,
            runtime_config_data,
        )
        return resolved_nbins

    def _resolve_max_events_from_runtime_store(self, runtime_config_data: Any) -> int:
        if not isinstance(runtime_config_data, dict):
            logger.debug(
                "_resolve_max_events_from_runtime_store received non-dict payload=%r. Using Default.max_events_for_analysis=%r",
                runtime_config_data,
                self.default.max_events_for_analysis,
            )
            return self.default.max_events_for_analysis

        resolved_max_events = runtime_config_data.get(
            "max_events_for_analysis",
            self.default.max_events_for_analysis,
        )
        logger.debug(
            "_resolve_max_events_from_runtime_store resolved max_events=%r from runtime_config_data=%r",
            resolved_max_events,
            runtime_config_data,
        )
        return resolved_max_events

    def _parse_scattering_callback_inputs(
        self,
        *,
        threshold_input_value: Any,
        scattering_channel: Any,
        scattering_nbins: Any,
        yscale_selection: Any,
        debug_switch_value: Any,
        scattering_threshold_store_data: Any,
        max_events_for_plots: Any,
    ) -> ScatteringCallbackInputs:
        triggered_id = dash.callback_context.triggered_id
        debug_enabled = self._is_switch_enabled(debug_switch_value)
        max_events, nbins = self._parse_limits(
            max_events_for_plots=max_events_for_plots,
            scattering_nbins=scattering_nbins,
        )
        scattering_channel_clean = self._clean_channel_name(scattering_channel)
        stored_threshold = self._extract_stored_threshold(scattering_threshold_store_data)
        manual_threshold = _as_float(threshold_input_value)

        must_estimate = triggered_id in {
            self.page.ids.Scattering.find_threshold_btn,
            self.page.ids.Scattering.detector_dropdown,
            self.page.ids.Scattering.nbins_input,
        }

        parsed_inputs = ScatteringCallbackInputs(
            triggered_id=triggered_id,
            debug_enabled=debug_enabled,
            scattering_channel=scattering_channel_clean,
            nbins=nbins,
            max_events=max_events,
            yscale_selection=yscale_selection,
            manual_threshold=manual_threshold,
            stored_threshold=stored_threshold,
            must_estimate=must_estimate,
        )

        logger.debug("Parsed scattering callback inputs=%r", parsed_inputs)
        return parsed_inputs

    def _run_scattering_callback(
        self,
        callback_inputs: ScatteringCallbackInputs,
    ) -> ScatteringResult:
        logger.debug("_run_scattering_callback called with callback_inputs=%r", callback_inputs)

        try:
            threshold_value, threshold_input_output = self._resolve_threshold(
                must_estimate=callback_inputs.must_estimate,
                scattering_channel=callback_inputs.scattering_channel,
                nbins=callback_inputs.nbins,
                max_events=callback_inputs.max_events,
                manual_thr=callback_inputs.manual_threshold,
                store_thr=callback_inputs.stored_threshold,
            )

            threshold_store_payload = self._build_threshold_store_payload(
                scattering_channel=callback_inputs.scattering_channel,
                threshold_value=threshold_value,
                nbins=callback_inputs.nbins,
            )

            figure = self._build_scattering_histogram(
                debug_enabled=callback_inputs.debug_enabled,
                scattering_channel=callback_inputs.scattering_channel,
                nbins=callback_inputs.nbins,
                max_events=callback_inputs.max_events,
                yscale_selection=callback_inputs.yscale_selection,
                threshold_value=threshold_value,
            )
        except Exception:
            logger.exception(
                "Failed in _run_scattering_callback for callback_inputs=%r",
                callback_inputs,
            )
            raise

        result = ScatteringResult(
            figure=figure,
            scattering_threshold_store=threshold_store_payload,
            scattering_threshold_input_value=threshold_input_output,
        )

        logger.debug("Returning scattering result=%r", result)
        return result

    def _is_switch_enabled(self, switch_value: Any) -> bool:
        return isinstance(switch_value, list) and ("enabled" in switch_value)

    def _clean_channel_name(self, scattering_channel: Any) -> str:
        if scattering_channel is None:
            return ""

        scattering_channel_clean = str(scattering_channel).strip()

        if scattering_channel_clean.lower() == "none":
            return ""

        return scattering_channel_clean

    def _extract_stored_threshold(self, scattering_threshold_store_data: Any) -> Optional[float]:
        if not isinstance(scattering_threshold_store_data, dict):
            return None

        return _as_float(scattering_threshold_store_data.get("threshold"))

    def _build_threshold_store_payload(
        self,
        *,
        scattering_channel: str,
        threshold_value: float,
        nbins: int,
    ) -> dict:
        return {
            "scattering_channel": scattering_channel or None,
            "threshold": float(threshold_value),
            "nbins": int(nbins),
        }

    def _parse_limits(self, *, max_events_for_plots: Any, scattering_nbins: Any) -> Tuple[int, int]:
        max_events = _as_int(
            max_events_for_plots if max_events_for_plots is not None else self.default.max_events_for_analysis,
            default=self.default.max_events_for_analysis,
            min_value=1_000,
            max_value=5_000_000,
        )

        nbins = _as_int(
            scattering_nbins,
            default=self.default.n_bins_for_plots,
            min_value=10,
            max_value=5000,
        )

        return max_events, nbins

    def _resolve_threshold(
        self,
        *,
        must_estimate: bool,
        scattering_channel: str,
        nbins: int,
        max_events: int,
        manual_thr: Optional[float],
        store_thr: Optional[float],
    ) -> Tuple[float, Any]:
        logger.debug(
            "_resolve_threshold called with must_estimate=%r scattering_channel=%r nbins=%r "
            "max_events=%r manual_thr=%r store_thr=%r",
            must_estimate,
            scattering_channel,
            nbins,
            max_events,
            manual_thr,
            store_thr,
        )

        if must_estimate:
            if self.page.backend is None:
                logger.debug("_resolve_threshold cannot estimate because backend is None.")
                return 0.0, dash.no_update

            if not scattering_channel:
                logger.debug("_resolve_threshold cannot estimate because scattering_channel is empty.")
                return 0.0, dash.no_update

            try:
                response = self.page.backend.process_scattering(
                    {
                        "operation": "estimate_scattering_threshold",
                        "column": scattering_channel,
                        "nbins": int(nbins),
                        "number_of_points": int(max_events),
                    }
                )
            except Exception:
                logger.exception(
                    "Backend threshold estimation failed for scattering_channel=%r nbins=%r max_events=%r",
                    scattering_channel,
                    nbins,
                    max_events,
                )
                raise

            threshold_value = _as_float(response.get("threshold")) or 0.0
            logger.debug(
                "_resolve_threshold estimated threshold_value=%r from response=%r",
                threshold_value,
                response,
            )
            return float(threshold_value), f"{float(threshold_value):.6g}"

        if manual_thr is not None:
            logger.debug("_resolve_threshold using manual threshold=%r", manual_thr)
            return float(manual_thr), dash.no_update

        if store_thr is not None:
            logger.debug("_resolve_threshold using stored threshold=%r", store_thr)
            return float(store_thr), dash.no_update

        logger.debug("_resolve_threshold fell back to default threshold=0.0")
        return 0.0, dash.no_update

    def _build_scattering_histogram(
        self,
        *,
        debug_enabled: bool,
        scattering_channel: str,
        nbins: int,
        max_events: int,
        yscale_selection: Any,
        threshold_value: float,
    ) -> go.Figure:
        logger.debug(
            "_build_scattering_histogram called with debug_enabled=%r scattering_channel=%r "
            "nbins=%r max_events=%r yscale_selection=%r threshold_value=%r",
            debug_enabled,
            scattering_channel,
            nbins,
            max_events,
            yscale_selection,
            threshold_value,
        )

        if not debug_enabled:
            return _make_info_figure("Debug graph is disabled.")

        if self.page.backend is None:
            return _make_info_figure("Backend is not available.")

        if not scattering_channel:
            return _make_info_figure("Select a scattering detector first.")

        if not getattr(self.page.backend, "file_path", None):
            return _make_info_figure("No FCS file is loaded.")

        use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)

        try:
            with FCSFile(self.page.backend.file_path, writable=False) as fcs_file:
                values = fcs_file.column_copy(scattering_channel, dtype=float, n=max_events)
        except Exception:
            logger.exception(
                "Failed to read scattering histogram values from file_path=%r channel=%r max_events=%r",
                self.page.backend.file_path,
                scattering_channel,
                max_events,
            )
            raise

        if values is None or len(values) == 0:
            return _make_info_figure("No data available for the selected detector.")

        figure = make_histogram_with_lines(
            values=values,
            nbins=nbins,
            xaxis_title="Scattering (a.u.)",
            line_positions=[float(threshold_value)],
            line_labels=[f"{float(threshold_value):.3g}"],
        )
        figure.update_yaxes(type="log" if use_log else "linear")
        figure.update_layout(separators=".,")

        return figure