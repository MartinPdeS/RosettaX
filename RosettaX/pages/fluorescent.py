from pathlib import Path
from typing import Any, List, Optional, Tuple
import base64
import tempfile

import dash
from dash import Input, Output, State, callback, dash_table, dcc, html
import dash_bootstrap_components as dbc
from dash import callback_context
import numpy as np
import plotly.graph_objs as go

from RosettaX.backend import BackEnd
from RosettaX.pages.sidebar import sidebar_html


class FluorescentCalibrationIds:
    page_name = "fluorescent_calibration"

    upload = f"{page_name}-upload-data"
    upload_filename = f"{page_name}-upload-file-name"

    uploaded_fcs_path_store = f"{page_name}-uploaded-fcs-path-store"
    calibration_store = f"{page_name}-calibration-store"
    scattering_threshold_store = f"{page_name}-scattering-threshold-store"

    scattering_detector_dropdown = f"{page_name}-scattering-detector-dropdown"
    scattering_nbins_input = f"{page_name}-scattering-nbins"
    scattering_find_threshold_btn = f"{page_name}-find-scattering-threshold-btn"
    scattering_threshold_input = f"{page_name}-scattering-threshold-input"
    graph_scattering_hist = f"{page_name}-graph-scattering-hist"

    fluorescence_detector_dropdown = f"{page_name}-fluorescence-detector-dropdown"
    fluorescence_nbins_input = f"{page_name}-fluorescence-nbins"
    fluorescence_peak_count_input = f"{page_name}-fluorescence-peak-count"
    fluorescence_find_peaks_btn = f"{page_name}-find-fluorescence-peaks-btn"
    graph_fluorescence_hist = f"{page_name}-graph-fluorescence-hist"

    bead_table = f"{page_name}-bead-spec-table"
    add_row_btn = f"{page_name}-add-row-btn"
    calibrate_btn = f"{page_name}-calibrate-btn"

    graph_calibration = f"{page_name}-graph-calibration"
    slope_out = f"{page_name}-slope-out"
    intercept_out = f"{page_name}-intercept-out"
    r_squared_out = f"{page_name}-r-squared-out"

    apply_btn = f"{page_name}-apply-btn"
    preview_div = f"{page_name}-preview-div"

    channel_name = f"{page_name}-channel-name"
    file_name = f"{page_name}-file-name"

    save_btn = f"{page_name}-save-btn"
    save_out = f"{page_name}-save-out"

    sidebar_store = "apply-calibration-store"
    sidebar_content = "sidebar-content"


