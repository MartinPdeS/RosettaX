from dataclasses import dataclass
from typing import Any, Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines, _make_info_figure
from RosettaX.utils.casting import _as_float, _as_int


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

    def get_layout(self) -> dbc.Card:
        """
        Build the Dash layout for the scattering section.

        Returns
        -------
        dbc.Card
            Card containing the scattering controls and histogram plot.
        """
        return dbc.Card(
            [
                dbc.CardHeader("2. Scattering channel"),
                dbc.CardBody(self._scattering_build_body_children()),
            ]
        )

    def _scattering_build_body_children(self) -> list:
        """
        Build the list of Dash components shown in the scattering section body.

        Returns
        -------
        list
            List of Dash components used as children of the CardBody.
        """
        children = [
            self.debug_store(),
            dash.html.Br(),
            self.detector_row(),
            dash.html.Br(),
            self.debug_switch_row(),
            dash.html.Br(),
            self.debug_controls_container(),
        ]

        return children

    def debug_store(self) -> dash.dcc.Store:
        """
        Store the local debug visibility state for this section.

        Returns
        -------
        dash.dcc.Store
            Store containing whether debug controls are visible.
        """
        return dash.dcc.Store(
            id=self.page.ids.Scattering.debug_store,
            data={"enabled": False},
        )

    def detector_row(self) -> dash.html.Div:
        """
        Build the dropdown row for selecting the scattering detector channel.

        Returns
        -------
        dash.html.Div
            Row containing a label and dropdown.
        """
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

    def debug_switch_row(self) -> dash.html.Div:
        """
        Build the row containing the local debug switch.

        Returns
        -------
        dash.html.Div
            Row containing the debug switch.
        """
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

    def debug_controls_container(self) -> dash.html.Div:
        """
        Build the container that holds all debug-only controls and graph.

        Returns
        -------
        dash.html.Div
            Container whose visibility is controlled by the local debug switch.
        """
        return dash.html.Div(
            [
                self._scattering_estimate_and_threshold_row(),
                dash.html.Br(),
                self._scattering_histogram_graph(),
                dash.html.Br(),
                self._scattering_yscale_switch(),
                dash.html.Br(),
                self._scattering_nbins_row(),
            ],
            id=self.page.ids.Scattering.debug_container,
            style={"display": "none"},
        )

    def _scattering_nbins_row(self) -> dash.html.Div:
        """
        Build the input row for selecting histogram bin count.

        Returns
        -------
        dash.html.Div
            Row containing a label and numeric input.
        """
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
        )

    def _scattering_estimate_and_threshold_row(self) -> dash.html.Div:
        """
        Build the row containing the estimate button and the threshold input.

        Returns
        -------
        dash.html.Div
            Row with estimate threshold button and threshold text input.
        """
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

    def _scattering_yscale_switch(self) -> dbc.Checklist:
        """
        Build the y scale toggle (linear or log counts).

        Returns
        -------
        dbc.Checklist
            Switch to toggle log y axis.
        """
        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
        )

    def _scattering_histogram_graph(self) -> dash.dcc.Loading:
        """
        Build the histogram graph wrapper.

        Returns
        -------
        dash.dcc.Loading
            Loading wrapper containing the plotly graph.
        """
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

        Callback behavior:
        - The debug switch controls visibility of the debug container.
        - Threshold is estimated when triggered by estimate button, detector dropdown change, or nbins change.
        - Manual threshold from input is used when valid and when the input triggered the callback.
        - Histogram is only built when debug mode is enabled locally.
        """

        @dash.callback(
            dash.Output(self.page.ids.Scattering.debug_container, "style"),
            dash.Input(self.page.ids.Scattering.debug_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_debug(debug_switch_value: Any) -> dict:
            debug_enabled = isinstance(debug_switch_value, list) and ("enabled" in debug_switch_value)
            return {"display": "block"} if debug_enabled else {"display": "none"}


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

            debug_enabled = isinstance(debug_switch_value, list) and ("enabled" in debug_switch_value)

            max_events, nbins = self._parse_limits(
                max_events_for_plots=max_events_for_plots,
                scattering_nbins=scattering_nbins,
            )

            store_thr = None
            if isinstance(scattering_threshold_store_data, dict):
                store_thr = _as_float(scattering_threshold_store_data.get("threshold"))

            manual_thr = _as_float(threshold_input_value)

            must_estimate = triggered_id in {
                self.page.ids.Scattering.find_threshold_btn,
                self.page.ids.Scattering.detector_dropdown,
                self.page.ids.Scattering.nbins_input,
            }

            thr, threshold_out = self._resolve_threshold(
                must_estimate=must_estimate,
                scattering_channel=scattering_channel,
                nbins=nbins,
                max_events=max_events,
                manual_thr=manual_thr,
                store_thr=store_thr,
            )

            next_store = {
                "scattering_channel": str(scattering_channel) if scattering_channel is not None else None,
                "threshold": float(thr),
                "nbins": int(nbins),
            }

            fig = self._build_scattering_histogram(
                debug_enabled=debug_enabled,
                scattering_channel=scattering_channel,
                nbins=nbins,
                max_events=max_events,
                yscale_selection=yscale_selection,
                thr=thr,
            )

            return ScatteringResult(
                figure=fig,
                scattering_threshold_store=next_store,
                scattering_threshold_input_value=threshold_out,
            ).to_tuple()

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
            max_events_for_plots if max_events_for_plots is not None else runtime_config.max_events_for_analysis,
            default=runtime_config.max_events_for_analysis,
            min_value=10_000,
            max_value=5_000_000,
        )

        nbins = _as_int(
            scattering_nbins,
            default=runtime_config.n_bins_for_plots,
            min_value=10,
            max_value=5000,
        )

        return max_events, nbins

    def _resolve_threshold(
        self,
        *,
        must_estimate: bool,
        scattering_channel: Any,
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
        scattering_channel : Any
            Selected scattering channel name.
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
            threshold_input_output is either a formatted string when estimation ran,
            or dash.no_update when we should not overwrite user input.
        """
        if must_estimate:
            if self.page.backend is None:
                return 0.0, dash.no_update

            response = self.page.backend.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": str(scattering_channel),
                    "nbins": int(nbins),
                    "number_of_points": int(max_events),
                }
            )
            thr = _as_float(response.get("threshold")) or 0.0
            return float(thr), f"{float(thr):.6g}"

        if manual_thr is not None:
            return float(manual_thr), dash.no_update

        if store_thr is not None:
            return float(store_thr), dash.no_update

        return 0.0, dash.no_update

    def _build_scattering_histogram(
        self,
        *,
        debug_enabled: bool,
        scattering_channel: Any,
        nbins: int,
        max_events: int,
        yscale_selection: Any,
        thr: float,
    ) -> go.Figure:
        """
        Build the scattering histogram figure with a vertical threshold line.
        """
        if not debug_enabled:
            return _make_info_figure("Debug graph is disabled.")

        if self.page.backend is None:
            return _make_info_figure("Backend is not available.")

        if scattering_channel in (None, ""):
            return _make_info_figure("Select a scattering detector first.")

        use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)

        with FCSFile(self.page.backend.file_path, writable=False) as fcs:
            values = fcs.column_copy(str(scattering_channel), dtype=float, n=max_events)

        if values is None or len(values) == 0:
            return _make_info_figure("No data available for the selected detector.")

        fig = make_histogram_with_lines(
            values=values,
            nbins=nbins,
            xaxis_title="Scattering (a.u.)",
            line_positions=[float(thr)],
            line_labels=[f"{float(thr):.3g}"],
        )
        fig.update_yaxes(type="log" if use_log else "linear")
        fig.update_layout(separators=".,")
        return fig

