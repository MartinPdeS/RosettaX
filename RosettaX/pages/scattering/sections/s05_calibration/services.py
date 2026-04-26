# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils import casting
from RosettaX.utils.plottings import _make_info_figure


@dataclass(frozen=True)
class CalibrationResult:
    """
    Result of the scattering calibration service.

    This object intentionally contains plain Python values only. It does not
    depend on Dash. The Dash callback decides how to translate None values into
    dash.no_update when needed.
    """

    figure_store: Optional[dict[str, Any]] = None
    model_figure_store: Optional[dict[str, Any]] = None
    calibration_store: Optional[dict[str, Any]] = None
    bead_table_data: Optional[list[dict[str, Any]]] = None
    slope_out: str = ""
    intercept_out: str = ""
    r_squared_out: str = ""
    apply_status: str = ""

    def to_tuple(self) -> tuple:
        """
        Convert the result to the legacy tuple shape expected by the current
        calibration callback.

        Returns
        -------
        tuple
            Calibration result fields in callback output order.
        """
        return (
            self.figure_store,
            self.model_figure_store,
            self.calibration_store,
            self.bead_table_data,
            self.slope_out,
            self.intercept_out,
            self.r_squared_out,
            self.apply_status,
        )


@dataclass(frozen=True)
class PeakDetectionResultLike:
    """
    Minimal object matching the part of the peak detection result used by the
    backend calibration payload builder.
    """

    peak_positions: np.ndarray


@dataclass(frozen=True)
class OpticalParameters:
    """
    Parsed optical and particle parameters used for scattering calibration.
    """

    medium_refractive_index: float
    particle_refractive_index: Optional[float]
    core_refractive_index: Optional[float]
    shell_refractive_index: Optional[float]
    wavelength_nm: float
    detector_numerical_aperture: float
    detector_cache_numerical_aperture: float
    blocker_bar_numerical_aperture: float
    detector_sampling: int
    detector_phi_angle_degree: float
    detector_gamma_angle_degree: float
    optical_power_watt: float = 1.0
    source_numerical_aperture: float = 0.1
    polarization_angle_degree: float = 0.0


def resolve_mie_model(mie_model: Any) -> str:
    """
    Normalize the selected Mie model name.

    Parameters
    ----------
    mie_model:
        Raw Mie model value from Dash.

    Returns
    -------
    str
        Normalized Mie model name.
    """
    mie_model_string = "" if mie_model is None else str(mie_model).strip()

    if mie_model_string == "Core/Shell Sphere":
        return "Core/Shell Sphere"

    return "Solid Sphere"


def build_peak_detection_result_like_object(
    peak_positions: np.ndarray,
) -> PeakDetectionResultLike:
    """
    Build the minimal peak detection result object required by the backend.

    Parameters
    ----------
    peak_positions:
        Measured peak positions.

    Returns
    -------
    PeakDetectionResultLike
        Minimal peak detection result.
    """
    return PeakDetectionResultLike(
        peak_positions=np.asarray(
            peak_positions,
            dtype=float,
        )
    )


