from typing import Any, List, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages import styling
from RosettaX.pages.runtime_config import get_runtime_config
from RosettaX.reader import FCSFile


class PeaksSection():
    def _fluorescence_get_layout(self) -> dbc.Card:
        runtime_config = get_runtime_config()
        must_show_fluorescence_histogram = bool(runtime_config.fluorescence_show_fluorescence_controls)

        return dbc.Card(
            [
                self._fluorescence_build_header(),
                self._fluorescence_build_body(
                    must_show_fluorescence_histogram=must_show_fluorescence_histogram,
                    default_peak_count=runtime_config.default_peak_count,
                    default_n_bins_for_plots=runtime_config.n_bins_for_plots,
                ),
            ]
        )

    def _fluorescence_build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("3. Fluorescence channel after thresholding")

    def _fluorescence_build_body(
        self,
        *,
        must_show_fluorescence_histogram: bool,
        default_peak_count: int,
        default_n_bins_for_plots: int,
    ) -> dbc.CardBody:
        return dbc.CardBody(
            [
                html.Br(),
                self._fluorescence_build_detector_dropdown(),
                html.Br(),
                self._fluorescence_build_peak_controls(default_peak_count=default_peak_count),
                html.Br(),
                html.Br(),
                self._fluorescence_build_histogram_graph(),
                html.Br(),
                self._fluorescence_build_yscale_switch(),
                html.Br(),
                self._fluorescence_build_nbins_input(
                    default_n_bins_for_plots=default_n_bins_for_plots,
                    must_show_fluorescence_histogram=must_show_fluorescence_histogram,
                ),
            ]
        )


    def _fluorescence_build_detector_dropdown(self) -> html.Div:
        return html.Div(
            [
                html.Div("Fluorescence detector:"),
                dcc.Dropdown(
                    id=self.ids.fluorescence_detector_dropdown,
                    style={"width": "500px"},
                ),
            ],
            style=styling.CARD,
        )


    def _fluorescence_build_peak_controls(self, *, default_peak_count: int) -> html.Div:
        peak_count_input = dcc.Input(
            id=self.ids.fluorescence_peak_count_input,
            type="number",
            min=1,
            step=1,
            value=default_peak_count,
            style={"width": "120px"},
        )

        peak_count_row = html.Div(
            [
                html.Div("Number of peaks to look for:", style={"marginRight": "8px"}),
                peak_count_input,
            ],
            style={"display": "flex", "alignItems": "center"},
        )

        find_peaks_button = html.Button(
            "Find peaks",
            id=self.ids.fluorescence_find_peaks_btn,
            n_clicks=0,
            style={"marginLeft": "16px"},
        )

        return html.Div(
            [peak_count_row, find_peaks_button],
            style={"display": "flex", "alignItems": "center"},
        )


    def _fluorescence_build_histogram_graph(self) -> dcc.Loading:
        return dcc.Loading(
            dcc.Graph(
                id=self.ids.graph_fluorescence_hist,
                style=self.graph_style,
            ),
            type="default",
        )


    def _fluorescence_build_yscale_switch(self) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.ids.fluorescence_yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "block"},
        )


    def _fluorescence_build_nbins_input(
        self,
        *,
        default_n_bins_for_plots: int,
        must_show_fluorescence_histogram: bool,
    ) -> html.Div:
        return html.Div(
            [
                html.Div("number of bins:"),
                dcc.Input(
                    id=self.ids.fluorescence_nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=default_n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
            hidden=not must_show_fluorescence_histogram,
        )

    @staticmethod
    def _fluorescence_inject_peak_modes_into_table(table_data: Optional[list[dict]], peak_positions: List[float]) -> list[dict]:
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

    def _fluorescence_register_callbacks(self) -> None:
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
            Output(self.ids.fluorescence_source_channel_store, "data", allow_duplicate=True),
            Input(self.ids.fluorescence_detector_dropdown, "value"),
            State(self.ids.fluorescence_source_channel_store, "data"),
            prevent_initial_call=True,
        )
        def lock_fluorescence_source_channel(fluorescence_channel: Optional[str], current_locked: Optional[str]) -> Optional[str]:
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
            Output(self.ids.fluorescence_hist_store, "data", allow_duplicate=True),
            Input(self.ids.uploaded_fcs_path_store, "data"),
            Input(self.ids.scattering_detector_dropdown, "value"),
            Input(self.ids.fluorescence_detector_dropdown, "value"),
            Input(self.ids.fluorescence_nbins_input, "value"),
            Input(self.ids.scattering_threshold_store, "data"),
            Input(self.ids.scattering_threshold_input, "value"),
            State(self.ids.max_events_for_plots_input, "value", allow_optional=True),
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
            runtime_config = get_runtime_config()
            if not bool(runtime_config.fluorescence_show_fluorescence_controls):
                return dash.no_update

            # Normalize + early exit
            fcs_path_clean = str(fcs_path or "").strip()
            scattering_clean = str(scattering_channel or "").strip()
            fluorescence_clean = str(fluorescence_channel or "").strip()

            if not fcs_path_clean or not scattering_clean or not fluorescence_clean:
                return dash.no_update

            max_events_for_plots = self._as_int(
                max_events_for_plots,
                default=runtime_config.max_events_for_analysis,
                min_value=10_000,
                max_value=5_000_000,
            )

            threshold_value = resolve_threshold_value(
                fcs_path=fcs_path_clean,
                scattering_channel=scattering_clean,
                threshold_payload=threshold_payload,
                threshold_input_value=threshold_input_value,
                max_events=max_events_for_plots,
            )

            nbins = self._as_int(
                fluorescence_nbins,
                default=runtime_config.n_bins_for_plots,
                min_value=10,
                max_value=5000,
            )

            # IMPORTANT: open the file from the store path, not from self.backend
            with FCSFile(fcs_path_clean, writable=False) as fcs:
                cols = [str(c).strip() for c in fcs.get_column_names()]
                # Guard against transient mismatch (e.g., dropdown changed before file path, etc.)
                if fluorescence_clean not in cols or scattering_clean not in cols:
                    return dash.no_update

                try:
                    fluorescence_values = fcs.column_copy(
                        fluorescence_clean,
                        dtype=float,
                        n=max_events_for_plots,
                    )
                    scattering_values = fcs.column_copy(
                        scattering_clean,
                        dtype=float,
                        n=max_events_for_plots,
                    )
                except KeyError:
                    # Extra safety in case names mismatch due to whitespace/casing/race
                    return dash.no_update

            gated = self.service.apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            fig = self.service.make_histogram_with_lines(
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
            Output(self.ids.graph_fluorescence_hist, "figure"),
            Input(self.ids.fluorescence_yscale_switch, "value"),
            Input(self.ids.fluorescence_hist_store, "data"),
            Input(self.ids.fluorescence_peak_lines_store, "data"),
        )
        def update_fluorescence_yscale(yscale_selection, stored_figure, peak_lines):
            runtime_config = get_runtime_config()
            must_show_fluorescence_histogram = bool(runtime_config.fluorescence_show_fluorescence_controls)

            if not must_show_fluorescence_histogram:
                return self._empty_fig()

            if not stored_figure:
                fig = go.Figure()
                fig.update_layout(title="Select file + channels first.", separators=".,")
                return fig

            fig = go.Figure(stored_figure)

            positions = []
            labels = []
            if isinstance(peak_lines, dict):
                positions = peak_lines.get("positions") or []
                labels = peak_lines.get("labels") or []

            # you need a helper that adds vertical lines to an existing plotly fig
            fig = self.service.add_vertical_lines(
                fig=fig,
                line_positions=positions,
                line_labels=labels,
            )

            use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)
            fig.update_yaxes(type="log" if use_log else "linear")
            return fig


        @callback(
            Output(self.ids.bead_table, "data", allow_duplicate=True),
            Output(self.ids.fluorescence_peak_lines_store, "data", allow_duplicate=True),
            Input(self.ids.fluorescence_find_peaks_btn, "n_clicks"),
            State(self.ids.uploaded_fcs_path_store, "data"),
            State(self.ids.scattering_detector_dropdown, "value"),
            State(self.ids.fluorescence_detector_dropdown, "value"),
            State(self.ids.fluorescence_nbins_input, "value"),
            State(self.ids.fluorescence_peak_count_input, "value"),
            State(self.ids.max_events_for_plots_input, "value", allow_optional=True),
            State(self.ids.scattering_threshold_store, "data"),
            State(self.ids.scattering_threshold_input, "value"),
            State(self.ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def _debug_click(
            n_clicks,
            fcs_path,
            scattering_channel,
            fluorescence_channel,
            fluorescence_nbins,
            fluorescence_peak_count,
            max_events_for_plots,
            scattering_threshold_payload,
            scattering_threshold_input_value,
            table_data,
        ):
            runtime_config = get_runtime_config()

            if not runtime_config.fluorescence_show_fluorescence_controls:
                return dash.no_update

            if not fcs_path or not scattering_channel or not fluorescence_channel:
                return dash.no_update

            max_events = self._as_int(
                max_events_for_plots,
                default=runtime_config.max_events_for_analysis,
                min_value=10_000,
                max_value=5_000_000,
            )

            threshold_value = resolve_threshold_value(
                fcs_path=str(fcs_path),
                scattering_channel=str(scattering_channel),
                threshold_payload=scattering_threshold_payload,
                threshold_input_value=scattering_threshold_input_value,
                max_events=int(max_events),
            )

            nbins = self._as_int(
                fluorescence_nbins,
                default=runtime_config.n_bins_for_plots,
                min_value=10,
                max_value=5000,
            )

            max_peaks = self._as_int(
                fluorescence_peak_count,
                default=runtime_config.default_peak_count,
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

            with FCSFile(str(fcs_path), writable=False) as fcs:
                fluorescence_values = fcs.column_copy(
                    str(fluorescence_channel),
                    dtype=float,
                    n=int(max_events),
                )
                scattering_values = fcs.column_copy(
                    str(scattering_channel),
                    dtype=float,
                    n=int(max_events),
                )

            gated = self.service.apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            peak_positions = [float(p) for p in peak_positions if self._as_float(p) is not None]
            peak_label = [f"{float(p):.3g}" for p in peak_positions if self._as_float(p) is not None]

            fig = self.service.make_histogram_with_lines(
                values=fluorescence_values,
                overlay_values=gated,
                nbins=nbins,
                xaxis_title="Fluorescence (a.u.)",
                line_positions=peak_positions,
                line_labels=peak_label,
                base_name="all events",
                overlay_name="gated events",
            )

            peak_positions = [float(p) for p in peak_positions if self._as_float(p) is not None]
            peak_label = [f"{float(p):.3g}" for p in peak_positions if self._as_float(p) is not None]

            updated_table = self._inject_peak_modes_into_table(
                table_data=table_data,
                peak_positions=peak_positions,
            )

            peak_lines_payload = {"positions": peak_positions, "labels": peak_label}

            return updated_table, peak_lines_payload

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