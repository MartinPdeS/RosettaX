from typing import List, Optional, Tuple, Any

import dash
from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.reader import FCSFile

class OutputSection():
    def _output_get_layout(self) -> dbc.Card:
        ids = self.context.ids

        return dbc.Card(
            [
                dbc.CardHeader("5. Calibration output"),
                dbc.CardBody(
                    [
                        dcc.Loading(
                            dcc.Graph(id=ids.graph_calibration, style=self.context.graph_style),
                            type="default",
                        ),
                        html.Br(),
                        html.Div(
                            [
                                html.Div(
                                    [html.Div("Slope:"), html.Div("", id=ids.slope_out)],
                                    style={"display": "flex", "gap": "8px"},
                                ),
                                html.Div(
                                    [html.Div("Intercept:"), html.Div("", id=ids.intercept_out)],
                                    style={"display": "flex", "gap": "8px"},
                                ),
                                html.Div(
                                    [html.Div("R²:"), html.Div("", id=ids.r_squared_out)],
                                    style={"display": "flex", "gap": "8px"},
                                ),
                            ]
                        ),
                        html.Br(),
                        html.Button("Apply Calibration", id=ids.apply_btn, n_clicks=0),
                        html.Div(id=ids.preview_div),
                    ]
                ),
            ]
        )


    def _output_extract_xy_from_table(self, table_data: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
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
    def _output_compute_r_squared(*, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        mask = np.isfinite(y_true) & np.isfinite(y_pred)
        y_true = y_true[mask]
        y_pred = y_pred[mask]

        if y_true.size < 2:
            return float("nan")

        ss_res = float(np.sum((y_true - y_pred) ** 2))
        ss_tot = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
        if ss_tot <= 0.0:
            return float("nan")

        return 1.0 - ss_res / ss_tot

    def _output_register_callbacks(self) -> None:
        ids = self.context.ids

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
            fig = self._empty_fig()

            if not fcs_path:
                fig.update_layout(title="Upload a bead file first.")
                return fig, dash.no_update, "", "", ""

            mesf, intensity = self._output_extract_xy_from_table(table_data or [])
            if mesf.size < 2:
                fig.update_layout(title="Need at least 2 points to calibrate.")
                return fig, dash.no_update, "", "", ""

            # Fit MESF = slope * intensity + intercept
            x = np.asarray(intensity, dtype=float)
            y = np.asarray(mesf, dtype=float)

            mask = np.isfinite(x) & np.isfinite(y)
            x = x[mask]
            y = y[mask]
            if x.size < 2:
                fig.update_layout(title="Need at least 2 finite points.")
                return fig, dash.no_update, "", "", ""

            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            r2 = self._output_compute_r_squared(y_true=y, y_pred=y_pred)

            calib_payload = {
                "slope": float(slope),
                "intercept": float(intercept),
                "R_squared": float(r2),
            }

            x_fit = np.linspace(float(np.min(x)), float(np.max(x)), 200)
            y_fit = slope * x_fit + intercept

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="beads"))
            fig.add_trace(go.Scatter(x=x_fit, y=y_fit, mode="lines", name="fit"))
            fig.update_layout(
                title="MESF calibration",
                xaxis_title="Intensity (a.u.)",
                yaxis_title="MESF",
                separators=".,",
                hovermode="x unified",
            )

            return (
                fig,
                calib_payload,
                f"{float(slope):.6g}",
                f"{float(intercept):.6g}",
                f"{float(r2):.6g}",
            )

        @callback(
            Output(ids.preview_div, "children"),
            Input(ids.apply_btn, "n_clicks"),
            State(ids.calibration_store, "data"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_calibration(n_clicks, calib_payload, bead_file_path, detector_column):
            if not n_clicks:
                return dash.no_update

            if not isinstance(calib_payload, dict):
                return "No calibration yet. Run Calibrate first."
            if not bead_file_path:
                return "No bead file uploaded yet."
            if not detector_column:
                return "Select a fluorescence detector first."

            slope = calib_payload.get("slope")
            intercept = calib_payload.get("intercept")
            if slope is None or intercept is None:
                return "Calibration payload missing slope/intercept."

            slope = float(slope)
            intercept = float(intercept)

            with FCSFile(str(bead_file_path), writable=False) as fcs:
                raw = fcs.column_copy(str(detector_column), dtype=float, n=10)

            raw = np.asarray(raw, dtype=float)
            raw = raw[np.isfinite(raw)]
            calibrated = slope * raw + intercept

            return html.Pre(str(calibrated.tolist()))

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
