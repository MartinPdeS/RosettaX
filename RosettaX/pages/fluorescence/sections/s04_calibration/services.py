# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import logging

import dash
import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import _make_info_figure


DEFAULT_BEAD_ROWS = [
    {"col1": "", "col2": ""}
    for _ in range(3)
]


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


@dataclass(frozen=True)
class ExtractedCalibrationPoints:
    intensity_calibrated_units: np.ndarray
    intensity_au: np.ndarray


@dataclass(frozen=True)
class FluorescenceFitResult:
    slope: float
    intercept: float
    prefactor: float
    r_squared: float
    intensity_au_log10: np.ndarray
    intensity_calibrated_units_log10: np.ndarray


def build_default_bead_rows() -> list[dict[str, str]]:
    return [
        dict(row)
        for row in DEFAULT_BEAD_ROWS
    ]


def build_bead_rows_from_mesf_values(
    mesf_values: Any,
) -> list[dict[str, str]]:
    if mesf_values is None:
        return build_default_bead_rows()

    if isinstance(mesf_values, str):
        raw_parts = [
            part.strip()
            for part in mesf_values.split(",")
        ]
    elif isinstance(mesf_values, (list, tuple)):
        raw_parts = [
            str(part).strip()
            for part in mesf_values
        ]
    else:
        raw_parts = [
            str(mesf_values).strip()
        ]

    parsed_values: list[str] = []

    for raw_part in raw_parts:
        if not raw_part:
            continue

        parsed_value = casting.as_float(
            raw_part,
        )

        if parsed_value is None:
            continue

        parsed_values.append(
            f"{float(parsed_value):.6g}"
        )

    if not parsed_values:
        return build_default_bead_rows()

    return [
        {
            "col1": value,
            "col2": "",
        }
        for value in parsed_values
    ]


def resolve_bead_rows_from_runtime_store(
    runtime_config_data: Any,
) -> list[dict[str, str]]:
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    mesf_values = runtime_config.get_path(
        "calibration.mesf_values",
        default=[],
    )

    return build_bead_rows_from_mesf_values(
        mesf_values,
    )


def rebuild_calibration_graph(
    *,
    stored_figure: Any,
    empty_message: str,
    failure_message: str,
    logger: logging.Logger,
) -> go.Figure:
    if not stored_figure:
        logger.debug(
            "No stored figure available. Returning info figure."
        )
        return _make_info_figure(
            empty_message,
        )

    try:
        return go.Figure(
            stored_figure,
        )
    except Exception:
        logger.exception(
            "Failed to reconstruct calibration figure from stored_figure=%r",
            stored_figure,
        )
        return _make_info_figure(
            failure_message,
        )


