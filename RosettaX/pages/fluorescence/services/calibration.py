# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np

from RosettaX.utils import casting


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


def build_bead_rows_from_mesf_values(mesf_values: Any) -> list[dict[str, str]]:
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

        parsed_value = casting._as_float(raw_part)
        if parsed_value is None:
            continue

        parsed_values.append(f"{float(parsed_value):.6g}")

    if not parsed_values:
        return [{"col1": "", "col2": ""} for _ in range(3)]

    return [{"col1": value, "col2": ""} for value in parsed_values]


def extract_xy_from_table(table_data: list[dict[str, Any]] | None) -> ExtractedCalibrationPoints:
    intensity_calibrated_units_values: list[float] = []
    intensity_au_values: list[float] = []

    for row in table_data or []:
        intensity_calibrated_units = casting._as_float(row.get("col1"))
        intensity_au = casting._as_float(row.get("col2"))

        if intensity_calibrated_units is None or intensity_au is None:
            continue

        intensity_calibrated_units_values.append(float(intensity_calibrated_units))
        intensity_au_values.append(float(intensity_au))

    return ExtractedCalibrationPoints(
        intensity_calibrated_units=np.asarray(intensity_calibrated_units_values, dtype=float),
        intensity_au=np.asarray(intensity_au_values, dtype=float),
    )


def compute_r_squared(*, y_true: np.ndarray, y_pred: np.ndarray) -> float:
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


def fit_log10_calibration(
    *,
    intensity_calibrated_units: np.ndarray,
    intensity_au: np.ndarray,
) -> FluorescenceFitResult:
    intensity_calibrated_units = np.asarray(intensity_calibrated_units, dtype=float)
    intensity_au = np.asarray(intensity_au, dtype=float)

    finite_mask = np.isfinite(intensity_au) & np.isfinite(intensity_calibrated_units)
    intensity_au = intensity_au[finite_mask]
    intensity_calibrated_units = intensity_calibrated_units[finite_mask]

    positive_mask = (intensity_au > 0.0) & (intensity_calibrated_units > 0.0)
    intensity_au = intensity_au[positive_mask]
    intensity_calibrated_units = intensity_calibrated_units[positive_mask]

    intensity_au_log10 = np.log10(intensity_au)
    intensity_calibrated_units_log10 = np.log10(intensity_calibrated_units)

    slope, intercept = np.polyfit(
        intensity_au_log10,
        intensity_calibrated_units_log10,
        1,
    )

    intensity_calibrated_units_log10_predicted = slope * intensity_au_log10 + intercept
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


def build_calibration_payload(
    *,
    bead_file_path: Optional[str],
    detector_column: Optional[str],
    scattering_detector_column: Optional[str],
    scattering_threshold: Any,
    reference_points: list[dict[str, float]],
    fit_result: FluorescenceFitResult,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "calibration_type": "fluorescence",
        "name": "",
        "created_at": "",
        "source_file": Path(str(bead_file_path)).name if bead_file_path else None,
        "source_channel": str(detector_column) if detector_column else None,
        "gating_channel": str(scattering_detector_column) if scattering_detector_column else None,
        "gating_threshold": casting._as_float(scattering_threshold),
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
        f"Calibration fit created successfully. "
        f"Preview computed for {int(valid_event_count or 0)} valid events on detector '{detector_column}'."
    )