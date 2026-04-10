from typing import Any, List, Optional

import numpy as np

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines, add_vertical_lines, _make_info_figure
from RosettaX.utils.casting import _as_float, _as_int


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

    - self.page.ids: namespace containing component IDs
    - self.graph_style: style dict for plotly graphs
    - self.default_fluorescence_nbins: int, used when estimating threshold as a fallback
    - _as_float(...), _as_float(...): parsing helpers (implemented below for completeness)
    - self._empty_fig(): helper returning an empty plotly figure (implemented below)

    Notes
    -----
    This module reads FCS columns directly using `FCSFile` with the file path stored in the UI store,
    rather than using a long lived backend instance, to avoid stale paths and file handle issues.
    """

    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        """
        Build the Dash layout for the fluorescence after thresholding section.

        Returns
        -------
        dbc.Card
            Card containing detector selection, peak controls, histogram, y scale switch and nbins input.
        """
        return dbc.Card(
            [
                self.build_header(),
                self.build_body(),
            ]
        )

    def build_header(self) -> dbc.CardHeader:
        """
        Build the card header.

        Returns
        -------
        dbc.CardHeader
            Header for this section.
        """
        return dbc.CardHeader("3. Fluorescence channel after thresholding")

    def build_body(self) -> dbc.CardBody:
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
                self._build_detector_dropdown(),
                dash.html.Br(),
                self._build_peak_controls(),
                dash.html.Br(),
                self._build_graph_toggle_switch(),
                dash.html.Br(),
                self._build_graph_controls_container(),
            ]
        )

    def _build_graph_toggle_switch(self) -> dash.html.Div:
        """
        Build the local switch controlling whether the histogram graph is shown.
        """
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Fluorescence.graph_toggle_switch,
                    options=[{"label": "Show histogram", "value": "enabled"}],
                    value=[],
                    switch=True,
                ),
            ],
            style=styling.CARD,
        )


    def _build_graph_controls_container(self) -> dash.html.Div:
        """
        Build the container holding graph and graph related controls.
        """
        return dash.html.Div(
            [
                dash.html.Br(),
                self._build_histogram_graph(),
                dash.html.Br(),
                self._build_yscale_switch(),
                dash.html.Br(),
                self._build_nbins_input(),
            ],
            id=self.page.ids.Fluorescence.graph_toggle_container,
            style={"display": "none"},
        )

    def _build_detector_dropdown(self) -> dash.html.Div:
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
                    id=self.page.ids.Fluorescence.detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_peak_controls(self) -> dash.html.Div:
        """
        Build controls for peak finding.

        Returns
        -------
        dash.html.Div
            Row with peak count input and a button that triggers peak finding.
        """
        runtime_config = RuntimeConfig()

        peak_count_input = dash.dcc.Input(
            id=self.page.ids.Fluorescence.peak_count_input,
            type="number",
            min=1,
            step=1,
            value=runtime_config.peak_count,
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
            id=self.page.ids.Fluorescence.find_peaks_btn,
            n_clicks=0,
            style={"marginLeft": "16px"},
        )

        return dash.html.Div(
            [peak_count_row, find_peaks_button],
            style={"display": "flex", "alignItems": "center"},
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        """
        Build the histogram graph wrapper.

        Returns
        -------
        dash.dcc.Loading
            Loading wrapper containing the fluorescence histogram graph.
        """
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Fluorescence.graph_hist,
                style=self.page.style["graph"],
            ),
            type="default",
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        """
        Build the y scale switch (log or linear counts).

        Returns
        -------
        dbc.Checklist
            Switch used to toggle log counts on the histogram.
        """
        return dbc.Checklist(
            id=self.page.ids.Fluorescence.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
            style={"display": "block"},
        )

    def _build_nbins_input(self) -> dash.html.Div:
        """
        Build the histogram bin count input.

        Returns
        -------
        dash.html.Div
            Row containing a label and a numeric input for histogram bins.
        """
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Fluorescence.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
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

    def _register_callbacks(self) -> None:
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
            runtime_config = RuntimeConfig()
            threshold_value: Optional[float] = None

            if isinstance(threshold_payload, dict):
                threshold_value = _as_float(threshold_payload.get("threshold"))

            if threshold_value is None:
                threshold_value = _as_float(threshold_input_value)

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
                threshold_value = _as_float(response.get("threshold"))

            if threshold_value is None:
                threshold_value = 0.0

            return float(threshold_value)

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.peak_count_input, "value"),
            dash.Output(self.page.ids.Fluorescence.nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(runtime_config_data):
            runtime_config = RuntimeConfig()

            if not isinstance(runtime_config_data, dict):
                return (
                    runtime_config.peak_count,
                    runtime_config.n_bins_for_plots,
                )

            return (
                runtime_config_data.get("peak_count", runtime_config.peak_count),
                runtime_config_data.get("n_bins_for_plots", runtime_config.n_bins_for_plots),
            )

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.graph_toggle_container, "style"),
            dash.Input(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_fluorescence_graph_container(graph_toggle_value: Any) -> dict:
            enabled = isinstance(graph_toggle_value, list) and ("enabled" in graph_toggle_value)
            return {"display": "block"} if enabled else {"display": "none"}


        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.Input(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def clear_peak_lines_on_context_change(fluorescence_channel, fcs_path, scattering_channel):
            return {"positions": [], "labels": []}

        @dash.callback(
            dash.Output(self.page.ids.Fluorescence.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
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
            dash.Output(self.page.ids.Fluorescence.source_channel_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.source_channel_store, "data"),
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
            dash.Output(self.page.ids.Fluorescence.hist_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.Input(self.page.ids.Fluorescence.nbins_input, "value"),
            dash.Input(self.page.ids.Scattering.threshold_store, "data"),
            dash.Input(self.page.ids.Scattering.threshold_input, "value"),
            dash.State(self.page.ids.Load.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=True,
        )
        def refresh_fluorescence_hist_store(
            graph_toggle_value: Any,
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
            graph_enabled = isinstance(graph_toggle_value, list) and ("enabled" in graph_toggle_value)
            if not graph_enabled:
                return dash.no_update

            runtime_config = RuntimeConfig()

            fcs_path_clean = str(fcs_path or "").strip()
            scattering_clean = str(scattering_channel or "").strip()
            fluorescence_clean = str(fluorescence_channel or "").strip()

            if not fcs_path_clean or not scattering_clean or not fluorescence_clean:
                return dash.no_update

            max_events_for_plots_int = _as_int(
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

            nbins = _as_int(
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
            dash.Output(self.page.ids.Fluorescence.graph_hist, "figure"),
            dash.Input(self.page.ids.Fluorescence.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Fluorescence.yscale_switch, "value"),
            dash.Input(self.page.ids.Fluorescence.hist_store, "data"),
            dash.Input(self.page.ids.Fluorescence.peak_lines_store, "data"),
        )
        def update_fluorescence_yscale(
            graph_toggle_value: Any,
            yscale_selection: Any,
            stored_figure: Any,
            peak_lines: Any,
        ) -> go.Figure:
            """
            Update the displayed fluorescence histogram figure.
            """
            graph_enabled = isinstance(graph_toggle_value, list) and ("enabled" in graph_toggle_value)

            if not graph_enabled:
                return _make_info_figure("Histogram is hidden.")

            if not stored_figure:
                return _make_info_figure("Select file and channels first.")

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
            fig.update_layout(separators=".,")
            return fig

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Output(self.page.ids.Fluorescence.peak_lines_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Fluorescence.find_peaks_btn, "n_clicks"),
            dash.State(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.nbins_input, "value"),
            dash.State(self.page.ids.Fluorescence.peak_count_input, "value"),
            dash.State(self.page.ids.Load.max_events_for_plots_input, "value", allow_optional=True),
            dash.State(self.page.ids.Scattering.threshold_store, "data"),
            dash.State(self.page.ids.Scattering.threshold_input, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
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
            runtime_config = RuntimeConfig()

            if not fcs_path or not scattering_channel or not fluorescence_channel:
                return dash.no_update, dash.no_update

            max_events = _as_int(
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

            nbins = _as_int(
                fluorescence_nbins,
                default=runtime_config.n_bins_for_plots,
                min_value=10,
                max_value=5000,
            )

            max_peaks = _as_int(
                fluorescence_peak_count,
                default=runtime_config.peak_count,
                min_value=1,
                max_value=100,
            )

            backend = BackEnd(str(fcs_path))

            peaks_payload = backend.find_fluorescence_peaks(
                column=str(fluorescence_channel),
                max_peaks=int(max_peaks),
                gating_column=str(scattering_channel),
                gating_threshold=float(threshold_value),
                number_of_points=int(max_events),
                debug=False
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
                v = _as_float(p)
                if v is None:
                    continue
                peak_positions.append(float(v))

            peak_labels = [f"{float(p):.3g}" for p in peak_positions]

            print(f"Found peaks at positions: {peak_positions}")

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
    def apply_gate(*, fluorescence_values: np.ndarray, scattering_values: np.ndarray, threshold: float) -> np.ndarray:
        fluorescence_values = np.asarray(fluorescence_values, dtype=float)
        scattering_values = np.asarray(scattering_values, dtype=float)

        mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)
        mask = mask & (scattering_values >= float(threshold))

        return fluorescence_values[mask]