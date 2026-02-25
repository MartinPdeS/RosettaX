from dataclasses import dataclass
from typing import Any, Optional, Tuple
import numpy as np

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages import styling
from RosettaX.pages.runtime_config import get_runtime_config
from RosettaX.reader import FCSFile
from RosettaX.pages.fluorescence.utils import make_histogram_with_lines

@dataclass(frozen=True)
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
    def _scattering_get_layout(self) -> dbc.Card:
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
        runtime_config = get_runtime_config()

        children = [
            dash.html.Br(),
            self._scattering_detector_row(),
            dash.html.Br(),
            self._scattering_estimate_and_threshold_row(),
            dash.html.Br(),
            self._scattering_histogram_graph(),
            dash.html.Br(),
            self._scattering_yscale_switch(),
            dash.html.Br(),
            self._scattering_nbins_row(),
        ]

        return children

    def _scattering_detector_row(self) -> dash.html.Div:
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
                    id=self.ids.scattering_detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                ),
            ],
            style=styling.CARD,
        )

    def _scattering_nbins_row(self) -> dash.html.Div:
        """
        Build the input row for selecting histogram bin count.

        Returns
        -------
        dash.html.Div
            Row containing a label and numeric input.
        """
        runtime_config = get_runtime_config()
        return dash.html.Div(
            [
                dash.html.Div("number of bins:"),
                dash.dcc.Input(
                    id=self.ids.scattering_nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
            hidden=runtime_config.fluorescence_show_scattering_controls is False,
        )

    def _scattering_estimate_and_threshold_row(self) -> dash.html.Div:
        """
        Build the row containing the estimate button and the threshold input.

        Returns
        -------
        dash.html.Div
            Row with estimate threshold button and threshold text input.
        """
        runtime_config = get_runtime_config()

        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Estimate threshold",
                            id=self.ids.scattering_find_threshold_btn,
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
                            id=self.ids.scattering_threshold_input,
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
            hidden=runtime_config.fluorescence_show_scattering_controls is False,
        )

    def _scattering_yscale_switch(self) -> dbc.Checklist:
        """
        Build the y scale toggle (linear or log counts).

        Returns
        -------
        dbc.Checklist
            Switch to toggle log y axis.
        """
        runtime_config = get_runtime_config()

        return dbc.Checklist(
            id=self.ids.scattering_yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "none"} if runtime_config.fluorescence_show_scattering_controls is False else {"display": "block"},
        )

    def _scattering_histogram_graph(self) -> dash.dcc.Loading:
        """
        Build the histogram graph wrapper.

        Returns
        -------
        dash.dcc.Loading
            Loading wrapper containing the plotly graph.
        """
        runtime_config = get_runtime_config()
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.ids.graph_scattering_hist,
                style={"display": "none"} if runtime_config.fluorescence_show_scattering_controls is False else self.graph_style,
            ),
            type="default",
        )

    def _scattering_register_callbacks(self) -> None:
        """
        Register callbacks for scattering threshold estimation and histogram display.

        Callback behavior:
        - Estimates threshold when triggered by estimate button, detector dropdown change, or nbins change.
        - Uses manual threshold from input (if valid) when triggered by the threshold input.
        - Rebuilds the histogram and vertical line using the resolved threshold.
        """
        @dash.callback(
            dash.Output(self.ids.graph_scattering_hist, "figure"),
            dash.Output(self.ids.scattering_threshold_store, "data"),
            dash.Output(self.ids.scattering_threshold_input, "value"),
            dash.Input(self.ids.scattering_find_threshold_btn, "n_clicks"),
            dash.Input(self.ids.scattering_threshold_input, "value"),
            dash.Input(self.ids.scattering_detector_dropdown, "value"),
            dash.Input(self.ids.scattering_nbins_input, "value"),
            dash.Input(self.ids.scattering_yscale_switch, "value"),
            dash.State(self.ids.scattering_threshold_store, "data", allow_optional=True),
            dash.State(self.ids.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=True,
        )
        def scattering_section(
            n_clicks_estimate: int,
            threshold_input_value: Any,
            scattering_channel: Any,
            scattering_nbins: Any,
            yscale_selection: Any,
            scattering_threshold_store_data: Any,
            max_events_for_plots: Any,
        ) -> tuple:
            runtime_config = get_runtime_config()
            triggered_id = dash.callback_context.triggered_id

            max_events, nbins = self._parse_limits(
                max_events_for_plots=max_events_for_plots,
                scattering_nbins=scattering_nbins,
            )

            store_thr = None
            if isinstance(scattering_threshold_store_data, dict):
                store_thr = self._as_float(scattering_threshold_store_data.get("threshold"))

            manual_thr = self._as_float(threshold_input_value)

            must_estimate = triggered_id in {
                self.ids.scattering_find_threshold_btn,
                self.ids.scattering_detector_dropdown,
                self.ids.scattering_nbins_input,
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
                "scattering_channel": str(scattering_channel),
                "threshold": float(thr),
                "nbins": int(nbins),
            }

            fig = self._build_scattering_histogram(
                runtime_config=runtime_config,
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
        runtime_config = get_runtime_config()

        max_events = self._as_int(
            max_events_for_plots if max_events_for_plots is not None else runtime_config.max_events_for_analysis,
            default=runtime_config.max_events_for_analysis,
            min_value=10_000,
            max_value=5_000_000,
        )

        nbins = self._as_int(
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
            response = self.backend.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": str(scattering_channel),
                    "nbins": int(nbins),
                    "number_of_points": int(max_events),
                }
            )
            thr = self._as_float(response.get("threshold")) or 0.0
            return float(thr), f"{float(thr):.6g}"

        if manual_thr is not None:
            return float(manual_thr), dash.no_update

        if store_thr is not None:
            return float(store_thr), dash.no_update

        return 0.0, dash.no_update

    def _build_scattering_histogram(
        self,
        *,
        runtime_config: Any,
        scattering_channel: Any,
        nbins: int,
        max_events: int,
        yscale_selection: Any,
        thr: float,
    ) -> go.Figure:
        """
        Build the scattering histogram figure with a vertical threshold line.

        Parameters
        ----------
        runtime_config : Any
            Runtime configuration object.
        scattering_channel : Any
            Selected scattering channel.
        nbins : int
            Histogram bin count.
        max_events : int
            Number of events to plot.
        yscale_selection : Any
            Checklist value indicating log y scale selection.
        thr : float
            Threshold line position.

        Returns
        -------
        go.Figure
            Plotly figure for the scattering histogram.
        """
        if not runtime_config.fluorescence_show_scattering_controls:
            fig = go.Figure()
            fig.update_layout(separators=".,")
            return fig

        use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)

        with FCSFile(self.backend.file_path, writable=False) as fcs:
            values = fcs.column_copy(str(scattering_channel), dtype=float, n=max_events)

        fig = make_histogram_with_lines(
            values=values,
            nbins=nbins,
            xaxis_title="Scattering (a.u.)",
            line_positions=[float(thr)],
            line_labels=[f"{float(thr):.3g}"],
        )
        fig.update_yaxes(type="log" if use_log else "linear")
        return fig

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        """
        Parse a value into a finite float.

        Parameters
        ----------
        value : Any
            Candidate value from UI components.

        Returns
        -------
        Optional[float]
            Parsed float if valid and finite, otherwise None.
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            v = float(value)
            return v if np.isfinite(v) else None

        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            s = s.replace(",", ".")
            try:
                v = float(s)
            except ValueError:
                return None
            return v if np.isfinite(v) else None

        return None

    @staticmethod
    def _as_int(value: Any, default: int, min_value: int, max_value: int) -> int:
        """
        Parse a value into an int, falling back to a default and clamping within bounds.

        Parameters
        ----------
        value : Any
            Candidate numeric input.
        default : int
            Default value used when parsing fails.
        min_value : int
            Minimum allowed value.
        max_value : int
            Maximum allowed value.

        Returns
        -------
        int
            Parsed and clamped integer.
        """
        try:
            v = int(value)
        except Exception:
            v = default

        if v < min_value:
            v = min_value
        if v > max_value:
            v = max_value

        return v