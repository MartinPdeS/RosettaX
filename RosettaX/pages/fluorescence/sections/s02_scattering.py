from dataclasses import dataclass
from typing import Any, Optional, Tuple
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines, _make_info_figure
from RosettaX.utils.casting import _as_float, _as_int


logger = logging.getLogger(__name__)


@dataclass
class ScatteringResult:
    """
    Container for the Dash outputs of the scattering callback.

    This keeps the callback return logic clean and localizes the Dash output ordering.
    """

    figure: Any = dash.no_update
    scattering_threshold_store: Any = dash.no_update
    scattering_threshold_input_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert to the tuple expected by the Dash callback Outputs.

        Returns
        -------
        tuple
            (figure, scattering_threshold_store, scattering_threshold_input_value)
        """
        return (
            self.figure,
            self.scattering_threshold_store,
            self.scattering_threshold_input_value,
        )


class ScatteringSection:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ScatteringSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        """
        Build the Dash layout for the scattering section.

        Returns
        -------
        dbc.Card
            Card containing the scattering controls and histogram plot.
        """
        logger.debug("Building scattering section layout.")
        return dbc.Card(
            [
                dbc.CardHeader("2. Scattering channel"),
                dbc.CardBody(self._build_body_children()),
            ]
        )

    def _build_body_children(self) -> list:
        """
        Build the list of Dash components shown in the scattering section body.

        Returns
        -------
        list
            List of Dash components used as children of the CardBody.
        """
        logger.debug("Building scattering section body children.")
        return [
            self._build_debug_store(),
            dash.html.Br(),
            self._build_detector_row(),
            dash.html.Br(),
            self._build_debug_switch_row(),
            dash.html.Br(),
            self._build_debug_controls_container(),
        ]

    def _build_debug_store(self) -> dash.dcc.Store:
        """
        Store the local debug visibility state for this section.

        Returns
        -------
        dash.dcc.Store
            Store containing whether debug controls are visible.
        """
        logger.debug("Building scattering debug store.")
        return dash.dcc.Store(
            id=self.page.ids.Scattering.debug_store,
            data={"enabled": False},
        )

    def _build_detector_row(self) -> dash.html.Div:
        """
        Build the dropdown row for selecting the scattering detector channel.

        Returns
        -------
        dash.html.Div
            Row containing a label and dropdown.
        """
        logger.debug("Building scattering detector row.")
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
        """
        Build the row containing the local debug switch.

        Returns
        -------
        dash.html.Div
            Row containing the debug switch.
        """
        logger.debug("Building scattering debug switch row.")
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Scattering.debug_switch,
                    options=[{"label": "Show debug graph", "value": "enabled"}],
                    value=[],
                    switch=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_controls_container(self) -> dash.html.Div:
        """
        Build the container that holds all debug-only controls and graph.

        Returns
        -------
        dash.html.Div
            Container whose visibility is controlled by the local debug switch.
        """
        logger.debug("Building scattering debug controls container.")
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
        """
        Build the input row for selecting histogram bin count.

        Returns
        -------
        dash.html.Div
            Row containing a label and numeric input.
        """
        runtime_config = RuntimeConfig()
        logger.debug(
            "Building scattering nbins row with default n_bins_for_plots=%r",
            runtime_config.Default.n_bins_for_plots,
        )

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
                ),
            ],
            style=styling.CARD,
        )

    def _build_estimate_and_threshold_row(self) -> dash.html.Div:
        """
        Build the row containing the estimate button and the threshold input.

        Returns
        -------
        dash.html.Div
            Row with estimate threshold button and threshold text input.
        """
        logger.debug("Building scattering estimate and threshold row.")
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
        """
        Build the y scale toggle (linear or log counts).

        Returns
        -------
        dbc.Checklist
            Switch to toggle log y axis.
        """
        logger.debug("Building scattering yscale switch.")
        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        """
        Build the histogram graph wrapper.

        Returns
        -------
        dash.dcc.Loading
            Loading wrapper containing the plotly graph.
        """
        logger.debug("Building scattering histogram graph.")
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Scattering.graph_hist,
                style=self.page.style["graph"],
            ),
            type="default",
        )

    def _register_callbacks(self) -> None:
        """
        Register callbacks for scattering threshold estimation and histogram display.
        """
        logger.debug("Registering scattering callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Scattering.debug_container, "style"),
            dash.Input(self.page.ids.Scattering.debug_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_debug(debug_switch_value: Any) -> dict:
            debug_enabled = self._is_switch_enabled(debug_switch_value)
            logger.debug(
                "toggle_scattering_debug called with debug_switch_value=%r resolved debug_enabled=%r",
                debug_switch_value,
                debug_enabled,
            )
            return {"display": "block"} if debug_enabled else {"display": "none"}

        @dash.callback(
            dash.Output(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_scattering_nbins_from_runtime_store(runtime_config_data: Any) -> int:
            runtime_config = RuntimeConfig()
            logger.debug(
                "sync_scattering_nbins_from_runtime_store called with runtime_config_data=%r",
                runtime_config_data,
            )

            if not isinstance(runtime_config_data, dict):
                logger.debug(
                    "Runtime config store is not a dict. Using default n_bins_for_plots=%r",
                    runtime_config.Default.n_bins_for_plots,
                )
                return runtime_config.Default.n_bins_for_plots

            resolved_nbins = runtime_config_data.get(
                "n_bins_for_plots",
                runtime_config.Default.n_bins_for_plots,
            )
            logger.debug("Resolved scattering nbins from runtime store: %r", resolved_nbins)
            return resolved_nbins

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
            dash.State(self.page.ids.Load.max_events_for_plots_input, "value", allow_optional=True),
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
            triggered_id = dash.callback_context.triggered_id
            debug_enabled = self._is_switch_enabled(debug_switch_value)

            logger.debug(
                "scattering_section called with triggered_id=%r n_clicks_estimate=%r "
                "threshold_input_value=%r scattering_channel=%r scattering_nbins=%r "
                "yscale_selection=%r debug_switch_value=%r scattering_threshold_store_data=%r "
                "max_events_for_plots=%r",
                triggered_id,
                n_clicks_estimate,
                threshold_input_value,
                scattering_channel,
                scattering_nbins,
                yscale_selection,
                debug_switch_value,
                scattering_threshold_store_data,
                max_events_for_plots,
            )

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

            logger.debug(
                "Resolved scattering callback state: debug_enabled=%r max_events=%r nbins=%r "
                "scattering_channel_clean=%r stored_threshold=%r manual_threshold=%r must_estimate=%r",
                debug_enabled,
                max_events,
                nbins,
                scattering_channel_clean,
                stored_threshold,
                manual_threshold,
                must_estimate,
            )

            try:
                threshold_value, threshold_input_output = self._resolve_threshold(
                    must_estimate=must_estimate,
                    scattering_channel=scattering_channel_clean,
                    nbins=nbins,
                    max_events=max_events,
                    manual_thr=manual_threshold,
                    store_thr=stored_threshold,
                )

                next_store = self._build_threshold_store_payload(
                    scattering_channel=scattering_channel_clean,
                    threshold_value=threshold_value,
                    nbins=nbins,
                )

                figure = self._build_scattering_histogram(
                    debug_enabled=debug_enabled,
                    scattering_channel=scattering_channel_clean,
                    nbins=nbins,
                    max_events=max_events,
                    yscale_selection=yscale_selection,
                    threshold_value=threshold_value,
                )
            except Exception:
                logger.exception(
                    "Failed inside scattering_section callback with triggered_id=%r "
                    "scattering_channel_clean=%r nbins=%r max_events=%r",
                    triggered_id,
                    scattering_channel_clean,
                    nbins,
                    max_events,
                )
                raise

            logger.debug(
                "scattering_section returning threshold_value=%r threshold_input_output=%r next_store=%r",
                threshold_value,
                threshold_input_output,
                next_store,
            )

            return ScatteringResult(
                figure=figure,
                scattering_threshold_store=next_store,
                scattering_threshold_input_value=threshold_input_output,
            ).to_tuple()

    def _is_switch_enabled(self, switch_value: Any) -> bool:
        """
        Return whether a checklist-style switch is enabled.
        """
        enabled = isinstance(switch_value, list) and ("enabled" in switch_value)
        logger.debug("_is_switch_enabled called with switch_value=%r resolved=%r", switch_value, enabled)
        return enabled

    def _clean_channel_name(self, scattering_channel: Any) -> str:
        """
        Normalize the scattering channel value to a clean string.

        Parameters
        ----------
        scattering_channel : Any
            Raw channel value from Dash.

        Returns
        -------
        str
            Cleaned channel name or empty string.
        """
        if scattering_channel is None:
            logger.debug("_clean_channel_name received None and returned empty string.")
            return ""

        scattering_channel_clean = str(scattering_channel).strip()

        if scattering_channel_clean.lower() == "none":
            logger.debug(
                "_clean_channel_name received string representation of None=%r and returned empty string.",
                scattering_channel,
            )
            return ""

        logger.debug(
            "_clean_channel_name called with scattering_channel=%r returned=%r",
            scattering_channel,
            scattering_channel_clean,
        )
        return scattering_channel_clean

    def _extract_stored_threshold(self, scattering_threshold_store_data: Any) -> Optional[float]:
        """
        Extract a numeric threshold from the threshold store payload.

        Parameters
        ----------
        scattering_threshold_store_data : Any
            Store payload.

        Returns
        -------
        Optional[float]
            Parsed threshold or None.
        """
        if not isinstance(scattering_threshold_store_data, dict):
            logger.debug(
                "_extract_stored_threshold received non-dict store payload=%r and returned None.",
                scattering_threshold_store_data,
            )
            return None

        extracted_threshold = _as_float(scattering_threshold_store_data.get("threshold"))
        logger.debug(
            "_extract_stored_threshold extracted threshold=%r from store payload=%r",
            extracted_threshold,
            scattering_threshold_store_data,
        )
        return extracted_threshold

    def _build_threshold_store_payload(
        self,
        *,
        scattering_channel: str,
        threshold_value: float,
        nbins: int,
    ) -> dict:
        """
        Build the payload stored in the threshold store.

        Parameters
        ----------
        scattering_channel : str
            Clean scattering channel name.
        threshold_value : float
            Threshold value.
        nbins : int
            Number of bins.

        Returns
        -------
        dict
            Threshold store payload.
        """
        payload = {
            "scattering_channel": scattering_channel or None,
            "threshold": float(threshold_value),
            "nbins": int(nbins),
        }
        logger.debug("_build_threshold_store_payload returning payload=%r", payload)
        return payload

    def _parse_limits(self, *, max_events_for_plots: Any, scattering_nbins: Any) -> Tuple[int, int]:
        """
        Parse and clamp max events and number of bins.

        Parameters
        ----------
        max_events_for_plots : Any
            User input for max events.
        scattering_nbins : Any
            User input for histogram bin count.

        Returns
        -------
        Tuple[int, int]
            (max_events, nbins) clamped to safe ranges.
        """
        runtime_config = RuntimeConfig()

        max_events = _as_int(
            max_events_for_plots if max_events_for_plots is not None else runtime_config.Default.max_events_for_analysis,
            default=runtime_config.Default.max_events_for_analysis,
            min_value=10_000,
            max_value=5_000_000,
        )

        nbins = _as_int(
            scattering_nbins,
            default=runtime_config.Default.n_bins_for_plots,
            min_value=10,
            max_value=5000,
        )

        logger.debug(
            "_parse_limits called with max_events_for_plots=%r scattering_nbins=%r resolved max_events=%r nbins=%r",
            max_events_for_plots,
            scattering_nbins,
            max_events,
            nbins,
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
        """
        Resolve the threshold value to use and decide whether to update the input field.

        Parameters
        ----------
        must_estimate : bool
            Whether the backend estimation must run.
        scattering_channel : str
            Clean selected scattering channel name.
        nbins : int
            Histogram bin count.
        max_events : int
            Maximum number of points used for estimation.
        manual_thr : Optional[float]
            Parsed threshold value from user input, if valid.
        store_thr : Optional[float]
            Previously stored threshold value, if present.

        Returns
        -------
        Tuple[float, Any]
            (threshold_value, threshold_input_output)
        """
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
        """
        Build the scattering histogram figure with a vertical threshold line.

        Parameters
        ----------
        debug_enabled : bool
            Whether the local debug mode is enabled.
        scattering_channel : str
            Clean scattering channel name.
        nbins : int
            Number of bins.
        max_events : int
            Maximum number of events to read.
        yscale_selection : Any
            Checklist value for y scale.
        threshold_value : float
            Threshold value to draw.

        Returns
        -------
        go.Figure
            Plotly histogram figure or an info figure.
        """
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
            logger.debug("_build_scattering_histogram returning info figure because debug graph is disabled.")
            return _make_info_figure("Debug graph is disabled.")

        if self.page.backend is None:
            logger.debug("_build_scattering_histogram returning info figure because backend is not available.")
            return _make_info_figure("Backend is not available.")

        if not scattering_channel:
            logger.debug("_build_scattering_histogram returning info figure because no scattering channel is selected.")
            return _make_info_figure("Select a scattering detector first.")

        if not getattr(self.page.backend, "file_path", None):
            logger.debug("_build_scattering_histogram returning info figure because no FCS file is loaded.")
            return _make_info_figure("No FCS file is loaded.")

        use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)
        logger.debug(
            "_build_scattering_histogram resolved use_log=%r for yscale_selection=%r",
            use_log,
            yscale_selection,
        )

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
            logger.debug(
                "_build_scattering_histogram returning info figure because no data was available for channel=%r",
                scattering_channel,
            )
            return _make_info_figure("No data available for the selected detector.")

        logger.debug(
            "_build_scattering_histogram loaded %r values for channel=%r",
            len(values),
            scattering_channel,
        )

        figure = make_histogram_with_lines(
            values=values,
            nbins=nbins,
            xaxis_title="Scattering (a.u.)",
            line_positions=[float(threshold_value)],
            line_labels=[f"{float(threshold_value):.3g}"],
        )
        figure.update_yaxes(type="log" if use_log else "linear")
        figure.update_layout(separators=".,")

        logger.debug(
            "_build_scattering_histogram built figure successfully for channel=%r with threshold_value=%r",
            scattering_channel,
            threshold_value,
        )
        return figure