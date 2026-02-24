from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
import plotly.graph_objs as go

from RosettaX.pages import styling
from RosettaX.pages.runtime_config import get_ui_flags
from RosettaX.reader import FCSFile


class ScatteringSection():

    def _scattering_get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("2. Scattering channel"),
                dbc.CardBody(self._scattering_build_body_children()),
            ]
        )

    def _scattering_build_body_children(self) -> list:
        ui_flags = get_ui_flags()

        children = [
            html.Br(),
            self._scattering_detector_row(),
            html.Br(),
            self._scattering_estimate_and_threshold_row(hidden=not ui_flags.fluorescence_show_scattering_controls),
            html.Br(),
            self._scattering_histogram_graph(hidden=not ui_flags.fluorescence_show_scattering_controls),
            html.Br(),
            self._scattering_yscale_switch(hidden=not ui_flags.fluorescence_show_scattering_controls),
            html.Br(),
            self._scattering_nbins_row(hidden=not ui_flags.fluorescence_show_scattering_controls),
        ]

        return children

    def _scattering_detector_row(self) -> html.Div:
        return html.Div(
            [
                html.Div("Scattering detector:"),
                dcc.Dropdown(
                    id=self.ids.scattering_detector_dropdown,
                    style={"width": "500px"},
                ),
            ],
            style=styling.CARD,
        )

    def _scattering_nbins_row(self, *, hidden: bool) -> html.Div:
        ui_flags = get_ui_flags()
        return html.Div(
            [
                html.Div("number of bins:"),
                dcc.Input(
                    id=self.ids.scattering_nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=ui_flags.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
            hidden=hidden,
        )

    def _scattering_estimate_button(self) -> html.Button:
        return html.Button(
            "Estimate threshold",
            id=self.ids.scattering_find_threshold_btn,
            n_clicks=0,
            style={"display": "inline-block"},
        )

    def _scattering_threshold_input(self) -> dcc.Input:
        return dcc.Input(
            id=self.ids.scattering_threshold_input,
            type="text",
            value="",
            disabled=False,
            style={"width": "220px"},
        )

    def _scattering_estimate_and_threshold_row(self, *, hidden: bool) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [self._scattering_estimate_button()],
                    style={"display": "flex", "alignItems": "center"},
                ),
                html.Div(
                    [
                        html.Div("Threshold:", style={"marginRight": "8px"}),
                        self._scattering_threshold_input(),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginLeft": "16px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center"},
            hidden=hidden,
        )

    def _scattering_yscale_switch(self, *, hidden: bool) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.ids.scattering_yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "none"} if hidden else {"display": "block"},
        )

    def _scattering_histogram_graph(self, *, hidden: bool) -> dcc.Loading:
        return dcc.Loading(
            dcc.Graph(
                id=self.ids.graph_scattering_hist,
                style={"display": "none"} if hidden else self.graph_style,
            ),
            type="default",
        )

    def _scattering_register_callbacks(self) -> None:
        @callback(
            Output(self.ids.graph_scattering_hist, "figure"),
            Output(self.ids.scattering_threshold_store, "data"),
            Output(self.ids.scattering_threshold_input, "value"),
            Input(self.ids.scattering_find_threshold_btn, "n_clicks"),
            Input(self.ids.scattering_detector_dropdown, "value"),
            Input(self.ids.scattering_nbins_input, "value"),
            Input(self.ids.scattering_yscale_switch, "value"),
            State(self.ids.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=True,
        )
        def scattering_section(
            n_clicks_estimate,
            scattering_channel,
            scattering_nbins,
            yscale_selection,
            max_events_for_plots,
        ):
            ui_flags = get_ui_flags()

            max_events = self._as_int(
                max_events_for_plots if max_events_for_plots is not None else ui_flags.max_events_for_analysis,
                default=ui_flags.max_events_for_analysis,
                min_value=10_000,
                max_value=5_000_000,
            )

            nbins = self._as_int(
                scattering_nbins,
                default=ui_flags.n_bins_for_plots,
                min_value=10,
                max_value=5000,
            )

            column_names = None
            if ui_flags.fluorescence_show_scattering_controls:
                column_names = self.context.backend.get_column_names()

            response = self.context.backend.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": str(scattering_channel),
                    "nbins": int(nbins),
                    "number_of_points": int(max_events),
                }
            )
            thr = self._as_float(response.get("threshold")) or 0.0

            next_store = {
                "scattering_channel": str(scattering_channel),
                "threshold": float(thr),
                "nbins": int(nbins),
            }

            if ui_flags.fluorescence_show_scattering_controls and column_names is not None:
                use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)

                with FCSFile(self.context.backend.file_path, writable=False) as fcs:
                    values = fcs.column_copy(scattering_channel, dtype=float, n=max_events_for_plots)

                fig = self.service.make_histogram_with_lines(
                    values=values,
                    nbins=nbins,
                    xaxis_title="Scattering (a.u.)",
                    line_positions=[float(thr)] if ui_flags.fluorescence_show_scattering_controls else [],
                    line_labels=[f"{float(thr):.3g}"] if ui_flags.fluorescence_show_scattering_controls else [],
                )
                fig.update_yaxes(type="log" if use_log else "linear")
            else:
                fig = self._empty_fig()

            return fig, next_store, f"{float(thr):.6g}"

        @staticmethod
        def _empty_fig() -> go.Figure:
            fig = go.Figure()
            fig.update_layout(separators=".,")
            return fig


        @staticmethod
        def _as_float(value: Any) -> Optional[float]:
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
            try:
                v = int(value)
            except Exception:
                v = default

            if v < min_value:
                v = min_value
            if v > max_value:
                v = max_value

            return v
