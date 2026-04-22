from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines, _make_info_figure
from RosettaX.utils import casting
from RosettaX.pages.fluorescence.services.gating import (
    build_threshold_store_payload,
    clean_channel_name,
    extract_stored_threshold,
    is_switch_enabled,
    parse_limits,
    resolve_threshold,
)


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


class Gating:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ScatteringSection with page=%r", page)

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        return RuntimeConfig.from_default_profile()

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
        runtime_config = self._get_default_runtime_config()

        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Scattering.debug_switch,
                    options=[{"label": "Show graph", "value": "enabled"}],
                    value=["enabled"] if runtime_config.get_show_graphs(default=True) else [],
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
        runtime_config = self._get_default_runtime_config()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.get_int("calibration.n_bins_for_plots", default=100),
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
        runtime_config = self._get_default_runtime_config()
        histogram_scale = runtime_config.get_str("calibration.histogram_scale", default="log")

        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"] if histogram_scale == "log" else [],
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
            dash.Output(self.page.ids.Scattering.yscale_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_scattering_yscale_from_runtime_store(runtime_config_data: Any) -> list[str]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )
            histogram_scale = runtime_config.get_str("calibration.histogram_scale", default="log")

            logger.debug(
                "sync_scattering_yscale_from_runtime_store resolved histogram_scale=%r",
                histogram_scale,
            )

            return ["log"] if histogram_scale == "log" else []

        @dash.callback(
            dash.Output(self.page.ids.Scattering.debug_switch, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_scattering_graph_visibility_from_runtime_store(runtime_config_data: Any) -> list[str]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )
            resolved_show_graphs = runtime_config.get_show_graphs(default=True)

            logger.debug(
                "sync_scattering_graph_visibility_from_runtime_store resolved_show_graphs=%r",
                resolved_show_graphs,
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
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )
            resolved_nbins = runtime_config.get_int("calibration.n_bins_for_plots", default=100)

            logger.debug(
                "sync_scattering_nbins_from_runtime_store resolved_nbins=%r",
                resolved_nbins,
            )
            return resolved_nbins

        @dash.callback(
            dash.Output(self.page.ids.Upload.max_events_for_plots_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_max_events_from_runtime_store(runtime_config_data: Any) -> int:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )
            resolved_max_events = runtime_config.get_int("calibration.max_events_for_analysis", default=10000)

            logger.debug(
                "sync_max_events_from_runtime_store resolved_max_events=%r",
                resolved_max_events,
            )
            return resolved_max_events

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
            dash.State("runtime-config-store", "data"),
            prevent_initial_call=True,
        )
        def update_scattering_threshold_and_histogram(
            n_clicks_estimate: int,
            threshold_input_value: Any,
            scattering_channel: Any,
            scattering_nbins: Any,
            yscale_selection: Any,
            debug_switch_value: Any,
            scattering_threshold_store_data: Any,
            max_events_for_plots: Any,
            runtime_config_data: Any,
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
                runtime_config_data=runtime_config_data,
            )
            return self._run_scattering_callback(callback_inputs).to_tuple()

    def _toggle_debug_container(self, debug_switch_value: Any) -> dict:
        debug_enabled = is_switch_enabled(debug_switch_value)
        logger.debug(
            "_toggle_debug_container called with debug_switch_value=%r resolved debug_enabled=%r",
            debug_switch_value,
            debug_enabled,
        )
        return {"display": "block"} if debug_enabled else {"display": "none"}

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
        runtime_config_data: Any,
    ) -> ScatteringCallbackInputs:
        triggered_id = dash.callback_context.triggered_id
        debug_enabled = is_switch_enabled(debug_switch_value)

        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )
        default_max_events = runtime_config.get_int("calibration.max_events_for_analysis", default=10000)
        default_nbins = runtime_config.get_int("calibration.n_bins_for_plots", default=100)

        parsed_limits = parse_limits(
            max_events_for_plots=max_events_for_plots,
            scattering_nbins=scattering_nbins,
            default_max_events=default_max_events,
            default_nbins=default_nbins,
        )

        scattering_channel_clean = clean_channel_name(scattering_channel)
        stored_threshold = extract_stored_threshold(scattering_threshold_store_data)
        manual_threshold = casting._as_float(threshold_input_value)

        must_estimate = triggered_id in {
            self.page.ids.Scattering.find_threshold_btn,
            self.page.ids.Scattering.detector_dropdown,
            self.page.ids.Scattering.nbins_input,
        }

        parsed_inputs = ScatteringCallbackInputs(
            triggered_id=triggered_id,
            debug_enabled=debug_enabled,
            scattering_channel=scattering_channel_clean,
            nbins=parsed_limits.nbins,
            max_events=parsed_limits.max_events,
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
            threshold_value, threshold_input_output = resolve_threshold(
                page_backend=self.page.backend,
                must_estimate=callback_inputs.must_estimate,
                scattering_channel=callback_inputs.scattering_channel,
                nbins=callback_inputs.nbins,
                max_events=callback_inputs.max_events,
                manual_thr=callback_inputs.manual_threshold,
                store_thr=callback_inputs.stored_threshold,
                logger=logger,
            )

            threshold_store_payload = build_threshold_store_payload(
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