def parse_optical_parameters(
    *,
    medium_refractive_index: Any,
    particle_refractive_index: Any,
    core_refractive_index: Any,
    shell_refractive_index: Any,
    wavelength_nm: Any,
    detector_numerical_aperture: Any,
    detector_cache_numerical_aperture: Any,
    blocker_bar_numerical_aperture: Any,
    detector_sampling: Any,
    detector_phi_angle_degree: Any,
    detector_gamma_angle_degree: Any,
) -> OpticalParameters:
    """
    Parse raw callback values into typed optical parameters.

    Returns
    -------
    OpticalParameters
        Parsed parameters.
    """
    return OpticalParameters(
        medium_refractive_index=casting.as_required_float(
            medium_refractive_index,
            "medium_refractive_index",
        ),
        particle_refractive_index=casting.as_optional_float(
            particle_refractive_index,
        ),
        core_refractive_index=casting.as_optional_float(
            core_refractive_index,
        ),
        shell_refractive_index=casting.as_optional_float(
            shell_refractive_index,
        ),
        wavelength_nm=casting.as_required_float(
            wavelength_nm,
            "wavelength_nm",
        ),
        detector_numerical_aperture=casting.as_required_float(
            detector_numerical_aperture,
            "detector_numerical_aperture",
        ),
        detector_cache_numerical_aperture=casting.as_required_float(
            detector_cache_numerical_aperture,
            "detector_cache_numerical_aperture",
        ),
        blocker_bar_numerical_aperture=casting.as_required_float(
            blocker_bar_numerical_aperture,
            "blocker_bar_numerical_aperture",
        ),
        detector_sampling=casting.as_required_int(
            detector_sampling,
            "detector_sampling",
        ),
        detector_phi_angle_degree=casting.as_required_float(
            detector_phi_angle_degree,
            "detector_phi_angle_degree",
        ),
        detector_gamma_angle_degree=casting.as_required_float(
            detector_gamma_angle_degree,
            "detector_gamma_angle_degree",
        ),
    )


