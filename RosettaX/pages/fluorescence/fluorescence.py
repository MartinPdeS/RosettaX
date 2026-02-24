from typing import Any, List, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages import styling
from RosettaX.pages.fluorescence import BaseSection, SectionContext
from RosettaX.pages.runtime_config import get_ui_flags


class FluorescenceSection(BaseSection):
    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)
        self.debug_graph_id = f"{self.context.ids.page_name}-fluorescence-debug-graph"
        self.debug_text_id = f"{self.context.ids.page_name}-fluorescence-debug-out"

        self.default_fluorescence_nbins = 400
        self.default_peak_count = 3

    def layout(self) -> dbc.Card:
        ids = self.context.ids
        ui_flags = get_ui_flags()

        debug_container_style = {"display": "block"} if ui_flags.debug else {"display": "none"}
        must_show_fluorescence_histogram = bool(ui_flags.fluorescence_show_fluorescence_controls)

        return dbc.Card(
            [
                dbc.CardHeader("3. Fluorescence channel after thresholding"),
                dbc.CardBody(
                    [
                        html.Br(),
                        html.Div(
                            [
                                html.Div("Fluorescence detector:"),
                                dcc.Dropdown(
                                    id=ids.fluorescence_detector_dropdown,
                                    style={"width": "500px"},
                                ),
                            ],
                            style=styling.CARD,
                        ),
                        html.Br(),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div("Number of peaks to look for:", style={"marginRight": "8px"}),
                                        dcc.Input(
                                            id=ids.fluorescence_peak_count_input,
                                            type="number",
                                            min=1,
                                            step=1,
                                            value=self.default_peak_count,
                                            style={"width": "120px"},
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Button(
                                    "Find peaks",
                                    id=ids.fluorescence_find_peaks_btn,
                                    n_clicks=0,
                                    style={"marginLeft": "16px"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center"},
                        ),
                        html.Br(),
                        html.Br(),
                        dcc.Loading(
                            dcc.Graph(
                                id=ids.graph_fluorescence_hist,
                                style={"display": "none"} if (not must_show_fluorescence_histogram) else self.context.graph_style,
                            ),
                            type="default",
                        ),
                        html.Br(),
                        dbc.Checklist(
                            id=ids.fluorescence_yscale_switch,
                            options=[{"label": "Log scale (counts)", "value": "log"}],
                            value=["log"],
                            switch=True,
                            style={"display": "none"} if (not must_show_fluorescence_histogram) else {"display": "block"},
                        ),
                        html.Br(),
                        html.Div(
                            [
                                html.Div("number of bins:"),
                                dcc.Input(
                                    id=ids.fluorescence_nbins_input,
                                    type="number",
                                    min=10,
                                    step=10,
                                    value=self.default_fluorescence_nbins,
                                    style={"width": "160px"},
                                ),
                            ],
                            style=styling.CARD,
                            hidden=not must_show_fluorescence_histogram,
                        ),
                        html.Div(
                            [
                                html.Hr(),
                                dbc.Alert("Debug outputs (FluorescenceSection)", color="secondary", is_open=True),
                                dcc.Loading(
                                    dcc.Graph(id=self.debug_graph_id, style=self.context.graph_style),
                                    type="default",
                                ),
                                html.Pre(id=self.debug_text_id, style={"whiteSpace": "pre-wrap"}),
                            ],
                            style=debug_container_style,
                        ),
                    ]
                ),
            ]
        )

    @staticmethod
    def _inject_peak_modes_into_table(table_data: Optional[list[dict]], peak_positions: List[float]) -> list[dict]:
        rows = [dict(r) for r in (table_data or [])]

        modes: List[float] = []
        for p in peak_positions or []:
            try:
                v = float(p)
            except Exception:
                continue
            if np.isfinite(v):
                modes.append(v)

        if not modes:
            return rows

        while len(rows) < len(modes):
            rows.append({"col1": "", "col2": ""})

        for i, v in enumerate(modes):
            current = rows[i].get("col2", "")
            if current is None:
                current = ""
            if str(current).strip() == "":
                rows[i]["col2"] = f"{v:.6g}"

        return rows

    def register_callbacks(self) -> None:
        ids = self.context.ids
        service = self.context.service

        def resolve_threshold_value(
            *,
            fcs_path: str,
            scattering_channel: str,
            threshold_payload: Optional[dict],
            threshold_input_value: Any,
            max_events: int,
        ) -> float:
            threshold_value: Optional[float] = None

            if isinstance(threshold_payload, dict):
                threshold_value = self._as_float(threshold_payload.get("threshold"))

            if threshold_value is None:
                threshold_value = self._as_float(threshold_input_value)

            if threshold_value is None:
                backend = BackEnd(fcs_path)
                response = backend.process_scattering(
                    {
                        "operation": "estimate_scattering_threshold",
                        "column": str(scattering_channel),
                        "nbins": int(self.default_fluorescence_nbins),
                        "number_of_points": int(max_events),
                    }
                )
                threshold_value = self._as_float(response.get("threshold"))

            if threshold_value is None:
                threshold_value = 0.0

            return float(threshold_value)

        @callback(
            Output(ids.fluorescence_source_channel_store, "data", allow_duplicate=True),
            Input(ids.fluorescence_detector_dropdown, "value"),
            State(ids.fluorescence_source_channel_store, "data"),
            prevent_initial_call=True,
        )
        def lock_fluorescence_source_channel(
            fluorescence_channel: Optional[str],
            current_locked: Optional[str],
        ) -> Optional[str]:
            if not fluorescence_channel:
                return dash.no_update

            chosen = str(fluorescence_channel).strip()
            if not chosen:
                return dash.no_update

            # If already locked, keep it (do not auto-switch to MESF or other injected columns)
            if isinstance(current_locked, str) and current_locked.strip():
                return dash.no_update

            return chosen

        @callback(
            Output(ids.fluorescence_hist_store, "data", allow_duplicate=True),
            Input(ids.uploaded_fcs_path_store, "data"),
            Input(ids.scattering_detector_dropdown, "value"),
            Input(ids.fluorescence_detector_dropdown, "value"),
            Input(ids.fluorescence_nbins_input, "value"),
            Input(ids.scattering_threshold_store, "data"),
            Input(ids.scattering_threshold_input, "value"),
            State(ids.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=True,
        )
        def refresh_fluorescence_hist_store(
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            fluorescence_channel: Optional[str],
            fluorescence_nbins: Any,
            threshold_payload: Optional[dict],
            threshold_input_value: Any,
            max_events_for_plots: Any,
        ):
            ui_flags = get_ui_flags()
            must_show_fluorescence_histogram = bool(ui_flags.fluorescence_show_fluorescence_controls)

            if not must_show_fluorescence_histogram:
                return dash.no_update

            if not fcs_path or not scattering_channel or not fluorescence_channel:
                return dash.no_update

            if max_events_for_plots is None:
                max_events_for_plots = 200_000

            max_events = self._as_int(
                max_events_for_plots,
                default=200_000,
                min_value=10_000,
                max_value=5_000_000,
            )

            threshold_value = resolve_threshold_value(
                fcs_path=str(fcs_path),
                scattering_channel=str(scattering_channel),
                threshold_payload=threshold_payload,
                threshold_input_value=threshold_input_value,
                max_events=int(max_events),
            )

            nbins = self._as_int(
                fluorescence_nbins,
                default=self.default_fluorescence_nbins,
                min_value=10,
                max_value=5000,
            )

            backend = BackEnd(str(fcs_path))

            fluorescence_values = service.get_column_values(
                backend=backend,
                column=str(fluorescence_channel),
                max_points=max_events,
            )

            scattering_values = service.get_column_values(
                backend=backend,
                column=str(scattering_channel),
                max_points=max_events,
            )

            gated = service.apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            fig = service.make_histogram_with_lines(
                values=fluorescence_values,
                overlay_values=gated,
                nbins=nbins,
                xaxis_title="Fluorescence (a.u.)",
                line_positions=[],
                line_labels=[],
                base_name="all events",
                overlay_name="gated events",
            )

            return fig.to_dict()

        @callback(
            Output(ids.graph_fluorescence_hist, "figure"),
            Input(ids.fluorescence_yscale_switch, "value"),
            Input(ids.fluorescence_hist_store, "data"),
        )
        def update_fluorescence_yscale(
            yscale_selection: Optional[list[str]],
            stored_figure: Optional[dict],
        ):
            ui_flags = get_ui_flags()
            must_show_fluorescence_histogram = bool(ui_flags.fluorescence_show_fluorescence_controls)

            if not must_show_fluorescence_histogram:
                return self._empty_fig()

            if not stored_figure:
                fig = go.Figure()
                fig.update_layout(title="Select file + channels first.", separators=".,")
                return fig

            fig = go.Figure(stored_figure)
            use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)
            fig.update_yaxes(type="log" if use_log else "linear")
            return fig

        @callback(
            Output(ids.bead_table, "data", allow_duplicate=True),
            Output(ids.fluorescence_hist_store, "data", allow_duplicate=True),
            Output(self.debug_graph_id, "figure"),
            Output(self.debug_text_id, "children"),
            Input(ids.fluorescence_find_peaks_btn, "n_clicks"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.scattering_detector_dropdown, "value"),
            State(ids.fluorescence_detector_dropdown, "value"),
            State(ids.fluorescence_nbins_input, "value"),
            State(ids.fluorescence_peak_count_input, "value"),
            State(ids.max_events_for_plots_input, "value", allow_optional=True),
            State(ids.scattering_threshold_store, "data"),
            State(ids.scattering_threshold_input, "value"),
            State(ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def fluorescence_section(
            n_clicks: int,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            fluorescence_channel: Optional[str],
            fluorescence_nbins: Any,
            peak_count: Any,
            max_events_for_plots: Any,
            threshold_payload: Optional[dict],
            threshold_input_value: Any,
            table_data: Optional[list[dict]],
        ):
            ui_flags = get_ui_flags()
            must_show_fluorescence_histogram = bool(ui_flags.fluorescence_show_fluorescence_controls)

            if not must_show_fluorescence_histogram:
                return dash.no_update, dash.no_update, self._empty_fig(), ""

            if not fcs_path or not scattering_channel or not fluorescence_channel:
                return dash.no_update, dash.no_update, self._empty_fig(), ""

            if max_events_for_plots is None:
                max_events_for_plots = 200_000

            max_events = self._as_int(
                max_events_for_plots,
                default=200_000,
                min_value=10_000,
                max_value=5_000_000,
            )

            threshold_value = resolve_threshold_value(
                fcs_path=str(fcs_path),
                scattering_channel=str(scattering_channel),
                threshold_payload=threshold_payload,
                threshold_input_value=threshold_input_value,
                max_events=int(max_events),
            )

            nbins = self._as_int(
                fluorescence_nbins,
                default=self.default_fluorescence_nbins,
                min_value=10,
                max_value=5000,
            )

            max_peaks = self._as_int(
                peak_count,
                default=self.default_peak_count,
                min_value=1,
                max_value=100,
            )

            backend = BackEnd(str(fcs_path))

            peaks_payload = backend.find_fluorescence_peaks(
                {
                    "column": str(fluorescence_channel),
                    "max_peaks": int(max_peaks),
                    "gating_column": str(scattering_channel),
                    "gating_threshold": float(threshold_value),
                    "number_of_points": int(max_events),
                }
            )
            peak_positions = peaks_payload.get("peak_positions", [])

            fluorescence_values = service.get_column_values(
                backend=backend,
                column=str(fluorescence_channel),
                max_points=max_events,
            )

            scattering_values = service.get_column_values(
                backend=backend,
                column=str(scattering_channel),
                max_points=max_events,
            )

            gated = service.apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            fig = service.make_histogram_with_lines(
                values=fluorescence_values,
                overlay_values=gated,
                nbins=nbins,
                xaxis_title="Fluorescence (a.u.)",
                line_positions=[float(p) for p in peak_positions if self._as_float(p) is not None],
                line_labels=[f"{float(p):.3g}" for p in peak_positions if self._as_float(p) is not None],
                base_name="all events",
                overlay_name="gated events",
            )

            updated_table = self._inject_peak_modes_into_table(
                table_data=table_data,
                peak_positions=peak_positions,
            )

            debug_fig = self._empty_fig()
            debug_text = ""

            if ui_flags.debug:
                debug_fig = go.Figure()
                preview_count = int(min(fluorescence_values.size, 25_000))

                debug_fig.add_trace(
                    go.Scatter(
                        x=scattering_values[:preview_count],
                        y=fluorescence_values[:preview_count],
                        mode="markers",
                        name="all events",
                    )
                )

                gated_mask = scattering_values[:preview_count] > float(threshold_value)
                debug_fig.add_trace(
                    go.Scatter(
                        x=scattering_values[:preview_count][gated_mask],
                        y=fluorescence_values[:preview_count][gated_mask],
                        mode="markers",
                        name="gated events",
                    )
                )

                debug_fig.update_layout(
                    title="Fluorescence vs scattering preview",
                    xaxis_title="Scattering (a.u.)",
                    yaxis_title="Fluorescence (a.u.)",
                    separators=".,",
                )

                gated_fraction = float(np.mean(scattering_values > float(threshold_value))) if scattering_values.size else 0.0
                debug_text = (
                    f"fcs_path: {fcs_path}\n"
                    f"scattering_channel: {scattering_channel}\n"
                    f"fluorescence_channel: {fluorescence_channel}\n"
                    f"threshold_value: {float(threshold_value):.6g}\n"
                    f"nbins: {nbins}\n"
                    f"max_peaks: {max_peaks}\n"
                    f"max_events: {max_events}\n"
                    f"fluorescence_values.size: {fluorescence_values.size}\n"
                    f"scattering_values.size: {scattering_values.size}\n"
                    f"gated.size: {gated.size}\n"
                    f"gated_fraction: {gated_fraction:.6g}\n"
                    f"peak_positions: {peak_positions}\n"
                )

            return updated_table, fig.to_dict(), debug_fig, debug_text