def add_empty_row(
    *,
    rows: list[dict[str, Any]] | None,
    columns: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    next_rows = [
        dict(row)
        for row in (rows or [])
    ]

    next_rows.append(
        {
            str(column["id"]): ""
            for column in (columns or [])
        }
    )

    return next_rows


def extract_xy_from_table(
    table_data: list[dict[str, Any]] | None,
) -> ExtractedCalibrationPoints:
    intensity_calibrated_units_values: list[float] = []
    intensity_au_values: list[float] = []

    for row in table_data or []:
        intensity_calibrated_units = casting.as_float(
            row.get("col1"),
        )
        intensity_au = casting.as_float(
            row.get("col2"),
        )

        if intensity_calibrated_units is None or intensity_au is None:
            continue

        intensity_calibrated_units_values.append(
            float(intensity_calibrated_units)
        )
        intensity_au_values.append(
            float(intensity_au)
        )

    return ExtractedCalibrationPoints(
        intensity_calibrated_units=np.asarray(
            intensity_calibrated_units_values,
            dtype=float,
        ),
        intensity_au=np.asarray(
            intensity_au_values,
            dtype=float,
        ),
    )


def compute_r_squared(
    *,
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    y_true = np.asarray(
        y_true,
        dtype=float,
    )
    y_pred = np.asarray(
        y_pred,
        dtype=float,
    )

    finite_mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[finite_mask]
    y_pred = y_pred[finite_mask]

    if y_true.size < 2:
        return float("nan")

    sum_squared_residuals = float(
        np.sum((y_true - y_pred) ** 2)
    )
    sum_squared_total = float(
        np.sum((y_true - float(np.mean(y_true))) ** 2)
    )

    if sum_squared_total <= 0.0:
        return float("nan")

    return 1.0 - sum_squared_residuals / sum_squared_total


def fit_log10_calibration(
    *,
    intensity_calibrated_units: np.ndarray,
    intensity_au: np.ndarray,
) -> FluorescenceFitResult:
    intensity_calibrated_units = np.asarray(
        intensity_calibrated_units,
        dtype=float,
    )
    intensity_au = np.asarray(
        intensity_au,
        dtype=float,
    )

    finite_mask = np.isfinite(intensity_au) & np.isfinite(intensity_calibrated_units)
    intensity_au = intensity_au[finite_mask]
    intensity_calibrated_units = intensity_calibrated_units[finite_mask]

    positive_mask = (intensity_au > 0.0) & (intensity_calibrated_units > 0.0)
    intensity_au = intensity_au[positive_mask]
    intensity_calibrated_units = intensity_calibrated_units[positive_mask]

    if intensity_au.size < 2:
        raise ValueError(
            "Need at least 2 positive finite bead points for log10 fit."
        )

    intensity_au_log10 = np.log10(
        intensity_au,
    )
    intensity_calibrated_units_log10 = np.log10(
        intensity_calibrated_units,
    )

    slope, intercept = np.polyfit(
        intensity_au_log10,
        intensity_calibrated_units_log10,
        1,
    )

    intensity_calibrated_units_log10_predicted = (
        slope * intensity_au_log10 + intercept
    )

    r_squared = compute_r_squared(
        y_true=intensity_calibrated_units_log10,
        y_pred=intensity_calibrated_units_log10_predicted,
    )

    prefactor = 10.0 ** float(intercept)

    return FluorescenceFitResult(
        slope=float(slope),
        intercept=float(intercept),
        prefactor=float(prefactor),
        r_squared=float(r_squared),
        intensity_au_log10=intensity_au_log10,
        intensity_calibrated_units_log10=intensity_calibrated_units_log10,
    )


def build_reference_points(
    *,
    intensity_calibrated_units: np.ndarray,
    intensity_au: np.ndarray,
) -> list[dict[str, float]]:
    return [
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


def resolve_gating_threshold_value(
    scattering_threshold: Any,
) -> Optional[float]:
    if isinstance(scattering_threshold, dict):
        return casting.as_float(
            scattering_threshold.get("threshold"),
        )

    return casting.as_float(
        scattering_threshold,
    )


def build_calibration_payload(
    *,
    bead_file_path: Optional[str],
    detector_column: Optional[str],
    scattering_detector_column: Optional[str],
    scattering_threshold: Any,
    reference_points: list[dict[str, float]],
    fit_result: FluorescenceFitResult,
) -> dict[str, Any]:
    gating_threshold = resolve_gating_threshold_value(
        scattering_threshold,
    )

    return {
        "schema_version": "1.0",
        "calibration_type": "fluorescence",
        "name": "",
        "created_at": "",
        "source_file": Path(str(bead_file_path)).name if bead_file_path else None,
        "source_channel": str(detector_column) if detector_column else None,
        "gating_channel": str(scattering_detector_column) if scattering_detector_column else None,
        "gating_threshold": gating_threshold,
        "fit_model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
        "fit_metrics": {
            "r_squared": float(fit_result.r_squared),
            "point_count": int(len(reference_points)),
        },
        "parameters": {
            "slope": float(fit_result.slope),
            "intercept": float(fit_result.intercept),
            "prefactor": float(fit_result.prefactor),
        },
        "reference_points": reference_points,
        "export_notes": "",
        "payload": {
            "slope": float(fit_result.slope),
            "intercept": float(fit_result.intercept),
            "prefactor": float(fit_result.prefactor),
            "R_squared": float(fit_result.r_squared),
            "model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
            "x_definition": "Intensity [a.u.]",
            "y_definition": "Intensity [calibrated units]",
        },
    }


def build_apply_status(
    *,
    detector_column: Optional[str],
    valid_event_count: Optional[int],
) -> str:
    if not detector_column:
        return "Calibration fit created successfully."

    return (
        "Calibration fit created successfully. "
        f"Preview computed for {int(valid_event_count or 0)} valid events "
        f"on detector '{detector_column}'."
    )


def build_calibration_figure(
    *,
    x_log10: np.ndarray,
    y_log10: np.ndarray,
    slope: float,
    intercept: float,
) -> go.Figure:
    x_log10 = np.asarray(
        x_log10,
        dtype=float,
    )
    y_log10 = np.asarray(
        y_log10,
        dtype=float,
    )

    x_log10_fit = np.linspace(
        float(np.min(x_log10)),
        float(np.max(x_log10)),
        200,
    )
    y_log10_fit = slope * x_log10_fit + intercept

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=x_log10,
            y=y_log10,
            mode="markers",
            name="beads",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=x_log10_fit,
            y=y_log10_fit,
            mode="lines",
            name="fit",
        )
    )

    figure.update_layout(
        xaxis_title="log10(Intensity [a.u.])",
        yaxis_title="log10(Intensity [calibrated units])",
        separators=".,",
        hovermode="closest",
        uirevision="fluorescence_calibration_graph",
    )

    return figure


def compute_valid_event_count_for_preview(
    *,
    bead_file_path: str,
    detector_column: str,
    slope: float,
    prefactor: float,
) -> int:
    with FCSFile(
        str(bead_file_path),
        writable=False,
    ) as fcs_file:
        raw_intensity_au = fcs_file.column_copy(
            str(detector_column),
            dtype=float,
        )

    raw_intensity_au = np.asarray(
        raw_intensity_au,
        dtype=float,
    )
    raw_intensity_au = raw_intensity_au[
        np.isfinite(raw_intensity_au)
    ]
    raw_intensity_au = raw_intensity_au[
        raw_intensity_au > 0.0
    ]

    calibrated_intensity_units = prefactor * (
        raw_intensity_au ** float(slope)
    )
    calibrated_intensity_units = calibrated_intensity_units[
        np.isfinite(calibrated_intensity_units)
    ]
    calibrated_intensity_units = calibrated_intensity_units[
        calibrated_intensity_units > 0.0
    ]

    return int(
        calibrated_intensity_units.size
    )


def run_calibration_workflow(
    *,
    bead_file_path: Optional[str],
    table_data: list[dict[str, Any]] | None,
    detector_column: Optional[str],
    scattering_detector_column: Optional[str],
    scattering_threshold: Any,
    logger: logging.Logger,
) -> CalibrationResult:
    if not bead_file_path:
        logger.debug(
            "Calibration aborted because bead_file_path is missing."
        )
        figure = _make_info_figure(
            "Upload a bead file first."
        )
        return CalibrationResult(
            figure_store=figure.to_dict(),
            calibration_store=dash.no_update,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status="Missing bead file.",
        )

    extracted_points = extract_xy_from_table(
        table_data or [],
    )

    logger.debug(
        "Initial extracted calibration arrays sizes: calibrated=%r au=%r",
        extracted_points.intensity_calibrated_units.size,
        extracted_points.intensity_au.size,
    )

    if extracted_points.intensity_calibrated_units.size < 2:
        logger.debug(
            "Calibration aborted because fewer than 2 valid bead points were extracted."
        )
        figure = _make_info_figure(
            "Need at least 2 bead points to calibrate."
        )
        return CalibrationResult(
            figure_store=figure.to_dict(),
            calibration_store=dash.no_update,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status="Need at least 2 valid bead rows.",
        )

    fit_result = fit_log10_calibration(
        intensity_calibrated_units=extracted_points.intensity_calibrated_units,
        intensity_au=extracted_points.intensity_au,
    )

    logger.debug(
        "Calibration fit succeeded with slope=%r intercept=%r prefactor=%r r_squared=%r",
        fit_result.slope,
        fit_result.intercept,
        fit_result.prefactor,
        fit_result.r_squared,
    )

    reference_points = build_reference_points(
        intensity_calibrated_units=extracted_points.intensity_calibrated_units,
        intensity_au=extracted_points.intensity_au,
    )

    calibration_payload = build_calibration_payload(
        bead_file_path=bead_file_path,
        detector_column=detector_column,
        scattering_detector_column=scattering_detector_column,
        scattering_threshold=scattering_threshold,
        reference_points=reference_points,
        fit_result=fit_result,
    )

    figure = build_calibration_figure(
        x_log10=fit_result.intensity_au_log10,
        y_log10=fit_result.intensity_calibrated_units_log10,
        slope=fit_result.slope,
        intercept=fit_result.intercept,
    )

    valid_event_count: Optional[int] = None

    if detector_column:
        logger.debug(
            "Computing calibration preview for detector_column=%r using bead_file_path=%r",
            detector_column,
            bead_file_path,
        )
        valid_event_count = compute_valid_event_count_for_preview(
            bead_file_path=bead_file_path,
            detector_column=detector_column,
            slope=fit_result.slope,
            prefactor=fit_result.prefactor,
        )

        logger.debug(
            "Computed calibration preview for detector=%r valid_event_count=%r",
            detector_column,
            valid_event_count,
        )
    else:
        logger.debug(
            "No fluorescence detector selected. Returning calibration fit without detector preview."
        )

    apply_status = build_apply_status(
        detector_column=detector_column,
        valid_event_count=valid_event_count,
    )

    result = CalibrationResult(
        figure_store=figure.to_dict(),
        calibration_store=calibration_payload,
        slope_out=f"{float(fit_result.slope):.6g}",
        intercept_out=f"{float(fit_result.intercept):.6g} (A={float(fit_result.prefactor):.6g})",
        r_squared_out=f"{float(fit_result.r_squared):.6g}",
        apply_status=apply_status,
    )

    logger.debug(
        "run_calibration_workflow returning success with apply_status=%r calibration_payload=%r",
        apply_status,
        calibration_payload,
    )

    return result