def parse_sphere_rows_for_fit(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> dict[str, Any]:
    """
    Extract valid solid sphere calibration rows.

    Parameters
    ----------
    rows:
        Calibration table rows.

    Returns
    -------
    dict[str, Any]
        Parsed row indices, diameters, and measured peak positions.
    """
    row_indices: list[int] = []
    particle_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    for row_index, row in enumerate(rows or []):
        try:
            raw_particle_diameter_nm = row.get("particle_diameter_nm")
            raw_measured_peak_position = row.get("measured_peak_position")

            if raw_particle_diameter_nm in ("", None):
                continue

            if raw_measured_peak_position in ("", None):
                continue

            particle_diameter_nm = float(raw_particle_diameter_nm)
            measured_peak_position = float(raw_measured_peak_position)

        except Exception:
            continue

        if particle_diameter_nm <= 0.0:
            continue

        if measured_peak_position <= 0.0:
            continue

        row_indices.append(row_index)
        particle_diameters_nm.append(particle_diameter_nm)
        measured_peak_positions.append(measured_peak_position)

    return {
        "row_count": len(row_indices),
        "row_indices": row_indices,
        "particle_diameters_nm": np.asarray(
            particle_diameters_nm,
            dtype=float,
        ),
        "measured_peak_positions": np.asarray(
            measured_peak_positions,
            dtype=float,
        ),
    }


def parse_core_shell_rows_for_fit(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> dict[str, Any]:
    """
    Extract valid core shell calibration rows.

    Parameters
    ----------
    rows:
        Calibration table rows.

    Returns
    -------
    dict[str, Any]
        Parsed row indices, geometry values, and measured peak positions.
    """
    row_indices: list[int] = []
    core_diameters_nm: list[float] = []
    shell_thicknesses_nm: list[float] = []
    outer_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    for row_index, row in enumerate(rows or []):
        try:
            raw_core_diameter_nm = row.get("core_diameter_nm")
            raw_shell_thickness_nm = row.get("shell_thickness_nm")
            raw_measured_peak_position = row.get("measured_peak_position")

            if raw_core_diameter_nm in ("", None):
                continue

            if raw_shell_thickness_nm in ("", None):
                continue

            if raw_measured_peak_position in ("", None):
                continue

            core_diameter_nm = float(raw_core_diameter_nm)
            shell_thickness_nm = float(raw_shell_thickness_nm)
            measured_peak_position = float(raw_measured_peak_position)

        except Exception:
            continue

        if core_diameter_nm <= 0.0:
            continue

        if shell_thickness_nm < 0.0:
            continue

        if measured_peak_position <= 0.0:
            continue

        outer_diameter_nm = core_diameter_nm + 2.0 * shell_thickness_nm

        row_indices.append(row_index)
        core_diameters_nm.append(core_diameter_nm)
        shell_thicknesses_nm.append(shell_thickness_nm)
        outer_diameters_nm.append(outer_diameter_nm)
        measured_peak_positions.append(measured_peak_position)

    return {
        "row_count": len(row_indices),
        "row_indices": row_indices,
        "core_diameters_nm": np.asarray(
            core_diameters_nm,
            dtype=float,
        ),
        "shell_thicknesses_nm": np.asarray(
            shell_thicknesses_nm,
            dtype=float,
        ),
        "outer_diameters_nm": np.asarray(
            outer_diameters_nm,
            dtype=float,
        ),
        "measured_peak_positions": np.asarray(
            measured_peak_positions,
            dtype=float,
        ),
    }


def write_expected_coupling_into_sphere_table(
    *,
    rows: list[dict[str, Any]],
    row_indices: list[int],
    expected_coupling_values: np.ndarray,
) -> list[dict[str, str]]:
    """
    Write expected coupling values into the calibration table rows.

    Parameters
    ----------
    rows:
        Current table rows.

    row_indices:
        Indices of rows that were used in the fit.

    expected_coupling_values:
        Expected coupling values to write.

    Returns
    -------
    list[dict[str, str]]
        Updated table rows.
    """
    updated_rows = [dict(row) for row in rows]

    expected_coupling_values = np.asarray(
        expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    for row in updated_rows:
        row["expected_coupling"] = ""

    for row_index, expected_coupling_value in zip(
        row_indices,
        expected_coupling_values,
        strict=False,
    ):
        if row_index >= len(updated_rows):
            continue

        updated_rows[row_index]["expected_coupling"] = (
            f"{float(expected_coupling_value):.6g}"
        )

    return [
        {
            key: "" if value is None else str(value)
            for key, value in row.items()
        }
        for row in updated_rows
    ]


def build_model_comparison_figure(
    *,
    measured_peak_positions: np.ndarray,
    expected_coupling_values: np.ndarray,
    particle_diameters_nm: np.ndarray,
) -> go.Figure:
    """
    Build the calibration comparison figure.

    Returns
    -------
    go.Figure
        Figure comparing measured peak position and expected coupling.
    """
    figure = go.Figure()

    measured_peak_positions = np.asarray(
        measured_peak_positions,
        dtype=float,
    ).reshape(-1)

    expected_coupling_values = np.asarray(
        expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    particle_diameters_nm = np.asarray(
        particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    figure.add_trace(
        go.Scatter(
            x=measured_peak_positions,
            y=expected_coupling_values,
            mode="markers+text",
            text=[
                f"{float(diameter):.6g} nm"
                for diameter in particle_diameters_nm
            ],
            textposition="top center",
            name="Reference points",
        )
    )

    figure.update_layout(
        xaxis_title="Measured peak position [a.u.]",
        yaxis_title="Expected coupling",
        separators=".,",
        hovermode="closest",
        uirevision="scattering_calibration_left_graph",
    )

    figure.update_yaxes(
        type="log",
        exponentformat="e",
        showexponent="all",
    )

    return figure


def build_core_shell_placeholder_figure(
    *,
    measured_peak_positions: np.ndarray,
    outer_diameters_nm: np.ndarray,
) -> go.Figure:
    """
    Build a temporary diagnostic figure for core shell calibration rows.

    Returns
    -------
    go.Figure
        Placeholder figure.
    """
    figure = go.Figure()

    outer_diameters_nm = np.asarray(
        outer_diameters_nm,
        dtype=float,
    ).reshape(-1)

    figure.add_trace(
        go.Scatter(
            x=np.asarray(
                measured_peak_positions,
                dtype=float,
            ),
            y=outer_diameters_nm,
            mode="markers+text",
            text=[
                f"{float(value):.6g} nm"
                for value in outer_diameters_nm
            ],
            textposition="top center",
            name="Parsed rows",
        )
    )

    figure.update_layout(
        xaxis_title="Measured peak position [a.u.]",
        yaxis_title="Outer diameter [nm]",
        separators=".,",
        hovermode="closest",
    )

    return figure


def build_dense_simulated_coupling_curve(
    *,
    particle_diameters_nm: np.ndarray,
    optical_parameters: OpticalParameters,
    simulated_curve_point_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build a dense simulated coupling curve for the right graph.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Dense diameter values and dense expected coupling values.
    """
    particle_diameters_nm = np.asarray(
        particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    if particle_diameters_nm.size == 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    diameter_min = float(np.min(particle_diameters_nm))
    diameter_max = float(np.max(particle_diameters_nm))

    if diameter_min <= 0.0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    if diameter_max <= 0.0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    dense_diameter_values = np.linspace(
        diameter_min,
        diameter_max,
        int(simulated_curve_point_count),
    )

    dense_modeled_coupling_result = BackEnd.compute_modeled_coupling_from_diameters(
        particle_diameters_nm=dense_diameter_values,
        wavelength_nm=optical_parameters.wavelength_nm,
        source_numerical_aperture=optical_parameters.source_numerical_aperture,
        optical_power_watt=optical_parameters.optical_power_watt,
        detector_numerical_aperture=optical_parameters.detector_numerical_aperture,
        medium_refractive_index=optical_parameters.medium_refractive_index,
        particle_refractive_index=float(optical_parameters.particle_refractive_index),
        detector_cache_numerical_aperture=optical_parameters.detector_cache_numerical_aperture,
        detector_phi_offset_degree=optical_parameters.detector_phi_angle_degree,
        detector_gamma_offset_degree=optical_parameters.detector_gamma_angle_degree,
        polarization_angle_degree=optical_parameters.polarization_angle_degree,
        detector_sampling=optical_parameters.detector_sampling,
    )

    return (
        np.asarray(
            dense_modeled_coupling_result.particle_diameters_nm,
            dtype=float,
        ).reshape(-1),
        np.asarray(
            dense_modeled_coupling_result.expected_coupling_values,
            dtype=float,
        ).reshape(-1),
    )


def build_simulated_coupling_vs_diameter_figure(
    *,
    particle_diameters_nm: np.ndarray,
    expected_coupling_values: np.ndarray,
    dense_particle_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    simulated_curve_point_count: int,
) -> go.Figure:
    """
    Build the simulated coupling versus diameter figure.

    Returns
    -------
    go.Figure
        Simulated coupling figure.
    """
    figure = go.Figure()

    point_x_values = np.asarray(
        particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    point_y_values = np.asarray(
        expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    line_x_values = np.asarray(
        dense_particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    line_y_values = np.asarray(
        dense_expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    point_mask = (
        np.isfinite(point_x_values)
        & np.isfinite(point_y_values)
        & (point_y_values > 0.0)
    )

    line_mask = (
        np.isfinite(line_x_values)
        & np.isfinite(line_y_values)
        & (line_y_values > 0.0)
    )

    point_x_values = point_x_values[point_mask]
    point_y_values = point_y_values[point_mask]
    line_x_values = line_x_values[line_mask]
    line_y_values = line_y_values[line_mask]

    if point_x_values.size == 0 and line_x_values.size == 0:
        return _make_info_figure("No simulated coupling data available.")

    if point_x_values.size > 0:
        point_order = np.argsort(point_x_values)
        point_x_values = point_x_values[point_order]
        point_y_values = point_y_values[point_order]

    if line_x_values.size > 0:
        line_order = np.argsort(line_x_values)
        line_x_values = line_x_values[line_order]
        line_y_values = line_y_values[line_order]

        figure.add_trace(
            go.Scatter(
                x=line_x_values,
                y=line_y_values,
                mode="lines",
                name=f"Model ({int(simulated_curve_point_count)} points)",
            )
        )

    if point_x_values.size > 0:
        figure.add_trace(
            go.Scatter(
                x=point_x_values,
                y=point_y_values,
                mode="markers",
                name="Simulated points",
                text=[
                    f"{float(value):.6g} nm"
                    for value in point_x_values
                ],
                textposition="top center",
            )
        )

    figure.update_layout(
        xaxis_title="Particle diameter [nm]",
        yaxis_title="Simulated coupling",
        separators=".,",
        hovermode="closest",
        uirevision="scattering_calibration_right_graph",
    )

    figure.update_yaxes(
        type="log",
        exponentformat="e",
        showexponent="all",
    )

    return figure


def build_missing_input_result(message: str) -> CalibrationResult:
    """
    Build a calibration result for missing required inputs.

    Parameters
    ----------
    message:
        Message to display.

    Returns
    -------
    CalibrationResult
        Result with informational graph payloads.
    """
    left_figure = _make_info_figure(message)
    right_figure = _make_info_figure(message)

    return CalibrationResult(
        figure_store=left_figure.to_dict(),
        model_figure_store=right_figure.to_dict(),
        calibration_store=None,
        bead_table_data=None,
        slope_out="",
        intercept_out="",
        r_squared_out="",
        apply_status=message,
    )


def run_core_shell_calibration_placeholder(
    *,
    current_table_rows: list[dict[str, Any]],
    resolved_core_refractive_index: float,
    resolved_shell_refractive_index: float,
) -> CalibrationResult:
    """
    Temporary core shell calibration branch.

    Returns
    -------
    CalibrationResult
        Placeholder result.
    """
    parsed_core_shell_rows = parse_core_shell_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_core_shell_rows["row_count"] < 2:
        left_figure = _make_info_figure(
            "Enter at least 2 valid core shell rows with measured peak positions."
        )

        right_figure = _make_info_figure(
            "Enter at least 2 valid core shell rows with measured peak positions."
        )

        return CalibrationResult(
            figure_store=left_figure.to_dict(),
            model_figure_store=right_figure.to_dict(),
            calibration_store=None,
            bead_table_data=None,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status="Need at least 2 valid core shell rows.",
        )

    left_figure = build_core_shell_placeholder_figure(
        measured_peak_positions=parsed_core_shell_rows["measured_peak_positions"],
        outer_diameters_nm=parsed_core_shell_rows["outer_diameters_nm"],
    )

    right_figure = _make_info_figure(
        "Core/Shell Sphere coupling fit is not implemented yet."
    )

    return CalibrationResult(
        figure_store=left_figure.to_dict(),
        model_figure_store=right_figure.to_dict(),
        calibration_store=None,
        bead_table_data=current_table_rows,
        slope_out="",
        intercept_out="",
        r_squared_out="",
        apply_status=(
            f"Core/Shell rows parsed successfully with core RI={resolved_core_refractive_index:.6g} "
            f"and shell RI={resolved_shell_refractive_index:.6g}, but fitting is not implemented yet."
        ),
    )


def run_solid_sphere_calibration(
    *,
    uploaded_fcs_path: str,
    detector_column: str,
    current_table_rows: list[dict[str, Any]],
    optical_parameters: OpticalParameters,
    simulated_curve_point_count: int,
) -> CalibrationResult:
    """
    Run solid sphere scattering calibration.

    Returns
    -------
    CalibrationResult
        Fitted calibration result.
    """
    if optical_parameters.particle_refractive_index is None:
        raise ValueError(
            "particle_refractive_index is required for Solid Sphere calibration."
        )

    scattering_backend = BackEnd()
    scattering_backend.fcs_file_path = uploaded_fcs_path

    parsed_sphere_rows = parse_sphere_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_sphere_rows["row_count"] < 2:
        left_figure = _make_info_figure(
            "Enter at least 2 valid rows with particle diameter and measured peak position."
        )

        right_figure = _make_info_figure(
            "You may need to click Compute Expected Coupling first."
        )

        return CalibrationResult(
            figure_store=left_figure.to_dict(),
            model_figure_store=right_figure.to_dict(),
            calibration_store=None,
            bead_table_data=None,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status="Need at least 2 valid calibration rows.",
        )

    modeled_coupling_result = (
        scattering_backend.compute_modeled_coupling_from_diameters(
            particle_diameters_nm=parsed_sphere_rows["particle_diameters_nm"],
            wavelength_nm=optical_parameters.wavelength_nm,
            source_numerical_aperture=optical_parameters.source_numerical_aperture,
            optical_power_watt=optical_parameters.optical_power_watt,
            detector_numerical_aperture=optical_parameters.detector_numerical_aperture,
            medium_refractive_index=optical_parameters.medium_refractive_index,
            particle_refractive_index=float(optical_parameters.particle_refractive_index),
            detector_cache_numerical_aperture=optical_parameters.detector_cache_numerical_aperture,
            detector_phi_offset_degree=optical_parameters.detector_phi_angle_degree,
            detector_gamma_offset_degree=optical_parameters.detector_gamma_angle_degree,
            polarization_angle_degree=optical_parameters.polarization_angle_degree,
            detector_sampling=optical_parameters.detector_sampling,
        )
    )

    fit_result = scattering_backend.fit_measured_peak_positions_to_modeled_coupling(
        measured_peak_positions=parsed_sphere_rows["measured_peak_positions"],
        modeled_coupling_result=modeled_coupling_result,
    )

    dense_particle_diameters_nm, dense_expected_coupling_values = (
        build_dense_simulated_coupling_curve(
            particle_diameters_nm=np.asarray(
                modeled_coupling_result.particle_diameters_nm,
                dtype=float,
            ),
            optical_parameters=optical_parameters,
            simulated_curve_point_count=simulated_curve_point_count,
        )
    )

    left_figure = build_model_comparison_figure(
        measured_peak_positions=np.asarray(
            parsed_sphere_rows["measured_peak_positions"],
            dtype=float,
        ),
        expected_coupling_values=np.asarray(
            fit_result.expected_coupling_values,
            dtype=float,
        ),
        particle_diameters_nm=np.asarray(
            parsed_sphere_rows["particle_diameters_nm"],
            dtype=float,
        ),
    )

    right_figure = build_simulated_coupling_vs_diameter_figure(
        particle_diameters_nm=np.asarray(
            modeled_coupling_result.particle_diameters_nm,
            dtype=float,
        ),
        expected_coupling_values=np.asarray(
            modeled_coupling_result.expected_coupling_values,
            dtype=float,
        ),
        dense_particle_diameters_nm=dense_particle_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        simulated_curve_point_count=simulated_curve_point_count,
    )

    calibration_payload = scattering_backend.build_calibration_payload(
        detector_column=str(detector_column),
        peak_detection_result=build_peak_detection_result_like_object(
            peak_positions=np.asarray(
                parsed_sphere_rows["measured_peak_positions"],
                dtype=float,
            ),
        ),
        modeled_coupling_result=modeled_coupling_result,
        fit_result=fit_result,
        notes="",
    )

    calibration_payload["payload"]["parameters"].update(
        {
            "mie_model": "Solid Sphere",
            "medium_refractive_index": optical_parameters.medium_refractive_index,
            "particle_refractive_index": optical_parameters.particle_refractive_index,
            "core_refractive_index": optical_parameters.core_refractive_index,
            "shell_refractive_index": optical_parameters.shell_refractive_index,
            "particle_diameter_nm": fit_result.particle_diameters_nm.tolist(),
            "wavelength_nm": optical_parameters.wavelength_nm,
            "optical_power_watt": optical_parameters.optical_power_watt,
            "source_numerical_aperture": optical_parameters.source_numerical_aperture,
            "detector_numerical_aperture": optical_parameters.detector_numerical_aperture,
            "detector_cache_numerical_aperture": optical_parameters.detector_cache_numerical_aperture,
            "blocker_bar_numerical_aperture": optical_parameters.blocker_bar_numerical_aperture,
            "detector_sampling": optical_parameters.detector_sampling,
            "detector_phi_angle_degree": optical_parameters.detector_phi_angle_degree,
            "detector_gamma_angle_degree": optical_parameters.detector_gamma_angle_degree,
        }
    )

    updated_table_rows = write_expected_coupling_into_sphere_table(
        rows=current_table_rows,
        row_indices=parsed_sphere_rows["row_indices"],
        expected_coupling_values=fit_result.expected_coupling_values,
    )

    return CalibrationResult(
        figure_store=left_figure.to_dict(),
        model_figure_store=right_figure.to_dict(),
        calibration_store=calibration_payload,
        bead_table_data=updated_table_rows,
        slope_out=f"{fit_result.slope:.6g}",
        intercept_out=f"{fit_result.intercept:.6g} (A={fit_result.prefactor:.6g})",
        r_squared_out=f"{fit_result.r_squared:.6g}",
        apply_status="Calibration fitted successfully.",
    )


def run_scattering_calibration(
    *,
    uploaded_fcs_path: Any,
    detector_column: Any,
    mie_model: Any,
    bead_table_data: Optional[list[dict[str, Any]]],
    medium_refractive_index: Any,
    particle_refractive_index: Any,
    core_refractive_index: Any,
    shell_refractive_index: Any,
    wavelength_nm: Any,
    detector_numerical_aperture: Any,
    detector_cache_numerical_aperture: Any,
    blocker_bar_numerical_aperture: Any,
    detector_sampling: Any,
    detector_phi_angle_degree: Any,
    detector_gamma_angle_degree: Any,
    simulated_curve_point_count: int,
    logger: logging.Logger,
) -> CalibrationResult:
    """
    Run the scattering calibration workflow.

    Parameters
    ----------
    uploaded_fcs_path:
        Uploaded FCS file path.

    detector_column:
        Detector column used for calibration.

    mie_model:
        Selected Mie model.

    bead_table_data:
        Calibration reference table rows.

    simulated_curve_point_count:
        Number of points in the dense simulated curve.

    logger:
        Logger used by the caller.

    Returns
    -------
    CalibrationResult
        Calibration result.
    """
    logger.debug(
        "run_scattering_calibration called with uploaded_fcs_path=%r "
        "detector_column=%r mie_model=%r table_row_count=%r",
        uploaded_fcs_path,
        detector_column,
        mie_model,
        None if bead_table_data is None else len(bead_table_data),
    )

    try:
        current_table_rows = [
            dict(row)
            for row in (bead_table_data or [])
        ]

        resolved_mie_model = resolve_mie_model(
            mie_model,
        )

        if not uploaded_fcs_path:
            return build_missing_input_result(
                "Missing FCS file."
            )

        if not detector_column:
            return build_missing_input_result(
                "Missing scattering detector."
            )

        optical_parameters = parse_optical_parameters(
            medium_refractive_index=medium_refractive_index,
            particle_refractive_index=particle_refractive_index,
            core_refractive_index=core_refractive_index,
            shell_refractive_index=shell_refractive_index,
            wavelength_nm=wavelength_nm,
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
            detector_sampling=detector_sampling,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
        )

        logger.debug(
            "Resolved optical parameters=%r",
            optical_parameters,
        )

        if resolved_mie_model == "Core/Shell Sphere":
            if optical_parameters.core_refractive_index is None:
                raise ValueError(
                    "core_refractive_index is required for Core/Shell Sphere."
                )

            if optical_parameters.shell_refractive_index is None:
                raise ValueError(
                    "shell_refractive_index is required for Core/Shell Sphere."
                )

            return run_core_shell_calibration_placeholder(
                current_table_rows=current_table_rows,
                resolved_core_refractive_index=float(
                    optical_parameters.core_refractive_index,
                ),
                resolved_shell_refractive_index=float(
                    optical_parameters.shell_refractive_index,
                ),
            )

        return run_solid_sphere_calibration(
            uploaded_fcs_path=str(uploaded_fcs_path),
            detector_column=str(detector_column),
            current_table_rows=current_table_rows,
            optical_parameters=optical_parameters,
            simulated_curve_point_count=simulated_curve_point_count,
        )

    except Exception as exc:
        logger.exception("Scattering calibration failed.")

        left_figure = _make_info_figure(
            "Calibration fitting failed."
        )

        right_figure = _make_info_figure(
            "Calibration fitting failed."
        )

        return CalibrationResult(
            figure_store=left_figure.to_dict(),
            model_figure_store=right_figure.to_dict(),
            calibration_store=None,
            bead_table_data=None,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status=f"{type(exc).__name__}: {exc}",
        )