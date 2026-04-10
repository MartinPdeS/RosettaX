# -*- coding: utf-8 -*-
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.casting import _as_float
from RosettaX.utils.plottings import _make_info_figure


@dataclass
class CalibrationResult:
    """
    Container for all Dash outputs of the calibration callback.

    This lets the callback return a single object instead of manually building a long tuple
    matching the Dash Output order.
    """

    figure_store: Any = dash.no_update
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
            (figure_store, calibration_store, slope_out, intercept_out, r_squared_out, apply_status)
        """
        return (
            self.figure_store,
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

    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        """
        Build the Dash layout for the calibration section.

        Returns
        -------
        dbc.Card
            A card containing bead specification editing, calibration action, plot, and fit outputs.
        """
        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the card header.

        Returns
        -------
        dbc.CardHeader
            Header for the calibration section.
        """
        return dbc.CardHeader("4. Calibration")

    def _build_collapse(self) -> dbc.Collapse:
        """
        Build the collapsible container for the calibration section.

        Returns
        -------
        dbc.Collapse
            Collapse wrapping the calibration card body.
        """
        return dbc.Collapse(
            self._build_body(),
            id=f"collapse-{self.page.ids.page_name}-calibration",
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the main card body.

        Returns
        -------
        dbc.CardBody
            Card body containing all calibration controls and outputs.
        """
        return dbc.CardBody(
            [
                self._build_graph_store(),
                self._build_bead_specifications_block(),
                dash.html.Br(),
                self._build_actions_block(),
                dash.html.Hr(),
                self._build_graph_block(),
                dash.html.Br(),
                self._build_fit_outputs_block(),
                dash.html.Br(),
                self._build_status_block(),
            ]
        )

    def _build_graph_store(self) -> dash.dcc.Store:
        """
        Build the store holding the calibration figure.

        Returns
        -------
        dash.dcc.Store
            Store containing the calibration figure as a Plotly dict.
        """
        return dash.dcc.Store(id=self.page.ids.Calibration.graph_store)

    def _build_bead_specifications_block(self) -> dash.html.Div:
        """
        Build the bead specification editor block.

        Returns
        -------
        dash.html.Div
            Container with title, bead table, and add row button.
        """
        return dash.html.Div(
            [
                dash.html.H5("Bead specifications"),
                self._build_bead_table(),
                self._build_add_row_button_row(),
            ]
        )

    def _build_bead_table(self) -> dash.dash_table.DataTable:
        """
        Build the editable bead specification table.

        Returns
        -------
        dash.dash_table.DataTable
            Editable bead table.
        """
        runtime_config = RuntimeConfig()

        return dash.dash_table.DataTable(
            id=self.page.ids.Calibration.bead_table,
            columns=self.bead_table_columns,
            data=self._build_bead_rows_from_mesf_values(runtime_config.mesf_values),
            editable=True,
            row_deletable=True,
            style_table={"overflowX": "auto"},
        )

    def _build_add_row_button_row(self) -> dash.html.Div:
        """
        Build the add row button row.

        Returns
        -------
        dash.html.Div
            Container holding the add row button.
        """
        return dash.html.Div(
            [
                dash.html.Button(
                    "Add Row",
                    id=self.page.ids.Calibration.add_row_btn,
                    n_clicks=0,
                )
            ],
            style={"marginTop": "10px"},
        )

    def _build_actions_block(self) -> dash.html.Div:
        """
        Build the action button block.

        Returns
        -------
        dash.html.Div
            Container holding the calibration action button.
        """
        return dash.html.Div(
            [
                self._build_calibrate_button(),
            ]
        )

    def _build_calibrate_button(self) -> dash.html.Button:
        """
        Build the calibration button.

        Returns
        -------
        dash.html.Button
            Button used to trigger calibration.
        """
        return dash.html.Button(
            "Create Calibration",
            id=self.page.ids.Calibration.calibrate_btn,
            n_clicks=0,
        )

    def _build_graph_block(self) -> dash.html.Div:
        """
        Build the graph related block.

        Returns
        -------
        dash.html.Div
            Container holding graph toggle and graph container.
        """
        return dash.html.Div(
            [
                self._build_graph_toggle_switch(),
                dash.html.Br(),
                self._build_graph_container(),
            ]
        )

    def _build_graph_toggle_switch(self) -> dash.html.Div:
        """
        Build the local switch controlling whether the calibration plot is shown.

        Returns
        -------
        dash.html.Div
            Container holding the graph toggle switch.
        """
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Calibration.graph_toggle_switch,
                    options=[{"label": "Show calibration plot", "value": "enabled"}],
                    value=[],
                    switch=True,
                ),
            ],
            style={"marginTop": "10px"},
        )

    def _build_graph_container(self) -> dash.html.Div:
        """
        Build the container holding the calibration graph.

        Returns
        -------
        dash.html.Div
            Container with loading wrapper and graph.
        """
        return dash.html.Div(
            [
                dash.dcc.Loading(
                    dash.dcc.Graph(
                        id=self.page.ids.Calibration.graph_calibration,
                        style=self.page.style["graph"],
                    ),
                    type="default",
                ),
            ],
            id=self.page.ids.Calibration.graph_toggle_container,
            style={"display": "none"},
        )

    def _build_fit_outputs_block(self) -> dash.html.Div:
        """
        Build the block displaying fitted calibration parameters.

        Returns
        -------
        dash.html.Div
            Container holding slope, intercept, and R² outputs.
        """
        return dash.html.Div(
            [
                self._build_output_row("Slope:", self.page.ids.Calibration.slope_out),
                self._build_output_row("Intercept:", self.page.ids.Calibration.intercept_out),
                self._build_output_row("R²:", self.page.ids.Calibration.r_squared_out),
            ]
        )

    def _build_output_row(self, label: str, output_id: str) -> dash.html.Div:
        """
        Build a labeled output row.

        Parameters
        ----------
        label : str
            Label shown at the left of the row.
        output_id : str
            Dash id of the output value container.

        Returns
        -------
        dash.html.Div
            Row containing label and output value.
        """
        return dash.html.Div(
            [
                dash.html.Div(label),
                dash.html.Div("", id=output_id),
            ],
            style={"display": "flex", "gap": "8px"},
        )

    def _build_status_block(self) -> dash.html.Div:
        """
        Build the status message block.

        Returns
        -------
        dash.html.Div
            Status output container.
        """
        return dash.html.Div(
            id=self.page.ids.Calibration.apply_status,
            style={"marginTop": "8px"},
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
            intensity_calibrated_units = _as_float(row.get("col1"))
            intensity_au = _as_float(row.get("col2"))
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
    def _is_graph_enabled(graph_toggle_value: Any) -> bool:
        """
        Return whether the calibration plot switch is enabled.

        Parameters
        ----------
        graph_toggle_value : Any
            Checklist value.

        Returns
        -------
        bool
            True when the graph toggle contains "enabled".
        """
        return isinstance(graph_toggle_value, list) and ("enabled" in graph_toggle_value)

    def _build_calibration_figure(
        self,
        *,
        x_log10: np.ndarray,
        y_log10: np.ndarray,
        slope: float,
        intercept: float,
    ) -> go.Figure:
        """
        Build the calibration figure.

        Parameters
        ----------
        x_log10 : np.ndarray
            Log10 transformed x values.
        y_log10 : np.ndarray
            Log10 transformed y values.
        slope : float
            Fitted slope.
        intercept : float
            Fitted intercept.

        Returns
        -------
        go.Figure
            Plotly figure containing calibration points and fit line.
        """
        x_log10_fit = np.linspace(float(np.min(x_log10)), float(np.max(x_log10)), 200)
        y_log10_fit = slope * x_log10_fit + intercept

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=x_log10, y=y_log10, mode="markers", name="beads"))
        figure.add_trace(go.Scatter(x=x_log10_fit, y=y_log10_fit, mode="lines", name="fit"))
        figure.update_layout(
            xaxis_title="log10(Intensity [a.u.])",
            yaxis_title="log10(Intensity [calibrated units])",
            separators=".,",
            hovermode="closest",
        )
        return figure

    def _register_callbacks(self) -> None:
        """
        Register callbacks for the calibration section.
        """
        runtime_config = RuntimeConfig()

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_bead_table_from_runtime_store(runtime_config_data: Any) -> list[dict]:
            runtime_config = RuntimeConfig()

            if not isinstance(runtime_config_data, dict):
                return self._build_bead_rows_from_mesf_values(runtime_config.mesf_values)

            mesf_values = runtime_config_data.get("mesf_values", runtime_config.mesf_values)
            return self._build_bead_rows_from_mesf_values(mesf_values)

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_toggle_container, "style"),
            dash.Input(self.page.ids.Calibration.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_calibration_graph_container(graph_toggle_value: Any) -> dict:
            graph_enabled = self._is_graph_enabled(graph_toggle_value)
            return {"display": "block"} if graph_enabled else {"display": "none"}

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_calibration, "figure"),
            dash.Input(self.page.ids.Calibration.graph_toggle_switch, "value"),
            dash.Input(self.page.ids.Calibration.graph_store, "data"),
            prevent_initial_call=False,
        )
        def update_calibration_graph(
            graph_toggle_value: Any,
            stored_figure: Any,
        ) -> go.Figure:
            graph_enabled = self._is_graph_enabled(graph_toggle_value)

            if not graph_enabled:
                return _make_info_figure("Calibration plot is hidden.")

            if not stored_figure:
                return _make_info_figure("Create a calibration first.")

            return go.Figure(stored_figure)

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Calibration.add_row_btn, "n_clicks"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, rows: List[dict], columns: List[dict]) -> List[dict]:
            """
            Append a blank row to the bead DataTable.
            """
            next_rows = list(rows or [])
            next_rows.append({column["id"]: "" for column in columns})
            return next_rows

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_store, "data"),
            dash.Output(self.page.ids.Calibration.calibration_store, "data"),
            dash.Output(self.page.ids.Calibration.slope_out, "children"),
            dash.Output(self.page.ids.Calibration.intercept_out, "children"),
            dash.Output(self.page.ids.Calibration.r_squared_out, "children"),
            dash.Output(self.page.ids.Calibration.apply_status, "children"),
            dash.Input(self.page.ids.Calibration.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def calibrate_and_apply(
            n_clicks: int,
            bead_file_path: Optional[str],
            table_data: Optional[list[dict]],
            detector_column: Optional[str],
        ) -> tuple:
            """
            Fit a log10 regression from bead table points and optionally apply it.
            """
            figure = go.Figure()

            try:
                if not bead_file_path:
                    figure = _make_info_figure("Upload a bead file first.")
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        slope_out="",
                        intercept_out="",
                        r_squared_out="",
                        apply_status="Missing bead file.",
                    ).to_tuple()

                intensity_calibrated_units, intensity_au = self._extract_xy_from_table(table_data or [])
                if intensity_calibrated_units.size < 2:
                    figure = _make_info_figure("Need at least 2 bead points to calibrate.")
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        slope_out="",
                        intercept_out="",
                        r_squared_out="",
                        apply_status="Need at least 2 valid bead rows.",
                    ).to_tuple()

                intensity_calibrated_units = np.asarray(intensity_calibrated_units, dtype=float)
                intensity_au = np.asarray(intensity_au, dtype=float)

                finite_mask = np.isfinite(intensity_au) & np.isfinite(intensity_calibrated_units)
                intensity_au = intensity_au[finite_mask]
                intensity_calibrated_units = intensity_calibrated_units[finite_mask]

                positive_mask = (intensity_au > 0.0) & (intensity_calibrated_units > 0.0)
                intensity_au = intensity_au[positive_mask]
                intensity_calibrated_units = intensity_calibrated_units[positive_mask]

                if intensity_au.size < 2:
                    figure = _make_info_figure("Need at least 2 positive finite points for log10 fit.")
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        slope_out="",
                        intercept_out="",
                        r_squared_out="",
                        apply_status="Need at least 2 positive finite bead points for log10 fit.",
                    ).to_tuple()

                intensity_au_log10 = np.log10(intensity_au)
                intensity_calibrated_units_log10 = np.log10(intensity_calibrated_units)

                slope, intercept = np.polyfit(
                    intensity_au_log10,
                    intensity_calibrated_units_log10,
                    1,
                )

                intensity_calibrated_units_log10_predicted = (
                    slope * intensity_au_log10 + intercept
                )
                r_squared = self._compute_r_squared(
                    y_true=intensity_calibrated_units_log10,
                    y_pred=intensity_calibrated_units_log10_predicted,
                )
                prefactor = 10.0 ** float(intercept)

                calibration_payload = {
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "prefactor": float(prefactor),
                    "R_squared": float(r_squared),
                    "model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
                    "x_definition": "Intensity [a.u.]",
                    "y_definition": "Intensity [calibrated units]",
                }

                figure = self._build_calibration_figure(
                    x_log10=intensity_au_log10,
                    y_log10=intensity_calibrated_units_log10,
                    slope=float(slope),
                    intercept=float(intercept),
                )

                if not detector_column:
                    apply_status = "Calibration fit OK. Select a fluorescence detector to apply."
                else:
                    with FCSFile(str(bead_file_path), writable=False) as fcs_file:
                        raw_intensity_au = fcs_file.column_copy(str(detector_column), dtype=float)

                    raw_intensity_au = np.asarray(raw_intensity_au, dtype=float)
                    raw_intensity_au = raw_intensity_au[np.isfinite(raw_intensity_au)]
                    raw_intensity_au = raw_intensity_au[raw_intensity_au > 0.0]

                    calibrated_intensity_units = prefactor * (raw_intensity_au ** float(slope))
                    calibrated_intensity_units = calibrated_intensity_units[np.isfinite(calibrated_intensity_units)]
                    calibrated_intensity_units = calibrated_intensity_units[calibrated_intensity_units > 0.0]

                    apply_status = (
                        f"Applied to {calibrated_intensity_units.size} events using detector '{detector_column}'."
                    )

                return CalibrationResult(
                    figure_store=figure.to_dict(),
                    calibration_store=calibration_payload,
                    slope_out=f"{float(slope):.6g}",
                    intercept_out=f"{float(intercept):.6g} (A={float(prefactor):.6g})",
                    r_squared_out=f"{float(r_squared):.6g}",
                    apply_status=apply_status,
                ).to_tuple()

            except Exception as exc:
                figure = _make_info_figure("Calibration failed.")
                return CalibrationResult(
                    figure_store=figure.to_dict(),
                    calibration_store=dash.no_update,
                    slope_out="",
                    intercept_out="",
                    r_squared_out="",
                    apply_status=f"{type(exc).__name__}: {exc}",
                ).to_tuple()

    @classmethod
    def _build_bead_rows_from_mesf_values(cls, mesf_values: Any) -> list[dict]:
        if mesf_values is None:
            return [{"col1": "", "col2": ""} for _ in range(3)]

        if isinstance(mesf_values, str):
            raw_parts = [part.strip() for part in mesf_values.split(",")]
        elif isinstance(mesf_values, (list, tuple)):
            raw_parts = [str(part).strip() for part in mesf_values]
        else:
            raw_parts = [str(mesf_values).strip()]

        parsed_values: list[str] = []
        for raw_part in raw_parts:
            if not raw_part:
                continue
            parsed_value = _as_float(raw_part)
            if parsed_value is None:
                continue
            parsed_values.append(f"{float(parsed_value):.6g}")

        if not parsed_values:
            return [{"col1": "", "col2": ""} for _ in range(3)]

        return [{"col1": value, "col2": ""} for value in parsed_values]