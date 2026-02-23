from typing import List, Optional, Tuple

import dash
from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.backend import BackEnd
from RosettaX.pages.fluorescence import BaseSection, SectionContext

class OutputSection(BaseSection):
    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)

    def layout(self) -> dbc.Card:
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

    @staticmethod
    def _extract_xy_from_table(table_data: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
        mesf_vals: List[float] = []
        au_vals: List[float] = []

        for row in table_data or []:
            mesf = BaseSection._as_float(row.get("col1"))
            au = BaseSection._as_float(row.get("col2"))
            if mesf is None or au is None:
                continue
            mesf_vals.append(mesf)
            au_vals.append(au)

        return np.asarray(mesf_vals, dtype=float), np.asarray(au_vals, dtype=float)

    @staticmethod
    def _compute_r_squared(*, y_true: np.ndarray, y_pred: np.ndarray) -> float:
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

    def register_callbacks(self) -> None:
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

            mesf_array, intensity_array = self._extract_xy_from_table(table_data or [])
            if mesf_array.size < 2:
                fig.update_layout(title="Need at least 2 points to calibrate.")
                return fig, dash.no_update, "", "", ""

            backend = BackEnd(fcs_path)
            calib_payload = backend.fit_fluorescence_calibration(
                {"MESF": mesf_array.tolist(), "intensity": intensity_array.tolist()}
            )

            slope_value = float(calib_payload.get("slope"))
            intercept_value = float(calib_payload.get("intercept"))

            predicted = slope_value * intensity_array + intercept_value
            r_squared_value = self._compute_r_squared(y_true=mesf_array, y_pred=predicted)

            if isinstance(calib_payload, dict) and "R_squared" not in calib_payload:
                calib_payload = dict(calib_payload)
                calib_payload["R_squared"] = float(r_squared_value)

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
                hovermode="x unified",
            )

            return (
                fig,
                calib_payload,
                f"{slope_value:.6g}",
                f"{intercept_value:.6g}",
                f"{float(r_squared_value):.6g}",
            )

        @callback(
            Output(ids.preview_div, "children"),
            Input(ids.apply_btn, "n_clicks"),
            State(ids.calibration_store, "data"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_calibration(
            n_clicks: int,
            calib_payload: Optional[dict],
            bead_file_path: Optional[str],
            detector_column: Optional[str],
        ):
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
