from typing import Any, List, Optional

import numpy as np

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages import styling
from RosettaX.pages.runtime_config import get_runtime_config
from RosettaX.reader import FCSFile
from RosettaX.pages.fluorescence.utils import make_histogram_with_lines, add_vertical_lines


class PeaksSection:
    """
    Fluorescence histogram section after scattering threshold gating, with peak detection.

    Responsibilities
    ----------------
    - Let the user select a fluorescence detector column.
    - Build a fluorescence histogram and an overlay histogram for gated events.
    - Allow peak finding on the gated distribution and display peak lines on the histogram.
    - Optionally inject found peak positions into an existing DataTable (bead table).

    Expected external attributes
    ----------------------------
    This class assumes these attributes exist on `self`:

    - self.ids: namespace containing component IDs
    - self.graph_style: style dict for plotly graphs
    - self.default_fluorescence_nbins: int, used when estimating threshold as a fallback
    - self._as_float(...), self._as_int(...): parsing helpers (implemented below for completeness)
    - self._empty_fig(): helper returning an empty plotly figure (implemented below)

    Notes
    -----
    This module reads FCS columns directly using `FCSFile` with the file path stored in the UI store,
    rather than using a long lived backend instance, to avoid stale paths and file handle issues.
    """

    def _fluorescence_get_layout(self) -> dbc.Card:
        """
        Build the Dash layout for the fluorescence after thresholding section.

        Returns
        -------
        dbc.Card
            Card containing detector selection, peak controls, histogram, y scale switch and nbins input.
        """
        return dbc.Card(
            [
                self._fluorescence_build_header(),
                self._fluorescence_build_body(),
            ]
        )

    def _fluorescence_build_header(self) -> dbc.CardHeader:
        """
        Build the card header.

        Returns
        -------
        dbc.CardHeader
            Header for this section.
        """
        return dbc.CardHeader("3. Fluorescence channel after thresholding")

    def _fluorescence_build_body(self) -> dbc.CardBody:
        """
        Build the card body.

        Returns
        -------
        dbc.CardBody
            Body containing dropdowns and controls for histogram + peak finding.
        """
        return dbc.CardBody(
            [
                dash.html.Br(),
                self._fluorescence_build_detector_dropdown(),
                dash.html.Br(),
                self._fluorescence_build_peak_controls(),
                dash.html.Br(),
                dash.html.Br(),
                self._fluorescence_build_histogram_graph(),
                dash.html.Br(),
                self._fluorescence_build_yscale_switch(),
                dash.html.Br(),
                self._fluorescence_build_nbins_input(),
            ]
        )

    def _fluorescence_build_detector_dropdown(self) -> dash.html.Div:
        """
        Build the fluorescence detector dropdown row.

        Returns
        -------
        dash.html.Div
            A row containing a label and a Dropdown listing detector columns.
        """
        return dash.html.Div(
            [
                dash.html.Div("Fluorescence detector:"),
                dash.dcc.Dropdown(
                    id=self.ids.fluorescence_detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                ),
            ],
            style=styling.CARD,
        )

    def _fluorescence_build_peak_controls(self) -> dash.html.Div:
        """
        Build controls for peak finding.

        Returns
        -------
        dash.html.Div
            Row with peak count input and a button that triggers peak finding.
        """
        runtime_config = get_runtime_config()

        peak_count_input = dash.dcc.Input(
            id=self.ids.fluorescence_peak_count_input,
            type="number",
            min=1,
            step=1,
            value=runtime_config.default_peak_count,
            style={"width": "120px"},
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
            id=self.ids.fluorescence_find_peaks_btn,
            n_clicks=0,
            style={"marginLeft": "16px"},
        )

        return dash.html.Div(
            [peak_count_row, find_peaks_button],
            style={"display": "flex", "alignItems": "center"},
        )

    def _fluorescence_build_histogram_graph(self) -> dash.dcc.Loading:
        """
        Build the histogram graph wrapper.

        Returns
        -------
        dash.dcc.Loading
            Loading wrapper containing the fluorescence histogram graph.
        """
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.ids.graph_fluorescence_hist,
                style=self.graph_style,
            ),
            type="default",
        )

    def _fluorescence_build_yscale_switch(self) -> dbc.Checklist:
        """
        Build the y scale switch (log or linear counts).

        Returns
        -------
        dbc.Checklist
            Switch used to toggle log counts on the histogram.
        """
        return dbc.Checklist(
            id=self.ids.fluorescence_yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "block"},
        )

    def _fluorescence_build_nbins_input(self) -> dash.html.Div:
        """
        Build the histogram bin count input.

        Returns
        -------
        dash.html.Div
            Row containing a label and a numeric input for histogram bins.
        """
        runtime_config = get_runtime_config()

        return dash.html.Div(
            [
                dash.html.Div("number of bins:"),
                dash.dcc.Input(
                    id=self.ids.fluorescence_nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
            hidden=runtime_config.fluorescence_show_fluorescence_controls is not True,
        )

    @staticmethod
    def _inject_peak_modes_into_table(table_data: Optional[list[dict]], peak_positions: List[float]) -> list[dict]:
        """
        Inject peak positions into the bead table rows.

        Behavior
        --------
        - Ensures there are at least as many rows as peak positions.
        - For each peak i, if row i "col2" is empty, sets it to the peak position.
        - Does not overwrite non empty existing values.

        Parameters
        ----------
        table_data : Optional[list[dict]]
            Existing table rows, typically from a Dash DataTable.
        peak_positions : List[float]
            Peak x positions in fluorescence units (a.u.).

        Returns
        -------
        list[dict]
            Updated table rows.
        """
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
        """
        Register callbacks for fluorescence histogram generation and peak finding.

        Registered callbacks
        --------------------
        - lock_fluorescence_source_channel:
          Stores the initially selected fluorescence channel in a store to prevent auto switching
          when new columns are injected (MESF, calibrated columns, etc).

        - refresh_fluorescence_hist_store:
          Computes a histogram figure (base and gated overlay) and stores it as a dict in a store.
          This callback reacts to file path, channel selection, nbins changes, and threshold changes.

        - update_fluorescence_yscale:
          Builds the displayed figure from the stored histogram dict, applies vertical peak lines,
          and toggles y axis between linear and log.

        - find_peaks_and_update_table:
          Runs peak detection on gated events and updates both:
            (a) the bead table data with peak positions injected
            (b) the peak lines store, which the display callback uses to draw vertical lines
        """

        def resolve_threshold_value(
            *,
            fcs_path: str,
            scattering_channel: str,
            threshold_payload: Optional[dict],
            threshold_input_value: Any,
            max_events: int,
        ) -> float:
            """
            Resolve the scattering threshold value used for gating.

            Resolution order
            ----------------
            1) Stored threshold payload (if present and valid)
            2) Threshold input value (if present and valid)
            3) Backend estimation (fallback)
            4) 0.0 as last resort

            Parameters
            ----------
            fcs_path : str
                Path to the current FCS file.
            scattering_channel : str
                Scattering channel used for threshold gating.
            threshold_payload : Optional[dict]
                Store payload containing a threshold value under key "threshold".
            threshold_input_value : Any
                Free text threshold value from UI input.
            max_events : int
                Number of points used for estimation.

            Returns
            -------
            float
                Threshold value used for gating.
            """
            runtime_config = get_runtime_config()
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
                        "nbins": int(runtime_config.n_bins_for_plots),
                        "number_of_points": int(max_events),
                    }
                )
                threshold_value = self._as_float(response.get("threshold"))

            if threshold_value is None:
                threshold_value = 0.0

            return float(threshold_value)

        @dash.callback(
            dash.Output(self.ids.fluorescence_peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.ids.fluorescence_detector_dropdown, "value"),
            dash.Input(self.ids.uploaded_fcs_path_store, "data"),
            dash.Input(self.ids.scattering_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(fluorescence_channel, fcs_path, scattering_channel):
            return {"positions": [], "labels": []}

        @dash.callback(
            dash.Output(self.ids.fluorescence_peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_detector_change(fluorescence_channel: Optional[str]):
            if fluorescence_channel is None:
                return dash.no_update

            chosen = str(fluorescence_channel).strip()
            if not chosen:
                return dash.no_update

            return {"positions": [], "labels": []}


        @dash.callback(
            dash.Output(self.ids.fluorescence_source_channel_store, "data", allow_duplicate=True),
            dash.Input(self.ids.fluorescence_detector_dropdown, "value"),
            dash.State(self.ids.fluorescence_source_channel_store, "data"),
            prevent_initial_call=True,
        )
        def lock_fluorescence_source_channel(
            fluorescence_channel: Optional[str],
            current_locked: Optional[str],
        ) -> Optional[str]:
            """
            Lock the fluorescence source channel at first selection.

            This prevents automatically switching the "source" column to a newly injected column
            (for example MESF) if dropdown options get refreshed later.

            Parameters
            ----------
            fluorescence_channel : Optional[str]
                Newly selected fluorescence dropdown value.
            current_locked : Optional[str]
                Currently locked source channel (if any).

            Returns
            -------
            Optional[str]
                The chosen channel when not already locked, otherwise dash.no_update.
            """
            if not fluorescence_channel:
                return dash.no_update

            chosen = str(fluorescence_channel).strip()
            if not chosen:
                return dash.no_update

            if isinstance(current_locked, str) and current_locked.strip():
                return dash.no_update

            return chosen

        @dash.callback(
            dash.Output(self.ids.fluorescence_hist_store, "data", allow_duplicate=True),
            dash.Input(self.ids.uploaded_fcs_path_store, "data"),
            dash.Input(self.ids.scattering_detector_dropdown, "value"),
            dash.Input(self.ids.fluorescence_detector_dropdown, "value"),
            dash.Input(self.ids.fluorescence_nbins_input, "value"),
            dash.Input(self.ids.scattering_threshold_store, "data"),
            dash.Input(self.ids.scattering_threshold_input, "value"),
            dash.State(self.ids.max_events_for_plots_input, "value", allow_optional=True),
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
        ) -> Any:
            """
            Refresh the stored fluorescence histogram figure.

            This callback:
            - Loads fluorescence and scattering columns from the current FCS file.
            - Applies gating based on scattering threshold.
            - Builds a histogram figure with base and gated overlay.
            - Stores the plotly figure dict in a `dcc.Store` for display and further decoration.

            Returns
            -------
            Any
                Plotly figure as dict if successful, otherwise dash.no_update.
            """
            runtime_config = get_runtime_config()
            if not bool(runtime_config.fluorescence_show_fluorescence_controls):
                return dash.no_update

            fcs_path_clean = str(fcs_path or "").strip()
            scattering_clean = str(scattering_channel or "").strip()
            fluorescence_clean = str(fluorescence_channel or "").strip()

            if not fcs_path_clean or not scattering_clean or not fluorescence_clean:
                return dash.no_update

            max_events_for_plots_int = self._as_int(
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
                max_events=max_events_for_plots_int,
            )

            nbins = self._as_int(
                fluorescence_nbins,
                default=runtime_config.n_bins_for_plots,
                min_value=10,
                max_value=5000,
            )

            with FCSFile(fcs_path_clean, writable=False) as fcs:
                cols = [str(c).strip() for c in fcs.get_column_names()]
                if fluorescence_clean not in cols or scattering_clean not in cols:
                    return dash.no_update

                try:
                    fluorescence_values = fcs.column_copy(
                        fluorescence_clean,
                        dtype=float,
                        n=max_events_for_plots_int,
                    )
                    scattering_values = fcs.column_copy(
                        scattering_clean,
                        dtype=float,
                        n=max_events_for_plots_int,
                    )
                except KeyError:
                    return dash.no_update

            gated = self.apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            fig = make_histogram_with_lines(
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

        @dash.callback(
            dash.Output(self.ids.graph_fluorescence_hist, "figure"),
            dash.Input(self.ids.fluorescence_yscale_switch, "value"),
            dash.Input(self.ids.fluorescence_hist_store, "data"),
            dash.Input(self.ids.fluorescence_peak_lines_store, "data"),
        )
        def update_fluorescence_yscale(yscale_selection: Any, stored_figure: Any, peak_lines: Any) -> go.Figure:
            """
            Update the displayed fluorescence histogram figure.

            This callback:
            - Rehydrates the figure from `fluorescence_hist_store`.
            - Adds peak vertical lines from `fluorescence_peak_lines_store`.
            - Applies y axis log or linear scaling.

            Parameters
            ----------
            yscale_selection : Any
                Checklist value list containing "log" when log scale is enabled.
            stored_figure : Any
                Plotly figure dict from the histogram store.
            peak_lines : Any
                Dict with keys "positions" and "labels" describing peak vertical lines.

            Returns
            -------
            go.Figure
                Displayed figure.
            """
            runtime_config = get_runtime_config()
            must_show_fluorescence_histogram = bool(runtime_config.fluorescence_show_fluorescence_controls)

            if not must_show_fluorescence_histogram:
                return self._empty_fig()

            if not stored_figure:
                fig = go.Figure()
                fig.update_layout(title="Select file + channels first.", separators=".,")
                return fig

            fig = go.Figure(stored_figure)

            positions: list = []
            labels: list = []
            if isinstance(peak_lines, dict):
                positions = peak_lines.get("positions") or []
                labels = peak_lines.get("labels") or []

            fig = add_vertical_lines(
                fig=fig,
                line_positions=positions,
                line_labels=labels,
            )

            use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)
            fig.update_yaxes(type="log" if use_log else "linear")
            return fig

        @dash.callback(
            dash.Output(self.ids.bead_table, "data", allow_duplicate=True),
            dash.Output(self.ids.fluorescence_peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.ids.fluorescence_find_peaks_btn, "n_clicks"),
            dash.State(self.ids.uploaded_fcs_path_store, "data"),
            dash.State(self.ids.scattering_detector_dropdown, "value"),
            dash.State(self.ids.fluorescence_detector_dropdown, "value"),
            dash.State(self.ids.fluorescence_nbins_input, "value"),
            dash.State(self.ids.fluorescence_peak_count_input, "value"),
            dash.State(self.ids.max_events_for_plots_input, "value", allow_optional=True),
            dash.State(self.ids.scattering_threshold_store, "data"),
            dash.State(self.ids.scattering_threshold_input, "value"),
            dash.State(self.ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def find_peaks_and_update_table(
            n_clicks: int,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            fluorescence_channel: Optional[str],
            fluorescence_nbins: Any,
            fluorescence_peak_count: Any,
            max_events_for_plots: Any,
            scattering_threshold_payload: Optional[dict],
            scattering_threshold_input_value: Any,
            table_data: Optional[list[dict]],
        ) -> tuple:
            """
            Find fluorescence peaks on gated events and update both the bead table and peak line store.

            Parameters
            ----------
            n_clicks : int
                Click count from "Find peaks" button.
            fcs_path : Optional[str]
                Current FCS file path.
            scattering_channel : Optional[str]
                Current scattering channel.
            fluorescence_channel : Optional[str]
                Current fluorescence channel.
            fluorescence_nbins : Any
                Histogram bins used for plotting (not required for peak finding, but used for consistent display).
            fluorescence_peak_count : Any
                Maximum number of peaks to return.
            max_events_for_plots : Any
                Maximum number of events to load from the file.
            scattering_threshold_payload : Optional[dict]
                Stored threshold data.
            scattering_threshold_input_value : Any
                Manual threshold input value.
            table_data : Optional[list[dict]]
                Current bead table rows to inject peaks into.

            Returns
            -------
            tuple
                (updated_table_rows, peak_lines_payload) or (dash.no_update, dash.no_update) when not applicable.
            """
            runtime_config = get_runtime_config()

            if not runtime_config.fluorescence_show_fluorescence_controls:
                return dash.no_update, dash.no_update

            if not fcs_path or not scattering_channel or not fluorescence_channel:
                return dash.no_update, dash.no_update

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

            peak_positions_raw = peaks_payload.get("peak_positions", []) or []

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

            gated = self.apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            peak_positions: List[float] = []
            for p in peak_positions_raw:
                v = self._as_float(p)
                if v is None:
                    continue
                peak_positions.append(float(v))

            peak_labels = [f"{float(p):.3g}" for p in peak_positions]

            _ = make_histogram_with_lines(
                values=fluorescence_values,
                overlay_values=gated,
                nbins=nbins,
                xaxis_title="Fluorescence (a.u.)",
                line_positions=peak_positions,
                line_labels=peak_labels,
                base_name="all events",
                overlay_name="gated events",
            )

            updated_table = self._inject_peak_modes_into_table(
                table_data=table_data,
                peak_positions=peak_positions,
            )

            peak_lines_payload = {"positions": peak_positions, "labels": peak_labels}

            return updated_table, peak_lines_payload

    def _empty_fig(self) -> go.Figure:
        """
        Create a minimal empty figure.

        Returns
        -------
        go.Figure
            Figure with consistent separators and no data.
        """
        fig = go.Figure()
        fig.update_layout(separators=".,")
        return fig

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        """
        Parse a value into a finite float.

        Parameters
        ----------
        value : Any
            Candidate value from a UI component.

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
        Parse a value into an int, with fallback and clamping.

        Parameters
        ----------
        value : Any
            Candidate value from a UI component.
        default : int
            Value used if parsing fails.
        min_value : int
            Minimum allowed value after parsing.
        max_value : int
            Maximum allowed value after parsing.

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

    @staticmethod
    def apply_gate(*, fluorescence_values: np.ndarray, scattering_values: np.ndarray, threshold: float) -> np.ndarray:
        fluorescence_values = np.asarray(fluorescence_values, dtype=float)
        scattering_values = np.asarray(scattering_values, dtype=float)

        mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)
        mask = mask & (scattering_values >= float(threshold))

        return fluorescence_values[mask]
