# -*- coding: utf-8 -*-
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.utils.reader import FCSFile


@dataclass(frozen=True)
class CalibrationResult:
    """
    Container for all Dash outputs of the calibration callback.

    This lets the callback return a single object instead of manually building a long tuple
    matching the Dash Output order.
    """

    figure: Any = dash.no_update
    calibration_store: Any = dash.no_update
    slope_out: str = ""
    intercept_out: str = ""
    r_squared_out: str = ""
    apply_status: str = ""

    def to_tuple(self) -> tuple:
        """
        Converts this result to the tuple expected by Dash multi output callbacks.

        Returns
        -------
        tuple
            Outputs in the exact order declared in the Dash callback:
            (figure, calibration_store, slope_out, intercept_out, r_squared_out, apply_status)
        """
        return (
            self.figure,
            self.calibration_store,
            self.slope_out,
            self.intercept_out,
            self.r_squared_out,
            self.apply_status,
        )


class CalibrationSection:
    def _calibration_get_layout(self) -> dbc.Card:
        """
        Build the Dash layout for the calibration section.

        Returns
        -------
        dbc.Card
            A card containing bead specification editing, calibration action, plot, and fit outputs.
        """
        return dbc.Card(
            [
                dbc.CardHeader("4. Calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            dash.html.H5("Bead specifications"),
                            dash.dash_table.DataTable(
                                id=self.ids.Calibration.bead_table,
                                columns=self.bead_table_columns,
                                data=self.default_bead_rows,
                                editable=True,
                                row_deletable=True,
                                style_table={"overflowX": "auto"},
                            ),
                            dash.html.Div(
                                [dash.html.Button("Add Row", id=self.ids.Calibration.add_row_btn, n_clicks=0)],
                                style={"marginTop": "10px"},
                            ),
                            dash.html.Br(),
                            dash.html.Button("Calibrate (fit + apply)", id=self.ids.Calibration.calibrate_btn, n_clicks=0),
                            dash.html.Hr(),
                            dash.dcc.Loading(
                                dash.dcc.Graph(id=self.ids.Calibration.graph_calibration, style=self.graph_style),
                                type="default",
                            ),
                            dash.html.Br(),
                            dash.html.Div(
                                [
                                    dash.html.Div(
                                        [dash.html.Div("Slope:"), dash.html.Div("", id=self.ids.Calibration.slope_out)],
                                        style={"display": "flex", "gap": "8px"},
                                    ),
                                    dash.html.Div(
                                        [dash.html.Div("Intercept:"), dash.html.Div("", id=self.ids.Calibration.intercept_out)],
                                        style={"display": "flex", "gap": "8px"},
                                    ),
                                    dash.html.Div(
                                        [dash.html.Div("R²:"), dash.html.Div("", id=self.ids.Calibration.r_squared_out)],
                                        style={"display": "flex", "gap": "8px"},
                                    ),
                                ]
                            ),
                            dash.html.Br(),
                            dash.html.Div(id=self.ids.Calibration.apply_status, style={"marginTop": "8px"}),
                        ],
                    ),
                    id=f"collapse-{self.ids.page_name}-calibration",
                    is_open=True,
                ),
            ]
        )

    def _extract_xy_from_table(self, table_data: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract MESF and intensity values from the bead DataTable.

        Parameters
        ----------
        table_data : List[dict]
            Rows from the Dash DataTable. Expected keys are "col1" for MESF and "col2" for intensity.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (mesf, intensity) as float arrays, excluding rows that cannot be parsed.
        """
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
    def _compute_r_squared(*, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Compute the coefficient of determination R squared.

        Parameters
        ----------
        y_true : np.ndarray
            Ground truth values.
        y_pred : np.ndarray
            Predicted values.

        Returns
        -------
        float
            R squared, or NaN if it cannot be computed.
        """
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

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        """
        Parse a value into a finite float.

        Parameters
        ----------
        value : Any
            Candidate value from UI components (may be str, int, float, or None).

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

    def _calibration_register_callbacks(self) -> None:
        """
        Register callbacks for the calibration section.

        This includes:
        - Adding a new editable row in the bead DataTable.
        - Fitting a linear calibration from bead points and optionally applying it to the selected detector.
        """
        @dash.callback(
            dash.Output(self.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Input(self.ids.Calibration.add_row_btn, "n_clicks"),
            dash.State(self.ids.Calibration.bead_table, "data"),
            dash.State(self.ids.Calibration.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, rows: List[dict], columns: List[dict]) -> List[dict]:
            """
            Append a blank row to the bead DataTable.

            Parameters
            ----------
            n_clicks : int
                Click count of the Add Row button.
            rows : List[dict]
                Current table rows.
            columns : List[dict]
                Column definitions used to build an empty row.

            Returns
            -------
            List[dict]
                Updated table rows with one appended blank row.
            """
            next_rows = list(rows or [])
            next_rows.append({c["id"]: "" for c in columns})
            return next_rows

        @dash.callback(
            dash.Output(self.ids.Calibration.graph_calibration, "figure"),
            dash.Output(self.ids.Calibration.calibration_store, "data"),
            dash.Output(self.ids.Calibration.slope_out, "children"),
            dash.Output(self.ids.Calibration.intercept_out, "children"),
            dash.Output(self.ids.Calibration.r_squared_out, "children"),
            dash.Output(self.ids.Calibration.apply_status, "children"),
            dash.Input(self.ids.Calibration.calibrate_btn, "n_clicks"),
            dash.State(self.ids.Load.uploaded_fcs_path_store, "data"),
            dash.State(self.ids.Calibration.bead_table, "data"),
            dash.State(self.ids.Fluorescence.detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def calibrate_and_apply(
            n_clicks: int,
            bead_file_path: Optional[str],
            table_data: Optional[list[dict]],
            detector_column: Optional[str],
        ) -> tuple:
            """
            Fit a linear calibration (MESF versus intensity) from bead table points and optionally apply it.

            Parameters
            ----------
            n_clicks : int
                Click count from the Calibrate button.
            bead_file_path : Optional[str]
                Uploaded bead FCS file path from store.
            table_data : Optional[list[dict]]
                Bead table rows.
            detector_column : Optional[str]
                Selected fluorescence detector column to apply calibration to.

            Returns
            -------
            tuple
                Dash outputs in the declared Output order.
            """
            fig = go.Figure()

            if not bead_file_path:
                fig.update_layout(title="Upload a bead file first.")
                return CalibrationResult(
                    figure=fig,
                    calibration_store=dash.no_update,
                    slope_out="",
                    intercept_out="",
                    r_squared_out="",
                    apply_status="Missing bead file.",
                ).to_tuple()

            mesf, intensity = self._extract_xy_from_table(table_data or [])
            if mesf.size < 2:
                fig.update_layout(title="Need at least 2 bead points to calibrate.")
                return CalibrationResult(
                    figure=fig,
                    calibration_store=dash.no_update,
                    apply_status="Need ≥ 2 valid bead rows.",
                ).to_tuple()

            x = np.asarray(intensity, dtype=float)
            y = np.asarray(mesf, dtype=float)

            mask = np.isfinite(x) & np.isfinite(y)
            x = x[mask]
            y = y[mask]
            if x.size < 2:
                fig.update_layout(title="Need at least 2 finite points.")
                return CalibrationResult(
                    figure=fig,
                    calibration_store=dash.no_update,
                    apply_status="Need ≥ 2 finite bead points.",
                ).to_tuple()

            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            r2 = self._compute_r_squared(y_true=y, y_pred=y_pred)

            calib_payload = {
                "slope": float(slope),
                "intercept": float(intercept),
                "R_squared": float(r2),
            }

            x_fit = np.linspace(float(np.min(x)), float(np.max(x)), 200)
            y_fit = slope * x_fit + intercept

            fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="beads"))
            fig.add_trace(go.Scatter(x=x_fit, y=y_fit, mode="lines", name="fit"))
            fig.update_layout(
                xaxis_title="Intensity (a.u.)",
                yaxis_title="MESF",
                separators=".,",
                hovermode="x unified",
            )

            if not detector_column:
                apply_msg = "Calibration fit OK. Select a fluorescence detector to apply."
            else:
                with FCSFile(str(bead_file_path), writable=False) as fcs:
                    raw = fcs.column_copy(str(detector_column), dtype=float)

                raw = np.asarray(raw, dtype=float)
                raw = raw[np.isfinite(raw)]
                calibrated = slope * raw + intercept
                apply_msg = f"Applied to {calibrated.size} events using detector '{detector_column}'."

            return CalibrationResult(
                figure=fig,
                calibration_store=calib_payload,
                slope_out=f"{float(slope):.6g}",
                intercept_out=f"{float(intercept):.6g}",
                r_squared_out=f"{float(r2):.6g}",
                apply_status=apply_msg,
            ).to_tuple()