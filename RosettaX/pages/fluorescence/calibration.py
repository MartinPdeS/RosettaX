# -*- coding: utf-8 -*-
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.utils.reader import FCSFile
from RosettaX.pages.runtime_config import get_runtime_config

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
    bead_table_columns = [
        {"name": "Intensity [calibrated units]", "id": "col1", "editable": True},
        {"name": "Intensity [a.u.]", "id": "col2", "editable": True},
    ]
    default_bead_rows = [{"col1": "", "col2": ""} for _ in range(3)]

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
                            dash.html.Button("Create Calibration", id=self.ids.Calibration.calibrate_btn, n_clicks=0),
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
        Extract calibration points from the bead DataTable.

        Parameters
        ----------
        table_data : List[dict]
            Rows from the Dash DataTable.
            Expected keys are:
            - "col1": Intensity [calibrated units]
            - "col2": Intensity [a.u.]

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (intensity_calibrated_units, intensity_au) as float arrays, excluding rows that cannot be parsed.
        """
        intensity_calibrated_units_values: List[float] = []
        intensity_au_values: List[float] = []

        for row in table_data or []:
            intensity_calibrated_units = self._as_float(row.get("col1"))
            intensity_au = self._as_float(row.get("col2"))
            if intensity_calibrated_units is None or intensity_au is None:
                continue
            intensity_calibrated_units_values.append(intensity_calibrated_units)
            intensity_au_values.append(intensity_au)

        return (
            np.asarray(intensity_calibrated_units_values, dtype=float),
            np.asarray(intensity_au_values, dtype=float),
        )

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
        - Fitting a calibration curve from bead points and optionally applying it to the selected detector.

        Regression model
        ---------------
        The regression is performed in log10 space:

            log10(y) = slope * log10(x) + intercept

        where:
            x = Intensity [a.u.]
            y = Intensity [calibrated units]

        Plot behavior
        -------------
        The plot uses linear Plotly axes, but it displays log10 transformed data. This makes the
        regression appear as a straight line without using Plotly log axis types.

        Applying calibration
        -------------------
        When applying to event data, the mapping is evaluated in linear space:

            y = 10**intercept * x**slope

        This guarantees positive calibrated values for positive x.
        """
        runtime_config = get_runtime_config()
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
            Fit a log10 space regression from bead table points and optionally apply it.

            Bead table columns:
            - col1: Intensity [calibrated units]
            - col2: Intensity [a.u.]

            The fit is done on log10 transformed data and the plot shows log10 transformed axes
            values on standard linear Plotly axes.

            Returns
            -------
            tuple
                Dash outputs in the declared Output order.
            """
            fig = go.Figure()

            try:
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

                intensity_calibrated_units, intensity_au = self._extract_xy_from_table(table_data or [])
                if intensity_calibrated_units.size < 2:
                    fig.update_layout(title="Need at least 2 bead points to calibrate.")
                    return CalibrationResult(
                        figure=fig,
                        calibration_store=dash.no_update,
                        slope_out="",
                        intercept_out="",
                        r_squared_out="",
                        apply_status="Need at least 2 valid bead rows.",
                    ).to_tuple()

                y = np.asarray(intensity_calibrated_units, dtype=float)
                x = np.asarray(intensity_au, dtype=float)

                finite_mask = np.isfinite(x) & np.isfinite(y)
                x = x[finite_mask]
                y = y[finite_mask]

                positive_mask = (x > 0.0) & (y > 0.0)
                x = x[positive_mask]
                y = y[positive_mask]

                if x.size < 2:
                    fig.update_layout(title="Need at least 2 positive finite points for log10 fit.")
                    return CalibrationResult(
                        figure=fig,
                        calibration_store=dash.no_update,
                        slope_out="",
                        intercept_out="",
                        r_squared_out="",
                        apply_status="Need at least 2 positive finite bead points for log10 fit.",
                    ).to_tuple()

                x_log10 = np.log10(x)
                y_log10 = np.log10(y)

                slope, intercept = np.polyfit(x_log10, y_log10, 1)

                y_log10_pred = slope * x_log10 + intercept
                r2 = self._compute_r_squared(y_true=y_log10, y_pred=y_log10_pred)

                prefactor = 10.0 ** float(intercept)

                calib_payload = {
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "prefactor": float(prefactor),
                    "R_squared": float(r2),
                    "model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
                    "x_definition": "Intensity [a.u.]",
                    "y_definition": "Intensity [calibrated units]",
                }

                x_log10_fit = np.linspace(float(np.min(x_log10)), float(np.max(x_log10)), 200)
                y_log10_fit = slope * x_log10_fit + intercept

                fig.add_trace(go.Scatter(x=x_log10, y=y_log10, mode="markers", name="beads"))
                fig.add_trace(go.Scatter(x=x_log10_fit, y=y_log10_fit, mode="lines", name="fit"))
                fig.update_layout(
                    xaxis_title="log10(Intensity [a.u.])",
                    yaxis_title="log10(Intensity [calibrated units])",
                    separators=".,",
                    hovermode="closest",
                )

                if not detector_column:
                    apply_msg = "Calibration fit OK. Select a fluorescence detector to apply."
                else:
                    with FCSFile(str(bead_file_path), writable=False) as fcs:
                        raw_intensity_au = fcs.column_copy(str(detector_column), dtype=float)

                    raw_intensity_au = np.asarray(raw_intensity_au, dtype=float)
                    raw_intensity_au = raw_intensity_au[np.isfinite(raw_intensity_au)]
                    raw_intensity_au = raw_intensity_au[raw_intensity_au > 0.0]

                    calibrated_intensity_units = prefactor * (raw_intensity_au ** float(slope))
                    calibrated_intensity_units = calibrated_intensity_units[np.isfinite(calibrated_intensity_units)]
                    calibrated_intensity_units = calibrated_intensity_units[calibrated_intensity_units > 0.0]

                    apply_msg = f"Applied to {calibrated_intensity_units.size} events using detector '{detector_column}'." if runtime_config.debug else ""

                return CalibrationResult(
                    figure=fig,
                    calibration_store=calib_payload,
                    slope_out=f"{float(slope):.6g}",
                    intercept_out=f"{float(intercept):.6g} (A={float(prefactor):.6g})",
                    r_squared_out=f"{float(r2):.6g}",
                    apply_status=apply_msg,
                ).to_tuple()

            except Exception as exc:
                fig.update_layout(title="Calibration failed due to an exception.")
                return CalibrationResult(
                    figure=fig,
                    calibration_store=dash.no_update,
                    slope_out="",
                    intercept_out="",
                    r_squared_out="",
                    apply_status=f"{type(exc).__name__}: {exc}",
                ).to_tuple()