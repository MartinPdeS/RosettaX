# -*- coding: utf-8 -*-
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.casting import _as_float
from RosettaX.utils.plottings import _make_info_figure
from RosettaX.utils import styling


logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    """
    Container for all Dash outputs of the calibration callback.
    """

    figure_store: Any = dash.no_update
    calibration_store: Any = dash.no_update
    slope_out: str = ""
    intercept_out: str = ""
    r_squared_out: str = ""
    apply_status: str = ""

    def to_tuple(self) -> tuple:
        return (
            self.figure_store,
            self.calibration_store,
            self.slope_out,
            self.intercept_out,
            self.r_squared_out,
            self.apply_status,
        )


class Calibration:
    bead_table_columns = [
        {"name": "Intensity [calibrated units]", "id": "col1", "editable": True},
        {"name": "Intensity [a.u.]", "id": "col2", "editable": True},
    ]

    default_bead_rows = [{"col1": "", "col2": ""} for _ in range(3)]

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized CalibrationSection with page=%r", page)

    def _get_runtime_config(self) -> RuntimeConfig:
        return RuntimeConfig()

    def _get_default_mesf_values(self) -> Any:
        runtime_config = self._get_runtime_config()
        return runtime_config.get_path("calibration.mesf_values", default=[])

    def get_layout(self) -> dbc.Card:
        logger.debug("Building calibration section layout.")
        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("4. Calibration")

    def _build_collapse(self) -> dbc.Collapse:
        return dbc.Collapse(
            self._build_body(),
            id=f"collapse-{self.page.ids.page_name}-calibration",
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
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
        return dash.dcc.Store(id=self.page.ids.Calibration.graph_store)

    def _build_bead_specifications_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H5("Bead specifications"),
                self._build_bead_table(),
                self._build_add_row_button_row(),
            ]
        )

    def _build_bead_table(self) -> dash.dash_table.DataTable:
        default_mesf_values = self._get_default_mesf_values()
        bead_rows = self._build_bead_rows_from_mesf_values(default_mesf_values)

        logger.debug(
            "Building bead table with default_mesf_values=%r resulting rows=%r",
            default_mesf_values,
            bead_rows,
        )

        return dash.dash_table.DataTable(
            id=self.page.ids.Calibration.bead_table,
            columns=self.bead_table_columns,
            data=bead_rows,
            **styling.DATATABLE,
        )

    def _build_add_row_button_row(self) -> dash.html.Div:
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
        return dash.html.Div(
            [
                self._build_calibrate_button(),
            ]
        )

    def _build_calibrate_button(self) -> dash.html.Button:
        return dash.html.Button(
            "Create Calibration",
            id=self.page.ids.Calibration.calibrate_btn,
            n_clicks=0,
        )

    def _build_graph_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_graph_container(),
            ]
        )

    def _build_graph_container(self) -> dash.html.Div:
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
            style={"display": "block"},
        )

    def _build_fit_outputs_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_output_row("Slope:", self.page.ids.Calibration.slope_out),
                self._build_output_row("Intercept:", self.page.ids.Calibration.intercept_out),
                self._build_output_row("R²:", self.page.ids.Calibration.r_squared_out),
            ]
        )

    def _build_output_row(self, label: str, output_id: str) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(label),
                dash.html.Div("", id=output_id),
            ],
            style={"display": "flex", "gap": "8px"},
        )

    def _build_status_block(self) -> dash.html.Div:
        return dash.html.Div(
            id=self.page.ids.Calibration.apply_status,
            style={"marginTop": "8px"},
        )

    def _extract_xy_from_table(self, table_data: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
        logger.debug(
            "Extracting XY from bead table with row_count=%r",
            None if table_data is None else len(table_data),
        )

        intensity_calibrated_units_values: List[float] = []
        intensity_au_values: List[float] = []

        for row_index, row in enumerate(table_data or []):
            intensity_calibrated_units = _as_float(row.get("col1"))
            intensity_au = _as_float(row.get("col2"))

            logger.debug(
                "Parsed bead row index=%r raw_row=%r parsed col1=%r parsed col2=%r",
                row_index,
                row,
                intensity_calibrated_units,
                intensity_au,
            )

            if intensity_calibrated_units is None or intensity_au is None:
                continue

            intensity_calibrated_units_values.append(intensity_calibrated_units)
            intensity_au_values.append(intensity_au)

        logger.debug(
            "Extracted valid calibration points count=%r",
            len(intensity_calibrated_units_values),
        )

        return (
            np.asarray(intensity_calibrated_units_values, dtype=float),
            np.asarray(intensity_au_values, dtype=float),
        )

    @staticmethod
    def _compute_r_squared(*, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        finite_mask = np.isfinite(y_true) & np.isfinite(y_pred)
        y_true = y_true[finite_mask]
        y_pred = y_pred[finite_mask]

        if y_true.size < 2:
            return float("nan")

        sum_squared_residuals = float(np.sum((y_true - y_pred) ** 2))
        sum_squared_total = float(np.sum((y_true - float(np.mean(y_true))) ** 2))

        if sum_squared_total <= 0.0:
            return float("nan")

        return 1.0 - sum_squared_residuals / sum_squared_total

    def _build_calibration_figure(
        self,
        *,
        x_log10: np.ndarray,
        y_log10: np.ndarray,
        slope: float,
        intercept: float,
    ) -> go.Figure:
        logger.debug(
            "Building calibration figure with point_count=%r slope=%r intercept=%r",
            len(x_log10),
            slope,
            intercept,
        )

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

    def register_callbacks(self) -> None:
        logger.debug("Registering calibration callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_bead_table_from_runtime_store(runtime_config_data: Any) -> list[dict]:
            logger.debug(
                "sync_bead_table_from_runtime_store called with runtime_config_data=%r",
                runtime_config_data,
            )

            if not isinstance(runtime_config_data, dict):
                default_mesf_values = self._get_default_mesf_values()
                resolved_rows = self._build_bead_rows_from_mesf_values(default_mesf_values)

                logger.debug(
                    "Runtime config data is not a dict. Returning default rows=%r",
                    resolved_rows,
                )
                return resolved_rows

            calibration_section = runtime_config_data.get("calibration") or {}
            mesf_values = calibration_section.get("mesf_values", [])
            resolved_rows = self._build_bead_rows_from_mesf_values(mesf_values)

            logger.debug(
                "Resolved bead rows from runtime store mesf_values=%r rows=%r",
                mesf_values,
                resolved_rows,
            )
            return resolved_rows

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_calibration, "figure"),
            dash.Input(self.page.ids.Calibration.graph_store, "data"),
            prevent_initial_call=False,
        )
        def update_calibration_graph(stored_figure: Any) -> go.Figure:
            logger.debug(
                "update_calibration_graph called with stored_figure_type=%s",
                type(stored_figure).__name__,
            )

            if not stored_figure:
                logger.debug("No stored calibration figure available. Returning info figure.")
                return _make_info_figure("Create a calibration first.")

            try:
                figure = go.Figure(stored_figure)
            except Exception:
                logger.exception(
                    "Failed to reconstruct calibration figure from stored_figure=%r",
                    stored_figure,
                )
                raise

            logger.debug("Calibration graph reconstructed successfully from store.")
            return figure

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Calibration.add_row_btn, "n_clicks"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, rows: List[dict], columns: List[dict]) -> List[dict]:
            logger.debug(
                "add_row called with n_clicks=%r existing_row_count=%r columns=%r",
                n_clicks,
                None if rows is None else len(rows),
                columns,
            )

            next_rows = list(rows or [])
            next_rows.append({column["id"]: "" for column in columns})

            logger.debug("add_row returning next_row_count=%r", len(next_rows))
            return next_rows

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_store, "data"),
            dash.Output(self.page.ids.Calibration.calibration_store, "data"),
            dash.Output(self.page.ids.Calibration.slope_out, "children"),
            dash.Output(self.page.ids.Calibration.intercept_out, "children"),
            dash.Output(self.page.ids.Calibration.r_squared_out, "children"),
            dash.Output(self.page.ids.Calibration.apply_status, "children"),
            dash.Input(self.page.ids.Calibration.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.page.ids.Scattering.threshold_store, "data"),
            prevent_initial_call=True,
        )
        def calibrate_and_apply(
            n_clicks: int,
            bead_file_path: Optional[str],
            table_data: Optional[list[dict]],
            detector_column: Optional[str],
            scattering_detector_column: Optional[str],
            scattering_threshold: Any,
        ) -> tuple:
            logger.debug(
                "calibrate_and_apply called with n_clicks=%r bead_file_path=%r table_row_count=%r detector_column=%r",
                n_clicks,
                bead_file_path,
                None if table_data is None else len(table_data),
                detector_column,
            )

            del n_clicks

            figure = go.Figure()

            try:
                if not bead_file_path:
                    logger.debug("Calibration aborted because bead_file_path is missing.")
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
                logger.debug(
                    "Initial extracted calibration arrays sizes: calibrated=%r au=%r",
                    intensity_calibrated_units.size,
                    intensity_au.size,
                )

                if intensity_calibrated_units.size < 2:
                    logger.debug("Calibration aborted because fewer than 2 valid bead points were extracted.")
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
                logger.debug(
                    "Finite mask kept %r / %r points",
                    int(np.count_nonzero(finite_mask)),
                    int(finite_mask.size),
                )

                intensity_au = intensity_au[finite_mask]
                intensity_calibrated_units = intensity_calibrated_units[finite_mask]

                positive_mask = (intensity_au > 0.0) & (intensity_calibrated_units > 0.0)
                logger.debug(
                    "Positive mask kept %r / %r points",
                    int(np.count_nonzero(positive_mask)),
                    int(positive_mask.size),
                )

                intensity_au = intensity_au[positive_mask]
                intensity_calibrated_units = intensity_calibrated_units[positive_mask]

                if intensity_au.size < 2:
                    logger.debug("Calibration aborted because fewer than 2 positive finite points remained.")
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

                logger.debug(
                    "Performing polyfit on %r log10 points. x range=[%r, %r] y range=[%r, %r]",
                    intensity_au_log10.size,
                    float(np.min(intensity_au_log10)),
                    float(np.max(intensity_au_log10)),
                    float(np.min(intensity_calibrated_units_log10)),
                    float(np.max(intensity_calibrated_units_log10)),
                )

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

                logger.debug(
                    "Calibration fit succeeded with slope=%r intercept=%r prefactor=%r r_squared=%r",
                    float(slope),
                    float(intercept),
                    float(prefactor),
                    float(r_squared),
                )

                reference_points = [
                    {
                        "reference_value": float(reference_value),
                        "measured_value": float(measured_value),
                    }
                    for reference_value, measured_value in zip(
                        intensity_calibrated_units,
                        intensity_au,
                        strict=False,
                    )
                ]

                calibration_payload = {
                    "schema_version": "1.0",
                    "calibration_type": "fluorescence",
                    "name": "",
                    "created_at": "",
                    "source_file": Path(str(bead_file_path)).name if bead_file_path else None,
                    "source_channel": str(detector_column) if detector_column else None,
                    "gating_channel": str(scattering_detector_column) if scattering_detector_column else None,
                    "gating_threshold": _as_float(scattering_threshold),
                    "fit_model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
                    "fit_metrics": {
                        "r_squared": float(r_squared),
                        "point_count": int(len(reference_points)),
                    },
                    "parameters": {
                        "slope": float(slope),
                        "intercept": float(intercept),
                        "prefactor": float(prefactor),
                    },
                    "reference_points": reference_points,
                    "export_notes": "",
                    "payload": {
                        "slope": float(slope),
                        "intercept": float(intercept),
                        "prefactor": float(prefactor),
                        "R_squared": float(r_squared),
                        "model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
                        "x_definition": "Intensity [a.u.]",
                        "y_definition": "Intensity [calibrated units]",
                    },
                }

                figure = self._build_calibration_figure(
                    x_log10=intensity_au_log10,
                    y_log10=intensity_calibrated_units_log10,
                    slope=float(slope),
                    intercept=float(intercept),
                )

                if not detector_column:
                    apply_status = "Calibration fit created successfully."
                    logger.debug(
                        "No fluorescence detector selected. Returning calibration fit without detector preview."
                    )
                else:
                    logger.debug(
                        "Computing calibration preview for detector_column=%r using bead_file_path=%r",
                        detector_column,
                        bead_file_path,
                    )

                    with FCSFile(str(bead_file_path), writable=False) as fcs_file:
                        raw_intensity_au = fcs_file.column_copy(str(detector_column), dtype=float)

                    raw_intensity_au = np.asarray(raw_intensity_au, dtype=float)
                    raw_intensity_au = raw_intensity_au[np.isfinite(raw_intensity_au)]
                    raw_intensity_au = raw_intensity_au[raw_intensity_au > 0.0]

                    calibrated_intensity_units = prefactor * (raw_intensity_au ** float(slope))
                    calibrated_intensity_units = calibrated_intensity_units[np.isfinite(calibrated_intensity_units)]
                    calibrated_intensity_units = calibrated_intensity_units[calibrated_intensity_units > 0.0]

                    logger.debug(
                        "Computed calibration preview for detector=%r valid_event_count=%r",
                        detector_column,
                        calibrated_intensity_units.size,
                    )

                    apply_status = (
                        f"Calibration fit created successfully. "
                        f"Preview computed for {calibrated_intensity_units.size} valid events on detector '{detector_column}'."
                    )

                result = CalibrationResult(
                    figure_store=figure.to_dict(),
                    calibration_store=calibration_payload,
                    slope_out=f"{float(slope):.6g}",
                    intercept_out=f"{float(intercept):.6g} (A={float(prefactor):.6g})",
                    r_squared_out=f"{float(r_squared):.6g}",
                    apply_status=apply_status,
                )

                logger.debug(
                    "calibrate_and_apply returning success with apply_status=%r calibration_payload=%r",
                    apply_status,
                    calibration_payload,
                )
                return result.to_tuple()

            except Exception as exc:
                logger.exception(
                    "Calibration failed for bead_file_path=%r detector_column=%r table_data=%r",
                    bead_file_path,
                    detector_column,
                    table_data,
                )
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
        logger.debug("_build_bead_rows_from_mesf_values called with mesf_values=%r", mesf_values)

        if mesf_values is None:
            default_rows = [{"col1": "", "col2": ""} for _ in range(3)]
            logger.debug("mesf_values is None. Returning default rows=%r", default_rows)
            return default_rows

        if isinstance(mesf_values, str):
            raw_parts = [part.strip() for part in mesf_values.split(",")]
        elif isinstance(mesf_values, (list, tuple)):
            raw_parts = [str(part).strip() for part in mesf_values]
        else:
            raw_parts = [str(mesf_values).strip()]

        logger.debug("Parsed raw MESF parts=%r", raw_parts)

        parsed_values: list[str] = []
        for raw_part in raw_parts:
            if not raw_part:
                continue

            parsed_value = _as_float(raw_part)
            if parsed_value is None:
                logger.debug(
                    "Skipping MESF part=%r because it could not be parsed to float.",
                    raw_part,
                )
                continue

            parsed_values.append(f"{float(parsed_value):.6g}")

        logger.debug("Parsed MESF values=%r", parsed_values)

        if not parsed_values:
            default_rows = [{"col1": "", "col2": ""} for _ in range(3)]
            logger.debug("No valid MESF values remained. Returning default rows=%r", default_rows)
            return default_rows

        rows = [{"col1": value, "col2": ""} for value in parsed_values]
        logger.debug("Returning MESF bead rows=%r", rows)
        return rows