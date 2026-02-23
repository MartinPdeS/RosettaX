from __future__ import annotations

from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback, callback_context, dcc, html

from RosettaX.backend import BackEnd
from RosettaX.pages import styling
from RosettaX.pages.fluorescence import BaseSection, SectionContext
from RosettaX.pages.runtime_config import get_ui_flags

class ScatteringSection(BaseSection):
    """
    Scattering section for the fluorescence calibration workflow.

    Key goals
    ----------
    1. Always compute and store a scattering threshold once a file and detector are available.
    2. Show or hide UI controls based on RuntimeConfig toggles.
    3. If scattering plot controls are visible, return a real histogram figure.
       Otherwise, keep the graph component alive but visually hidden.
    """

    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)
        self.default_scattering_nbins = 400
        self.debug_text_id = f"{self.context.ids.page_name}-scattering-debug-out"

    def layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("2. Scattering channel"),
                dbc.CardBody(self._build_body_children()),
            ]
        )

    def _build_body_children(self) -> list:
        ui_flags = get_ui_flags()

        show_scattering_controls = ui_flags.fluorescence_show_scattering_controls
        show_threshold_controls = ui_flags.fluorescence_show_threshold_controls
        debug_mode = ui_flags.debug
        children: list = [html.Br(), self._detector_row()]

        # Scattering controls (bins, button, scale, histogram) are opt in via config
        if show_scattering_controls:
            children.extend(
                [
                    html.Br(),
                    self._nbins_row(hidden=not debug_mode),
                    html.Br(),
                    self._estimate_button(hidden=not debug_mode),
                    html.Br(),
                    self._yscale_switch(hidden=not debug_mode),
                    self._histogram_graph(hidden=not debug_mode),
                ]
            )
        else:
            # Keep graph component alive for callback output, but never show it.
            children.extend([self._histogram_graph(hidden=True)])

        # Threshold controls are separately toggled
        if show_threshold_controls:
            children.extend([html.Br(), html.Br(), self._threshold_row(hidden=not debug_mode)])
        else:
            # Keep input alive for callback output, but never show it.
            children.extend([self._threshold_row(hidden=True)])

        # Debug output
        children.append(self._debug_container(hidden=not debug_mode))

        return children

    def _detector_row(self) -> html.Div:
        return html.Div(
            [
                html.Div("Scattering detector:"),
                dcc.Dropdown(
                    id=self.context.ids.scattering_detector_dropdown,
                    style={"width": "500px"},
                ),
            ],
            style=styling.CARD,
        )

    def _nbins_row(self, *, hidden: bool) -> html.Div:
        return html.Div(
            [
                html.Div("number of bins:"),
                dcc.Input(
                    id=self.context.ids.scattering_nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=self.default_scattering_nbins,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
            hidden=hidden,
        )

    def _estimate_button(self, *, hidden: bool) -> html.Button:
        return html.Button(
            "Estimate threshold",
            id=self.context.ids.scattering_find_threshold_btn,
            n_clicks=0,
            style={"display": "none"} if hidden else {"display": "inline-block"},
        )

    def _threshold_row(self, *, hidden: bool) -> html.Div:
        return html.Div(
            [
                html.Div("Threshold:"),
                dcc.Input(
                    id=self.context.ids.scattering_threshold_input,
                    type="text",
                    value="",
                    style={"width": "220px"},
                ),
            ],
            style=styling.CARD,
            hidden=hidden,
        )

    def _yscale_switch(self, *, hidden: bool) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.context.ids.scattering_yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "none"} if hidden else {"display": "block"},
        )

    def _histogram_graph(self, *, hidden: bool) -> dcc.Loading:
        return dcc.Loading(
            dcc.Graph(
                id=self.context.ids.graph_scattering_hist,
                style={"display": "none"} if hidden else self.context.graph_style,
            ),
            type="default",
        )

    def _debug_container(self, *, hidden: bool) -> html.Div:
        return html.Div(
            [
                html.Hr(),
                dbc.Alert("Debug outputs (ScatteringSection)", color="secondary", is_open=True),
                html.Pre(id=self.debug_text_id, style={"whiteSpace": "pre-wrap"}),
            ],
            style={"display": "none"} if hidden else {"display": "block"},
        )

    def register_callbacks(self) -> None:
        ids = self.context.ids
        service = self.context.service

        @callback(
            Output(ids.graph_scattering_hist, "figure"),
            Output(ids.scattering_threshold_store, "data"),
            Output(ids.scattering_threshold_input, "value"),
            Output(self.debug_text_id, "children"),
            Input(ids.scattering_find_threshold_btn, "n_clicks"),
            Input(ids.uploaded_fcs_path_store, "data"),
            Input(ids.scattering_detector_dropdown, "value"),
            Input(ids.scattering_nbins_input, "value"),
            Input(ids.scattering_threshold_input, "value"),
            Input(ids.scattering_yscale_switch, "value"),
            State(ids.max_events_for_plots_input, "value", allow_optional=True),
            State(ids.scattering_threshold_store, "data"),
            prevent_initial_call=True,
        )
        def scattering_section(
            n_clicks_estimate: int,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            scattering_nbins: Any,
            threshold_input_value: Any,
            yscale_selection: Optional[list[str]],
            max_events_for_plots: Any,
            stored_threshold_payload: Optional[dict],
        ):
            ui_flags = get_ui_flags()

            show_scattering_controls = ui_flags.fluorescence_show_scattering_controls
            show_threshold_controls = ui_flags.fluorescence_show_threshold_controls
            debug_mode = ui_flags.debug

            if not fcs_path or not scattering_channel:
                return self._empty_fig(), dash.no_update, dash.no_update, ""

            backend = BackEnd(fcs_path)

            max_events = self._as_int(
                max_events_for_plots if max_events_for_plots is not None else 200_000,
                default=200_000,
                min_value=10_000,
                max_value=5_000_000,
            )

            # One default for nbins. Only user editable in debug mode.
            nbins = self.default_scattering_nbins
            if debug_mode:
                nbins = self._as_int(
                    scattering_nbins,
                    default=self.default_scattering_nbins,
                    min_value=10,
                    max_value=5000,
                )

            triggered = (
                callback_context.triggered[0]["prop_id"].split(".")[0]
                if callback_context.triggered
                else ""
            )

            # Load values only if we might plot or need debug info.
            values = None
            if show_scattering_controls or debug_mode:
                values = service.get_column_values(
                    backend=backend,
                    column=str(scattering_channel),
                    max_points=max_events,
                )

            stored_thr = self._as_float((stored_threshold_payload or {}).get("threshold"))
            typed_thr = self._as_float(threshold_input_value)

            # Threshold behavior:
            # - If threshold controls are off, always estimate.
            # - If debug is off, always estimate (user cannot type/trigger).
            # - If debug is on, estimate on button click or if nothing exists yet.
            must_estimate = (
                (not show_threshold_controls)
                or (not debug_mode)
                or (triggered == ids.scattering_find_threshold_btn)
                or (stored_thr is None and typed_thr is None)
            )

            if must_estimate:
                response = backend.process_scattering(
                    {
                        "operation": "estimate_scattering_threshold",
                        "column": str(scattering_channel),
                        "nbins": int(nbins),
                        "number_of_points": int(max_events),
                    }
                )
                thr = self._as_float(response.get("threshold"))
                if thr is None:
                    thr = 0.0
            else:
                thr = typed_thr if typed_thr is not None else float(stored_thr)

            next_store = {
                "scattering_channel": str(scattering_channel),
                "threshold": float(thr),
                "nbins": int(nbins),
            }

            # Figure:
            # - If scattering controls are off, keep empty.
            # - If debug is on and controls are on, show histogram.
            # - If debug is off but controls are on, you can still compute histogram if you later decide to show it.
            #   Right now: only show the plot in debug mode.
            if show_scattering_controls and debug_mode:
                use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)

                fig = service.make_histogram_with_lines(
                    values=values,
                    nbins=nbins,
                    xaxis_title="Scattering (a.u.)",
                    line_positions=[float(thr)] if show_threshold_controls else [],
                    line_labels=[f"{float(thr):.3g}"] if show_threshold_controls else [],
                )
                fig.update_yaxes(type="log" if use_log else "linear")
            else:
                fig = self._empty_fig()
                use_log = False

            debug_text = ""
            if debug_mode:
                values_size = int(values.size) if values is not None else 0
                debug_text = (
                    f"triggered: {triggered}\n"
                    f"fcs_path: {fcs_path}\n"
                    f"scattering_channel: {scattering_channel}\n"
                    f"nbins: {nbins}\n"
                    f"max_events: {max_events}\n"
                    f"threshold: {float(thr):.6g}\n"
                    f"use_log: {use_log}\n"
                    f"values.size: {values_size}\n"
                    f"show_scattering_controls: {show_scattering_controls}\n"
                    f"show_threshold_controls: {show_threshold_controls}\n"
                )

            # If threshold controls are hidden, still keep the input updated but the user will not see it.
            return fig, next_store, f"{float(thr):.6g}", debug_text