class FluorescentCalibrationPage:
    def __init__(self) -> None:
        """Initialize the Fluorescent Calibration Page."""
        self.ids = FluorescentCalibrationIds()

        self.bead_table_columns = [
            {"name": "Intensity (MESF)", "id": "col1", "editable": True},
            {"name": "Intensity (a.u.)", "id": "col2", "editable": True},
        ]
        self.default_bead_rows = [{"col1": "", "col2": ""} for _ in range(3)]

        self.upload_style = {
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        }

        self.card_body_scroll = {"maxHeight": "60vh", "overflowY": "auto"}
        self.graph_style = {"width": "100%", "height": "45vh"}

    def register(self) -> None:
        """Register the page in Dash pages and set up callbacks."""
        dash.register_page(__name__, path="/fluorescent_calibration", name="Fluorescent Calibration")
        self._register_callbacks()

    def layout(self) -> html.Div:
        """
        Defines the layout for the Fluorescent Calibration page.

        Returns
        -------
        html.Div
            The layout for the Fluorescent Calibration page.
        """
        ids = self.ids

        section_0 = [
            dbc.CardHeader("2. Scattering channel"),
            dbc.CardBody(
                [
                    html.Br(),
                    html.Div(
                        [
                            html.Div("Scattering detector:"),
                            dcc.Dropdown(id=ids.scattering_detector_dropdown, style={"width": "500px"}),
                        ],
                        style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    ),
                    html.Br(),
                    html.Div(
                        [
                            html.Div("number of bins:"),
                            dcc.Input(
                                id=ids.scattering_nbins_input,
                                type="number",
                                min=10,
                                step=10,
                                value=200,
                                style={"width": "160px"},
                            ),
                        ],
                        style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    ),
                    html.Br(),
                    html.Button("Estimate threshold", id=ids.scattering_find_threshold_btn, n_clicks=0),
                    html.Br(),
                    html.Br(),
                    html.Div(
                        [
                            html.Div("Threshold:"),
                            dcc.Input(
                                id=ids.scattering_threshold_input,
                                type="text",
                                value="",
                                style={"width": "220px"},
                            ),
                        ],
                        style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    ),
                    html.Br(),
                    dcc.Graph(id=ids.graph_scattering_hist, style=self.graph_style),
                ]
            ),
        ]

        section_1 = [
            dbc.CardHeader("3. Fluorescence channel after thresholding"),
            dbc.CardBody(
                [
                    html.Br(),
                    html.Div(
                        [
                            html.Div("Fluorescence detector:"),
                            dcc.Dropdown(id=ids.fluorescence_detector_dropdown, style={"width": "500px"}),
                        ],
                        style={"display": "flex", "gap": "12px", "alignItems": "center"},
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
                                value=200,
                                style={"width": "160px"},
                            ),
                        ],
                        style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    ),
                    html.Br(),
                    html.Div(
                        [
                            html.Div("Number of peaks to look for:"),
                            dcc.Input(
                                id=ids.fluorescence_peak_count_input,
                                type="number",
                                min=2, # minimum 2 peaks needed otherwise cant fit a line
                                step=1,
                                value=3,
                                style={"width": "160px"},
                            ),
                        ],
                        style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    ),
                    html.Br(),
                    html.Button("Find peaks", id=ids.fluorescence_find_peaks_btn, n_clicks=0),
                    html.Br(),
                    html.Br(),
                    dcc.Graph(id=ids.graph_fluorescence_hist, style=self.graph_style),
                ]
            ),
        ]


        section_2 = [
            dbc.CardHeader("4. Bead specifications"),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        html.Br(),
                        dash_table.DataTable(
                            id=ids.bead_table,
                            columns=self.bead_table_columns,
                            data=self.default_bead_rows,
                            editable=True,
                            row_deletable=True,
                            style_table={"overflowX": "auto"},
                        ),
                        html.Div([html.Button("Add Row", id=ids.add_row_btn, n_clicks=0)], style={"marginTop": "10px"}),
                        html.Br(),
                        html.Button("Calibrate", id=ids.calibrate_btn, n_clicks=0),
                    ],
                    style=self.card_body_scroll,
                ),
                id=f"collapse-{ids.page_name}-beadspec",
                is_open=True,
            ),
        ]

        section_3 = [
            dbc.CardHeader("5. Calibration output"),
            dbc.CardBody(
                [
                    dcc.Graph(id=ids.graph_calibration, style=self.graph_style),
                    html.Br(),
                    html.Div(
                        [
                            html.Div([html.Div("Slope:"), html.Div("", id=ids.slope_out)], style={"display": "flex", "gap": "8px"}),
                            html.Div([html.Div("Intercept:"), html.Div("", id=ids.intercept_out)], style={"display": "flex", "gap": "8px"}),
                            html.Div([html.Div("R²:"), html.Div("", id=ids.r_squared_out)], style={"display": "flex", "gap": "8px"}),
                        ]
                    ),
                    html.Br(),
                    html.Button("Apply Calibration", id=ids.apply_btn, n_clicks=0),
                    html.Div(id=ids.preview_div),
                ]
            ),
        ]

        section_4 = [
            dbc.CardHeader("6. Save export calibration"),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        html.Label("Calibrated MESF Channel Name:"),
                        dcc.Input(id=ids.channel_name, type="text", value=""),
                        html.Br(),
                        html.Label("Save Calibration Setup As:"),
                        dcc.Input(id=ids.file_name, type="text", value=""),
                        html.Br(),
                        html.Button("Save Fluorescent Calibration", id=ids.save_btn, n_clicks=0),
                        html.Div(id=ids.save_out),
                    ]
                ),
                id=f"collapse-{ids.page_name}-save",
                is_open=True,
            ),
        ]

        return html.Div(
            [
                dcc.Store(id=ids.uploaded_fcs_path_store, storage_type="session"),
                dcc.Store(id=ids.calibration_store, storage_type="session"),
                dcc.Store(id=ids.scattering_threshold_store, storage_type="session"),
                html.H1("Create and Save A New Fluorescent Calibration"),
                self._collapse_card(
                    title="1. Upload Bead File",
                    children=[
                        dcc.Upload(
                            id=ids.upload,
                            children=html.Div(["Drag and Drop or ", html.A("Select Bead File")]),
                            style=self.upload_style,
                            multiple=False,
                        ),
                        html.Div(id=ids.upload_filename),
                    ],
                ),
                html.Br(),
                dbc.Card(section_0),
                html.Br(),
                dbc.Card(section_1),
                html.Br(),
                dbc.Card(section_2),
                html.Br(),
                dbc.Card(section_3),
                html.Br(),
                dbc.Card(section_4),
            ]
        )

    def _collapse_card(self, title: str, children, is_open: bool = True, height_style: Optional[dict] = None):
        """
        Create a collapsible card component.

        Parameters
        ----------

        title
            Title of the collapsible card.
        children
            Dash components to include inside the card body.
        is_open
            Whether the card is initially open or closed.
        height_style
            Optional style dict to set the height of the collapse container.
        Returns
        -------
        dbc.Collapse
            The collapsible card component.

        """
        collapse_id = f"collapse-{self.ids.page_name}-{title.lower().replace(' ', '_')}"
        style = {} if height_style is None else height_style
        return dbc.Collapse(
            dbc.Card([dbc.CardHeader(title), dbc.CardBody(children, style=self.card_body_scroll)]),
            id=collapse_id,
            is_open=is_open,
            style=style,
        )

    def _register_callbacks(self) -> None:
        """Register all callbacks for the Fluorescent Calibration page."""
        ids = self.ids

        @callback(
            Output(ids.uploaded_fcs_path_store, "data"),
            Output(ids.upload_filename, "children"),
            Output(ids.scattering_detector_dropdown, "options"),
            Output(ids.fluorescence_detector_dropdown, "options"),
            Output(ids.scattering_detector_dropdown, "value"),
            Output(ids.fluorescence_detector_dropdown, "value"),
            Input(ids.upload, "contents"),
            State(ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def on_upload_bead_file(contents: Optional[str], filename: Optional[str]):
            if not contents:
                return dash.no_update, "", [], [], None, None

            try:
                temp_path = self._write_upload_to_tempfile(contents=contents, filename=filename or "uploaded_file")
            except Exception as exc:
                return dash.no_update, f"Upload failed: {exc}", [], [], None, None

            try:
                backend = BackEnd(temp_path)
                columns = list(getattr(backend.fcs_file, "data").columns)
            except Exception as exc:
                msg = f"Saved upload to {temp_path} but BackEnd could not read it: {exc}"
                return temp_path, msg, [], [], None, None

            options = [{"label": c, "value": c} for c in columns]
            default_value = columns[0] if columns else None
            msg = f"Selected file: {filename}  Saved as: {temp_path}"
            return temp_path, msg, options, options, default_value, default_value

        @callback(
            Output(ids.graph_scattering_hist, "figure"),
            Output(ids.scattering_threshold_store, "data"),
            Output(ids.scattering_threshold_input, "value"),
            Input(ids.scattering_find_threshold_btn, "n_clicks"),
            Input(ids.uploaded_fcs_path_store, "data"),
            Input(ids.scattering_detector_dropdown, "value"),
            Input(ids.scattering_nbins_input, "value"),
            Input(ids.scattering_threshold_input, "value"),
            State(ids.scattering_threshold_store, "data"),
            prevent_initial_call=True,
        )
        def scattering_section(
            n_clicks_estimate: int,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            scattering_nbins: Any,
            threshold_input_value: Any,
            stored_threshold_payload: Optional[dict],
        ):
            if not fcs_path or not scattering_channel:
                return self._empty_fig(), dash.no_update, dash.no_update

            nbins = self._as_int(scattering_nbins, default=200, min_value=10, max_value=5000)

            triggered = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""

            backend = BackEnd(fcs_path)
            values = self._get_column_values(backend=backend, column=str(scattering_channel))

            stored_thr = self._as_float((stored_threshold_payload or {}).get("threshold"))
            input_thr = self._as_float(threshold_input_value)

            if triggered == ids.scattering_find_threshold_btn:
                response = backend.process_scattering(
                    {
                        "operation": "estimate_scattering_threshold",
                        "column": str(scattering_channel),
                        "nbins": int(nbins),
                        "number_of_points": 200_000,
                    }
                )
                thr = self._as_float(response.get("threshold"))
                if thr is None:
                    thr = 0.0
            else:
                thr = input_thr if input_thr is not None else (stored_thr if stored_thr is not None else 0.0)

            fig = self._make_histogram_with_lines(
                values=values,
                nbins=nbins,
                xaxis_title="Scattering (a.u.)",
                line_positions=[float(thr)],
                line_labels=[f"thr={float(thr):.3g}"],
            )

            next_store = {
                "scattering_channel": str(scattering_channel),
                "threshold": float(thr),
                "nbins": int(nbins),
            }

            return fig, next_store, f"{float(thr):.6g}"

        @callback(
            Output(ids.graph_fluorescence_hist, "figure"),
            Output(ids.bead_table, "data", allow_duplicate=True),
            Input(ids.fluorescence_find_peaks_btn, "n_clicks"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.scattering_detector_dropdown, "value"),
            State(ids.scattering_threshold_store, "data"),
            State(ids.fluorescence_detector_dropdown, "value"),
            State(ids.fluorescence_nbins_input, "value"),
            State(ids.fluorescence_peak_count_input, "value"),
            State(ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def fluorescence_section(
            n_clicks: int,
            fcs_path: Optional[str],
            scattering_channel: Optional[str],
            threshold_payload: Optional[dict],
            fluorescence_channel: Optional[str],
            fluorescence_nbins: Any,
            peak_count: Any,
            table_data: Optional[list[dict]],
        ):
            if not fcs_path or not scattering_channel or not fluorescence_channel:
                return self._empty_fig(), dash.no_update

            if not isinstance(threshold_payload, dict):
                fig = self._empty_fig()
                fig.update_layout(title="Set the scattering threshold first.")
                return fig, dash.no_update

            threshold_value = self._as_float(threshold_payload.get("threshold"))
            if threshold_value is None:
                threshold_value = 0.0

            nbins = self._as_int(fluorescence_nbins, default=200, min_value=10, max_value=5000)
            max_peaks = self._as_int(peak_count, default=3, min_value=2, max_value=100)
            #TODO: discuss with martin minimum 2 peaks needed otherwise cant fit a line, but maybe user just wants to visualize the histogram and not fit a line, so maybe can allow 1 peak but then just dont fit a line in that case.

            backend = BackEnd(fcs_path)

            peaks_payload = backend.find_fluorescence_peaks(
                {
                    "column": str(fluorescence_channel),
                    "max_peaks": int(max_peaks),
                    "gating_column": str(scattering_channel),
                    "gating_threshold": float(threshold_value),
                    "number_of_points": 200_000,
                }
            )
            peak_positions = peaks_payload.get("peak_positions", [])

            fluorescence_values = self._get_column_values(backend=backend, column=str(fluorescence_channel))
            scattering_values = self._get_column_values(backend=backend, column=str(scattering_channel))

            gated = self._apply_gate(
                fluorescence_values=fluorescence_values,
                scattering_values=scattering_values,
                threshold=float(threshold_value),
            )

            fig = self._make_histogram_with_lines(
                values=gated,
                nbins=nbins,
                xaxis_title="Fluorescence (a.u.)",
                line_positions=[float(p) for p in peak_positions if self._as_float(p) is not None],
                line_labels=[f"{float(p):.3g}" for p in peak_positions if self._as_float(p) is not None],
            )

            updated_table = self._inject_peak_modes_into_table(
                table_data=table_data,
                peak_positions=peak_positions,
            )

            return fig, updated_table

        @callback(
            Output(ids.graph_calibration, "figure"),
            Output(ids.calibration_store, "data"),
            Output(ids.slope_out, "children"),
            Output(ids.intercept_out, "children"),
            Output(ids.r_squared_out, "children"),
            Input(ids.calibrate_btn, "n_clicks"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def calibrate(n_clicks: int, fcs_path: Optional[str], table_data: Optional[list[dict]]):
            if not fcs_path:
                fig = self._empty_fig()
                fig.update_layout(title="Upload a bead file first.")
                return fig, dash.no_update, "", ""

            mesf_array, intensity_array = self._extract_xy_from_table(table_data or [])
            if mesf_array.size < 2:
                fig = self._empty_fig()
                fig.update_layout(title="Need at least 2 points to calibrate.")
                return fig, dash.no_update, "", ""

            backend = BackEnd(fcs_path)
            calib_payload = backend.fit_fluorescence_calibration(
                {"MESF": mesf_array.tolist(), "intensity": intensity_array.tolist()}
            )

            slope_value = float(calib_payload.get("slope"))
            intercept_value = float(calib_payload.get("intercept"))
            R_squared = float(calib_payload.get("R_squared"))

            x_fit = np.linspace(float(np.min(intensity_array)), float(np.max(intensity_array)), 200)
            y_fit = slope_value * x_fit + intercept_value

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=intensity_array, y=mesf_array, mode="markers", name="beads"))
            fig.add_trace(go.Scatter(x=x_fit, y=y_fit, mode="lines", name="fit"))
            fig.update_layout(
                title="MESF calibration",
                xaxis_title="Intensity (a.u.)",
                yaxis_title="MESF",
                separators=".,",
            )

            return fig, calib_payload, f"{slope_value:.6g}", f"{intercept_value:.6g}", f"{R_squared:.6g}"

        @callback(
            Output(ids.bead_table, "data"),
            Input(ids.add_row_btn, "n_clicks"),
            State(ids.bead_table, "data"),
            State(ids.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, rows: List[dict], columns: List[dict]) -> List[dict]:
            next_rows = list(rows or [])
            next_rows.append({c["id"]: "" for c in columns})
            return next_rows

        @callback(
            Output(ids.preview_div, "children"),
            Input(ids.apply_btn, "n_clicks"),
            State(ids.calibration_store, "data"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_calibration(n_clicks: int, calib_payload: Optional[dict], bead_file_path: Optional[str], detector_column: Optional[str]):
            if not n_clicks:
                return dash.no_update
            if not calib_payload:
                return "No calibration yet. Run Calibrate first."
            if not bead_file_path:
                return "No bead file uploaded yet."
            if not detector_column:
                return "Select a fluorescence detector first."

            backend = BackEnd(bead_file_path)
            response = backend.apply_fluorescence_calibration(
                {"calibration": calib_payload, "column": str(detector_column), "preview_n": 10}
            )

            preview = response.get("preview")
            if preview is None:
                return "BackEnd did not return preview."
            return html.Pre(str(preview))

        @callback(
            Output(ids.save_out, "children"),
            Output(ids.sidebar_store, "data"),
            Output(ids.sidebar_content, "children"),
            Input(ids.save_btn, "n_clicks"),
            State(ids.file_name, "value"),
            State(ids.sidebar_store, "data"),
            State(ids.calibration_store, "data"),
            prevent_initial_call=True,
        )
        def save_calibration(n_clicks: int, file_name: str, sidebar_data: Optional[dict], calib_payload: Optional[dict]):
            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update
            if not file_name or not str(file_name).strip():
                return "Please provide a file name.", dash.no_update, dash.no_update
            if not calib_payload:
                return "No calibration payload to save. Run Calibrate first.", dash.no_update, dash.no_update

            next_sidebar = dict(sidebar_data or {})
            next_sidebar.setdefault("Fluorescent", [])
            next_sidebar["Fluorescent"] = list(next_sidebar["Fluorescent"])
            next_sidebar["Fluorescent"].append(file_name)

            next_sidebar.setdefault("payloads", {})
            next_sidebar["payloads"][f"Fluorescent/{file_name}"] = calib_payload

            return f'Calibration "{file_name}" saved successfully.', next_sidebar, sidebar_html(next_sidebar)

    @staticmethod
    def _write_upload_to_tempfile(contents: str, filename: str) -> str:
        header, b64data = contents.split(",", 1)
        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        out_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        out_path.write_bytes(raw)
        return str(out_path)

    @staticmethod
    def _empty_fig() -> go.Figure:
        fig = go.Figure()
        fig.update_layout(separators=".,")
        return fig

    @staticmethod
    def _get_column_values(backend: BackEnd, column: str) -> np.ndarray:
        values = backend.fcs_file.data[str(column)].to_numpy(dtype=float)
        return values

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

    def _extract_xy_from_table(self, table_data: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
        mesf_vals: List[float] = []
        au_vals: List[float] = []

        for row in table_data or []:
            mesf = self._as_float(row.get("col1"))
            au = self._as_float(row.get("col2"))
            if mesf is None or au is None:
                continue
            mesf_vals.append(mesf)
            au_vals.append(au)

        return np.asarray(mesf_vals, dtype=float), np.asarray(au_vals, dtype=float)

    @staticmethod
    def _apply_gate(fluorescence_values: np.ndarray, scattering_values: np.ndarray, threshold: float) -> np.ndarray:
        fluorescence_values = np.asarray(fluorescence_values, dtype=float)
        scattering_values = np.asarray(scattering_values, dtype=float)
        mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)
        mask = mask & (scattering_values >= float(threshold))
        return fluorescence_values[mask]

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

    @staticmethod
    def _make_histogram_with_lines(
        values: np.ndarray,
        nbins: int,
        xaxis_title: str,
        line_positions: List[float],
        line_labels: List[str],
    ) -> go.Figure:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        fig = go.Figure()
        fig.add_trace(go.Histogram(x=values, nbinsx=int(nbins), name="hist"))

        for x, label in zip(line_positions, line_labels):
            if not np.isfinite(float(x)):
                continue
            fig.add_vline(
                x=float(x),
                line_width=2,
                line_dash="dash",
                annotation_text=str(label),
                annotation_position="top",
            )

        fig.update_layout(
            xaxis_title=xaxis_title,
            yaxis_title="Count",
            bargap=0.02,
            showlegend=False,
            separators=".,",
        )
        return fig


_page = FluorescentCalibrationPage()
_page.register()
layout = _page.layout()
