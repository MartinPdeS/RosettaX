# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.pages.p03_scattering.backend import BackEnd
from RosettaX.utils import plottings
from .scattering import OpticalParameters
from .scattering import build_solid_sphere_scattering_calibration_from_standard_data
from .scattering import parse_core_shell_rows_for_fit
from .scattering import parse_optical_parameters
from .scattering import parse_sphere_rows_for_fit
from .scattering import resolve_mie_model


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
        Convert the result to the tuple shape expected by the calibration callback.
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


def build_instrument_response_figure(
    *,
    measured_peak_positions: np.ndarray,
    expected_coupling_values: np.ndarray,
    particle_diameters_nm: np.ndarray,
    slope: float,
    intercept: float,
) -> go.Figure:
    """
    Build the measured signal to modeled coupling instrument response figure.

    Axis scaling is intentionally not forced here. The Dash graph callbacks
    apply the selected linear or log display mode.
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

    valid_mask = (
        np.isfinite(measured_peak_positions)
        & np.isfinite(expected_coupling_values)
        & np.isfinite(particle_diameters_nm)
        & (measured_peak_positions > 0.0)
        & (expected_coupling_values > 0.0)
    )

    measured_peak_positions = measured_peak_positions[valid_mask]
    expected_coupling_values = expected_coupling_values[valid_mask]
    particle_diameters_nm = particle_diameters_nm[valid_mask]

    if measured_peak_positions.size == 0:
        return plottings._make_info_figure(
            "No valid instrument response data available."
        )

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
            name="Calibration standards",
        )
    )

    x_min = float(
        np.min(
            measured_peak_positions,
        )
    )

    x_max = float(
        np.max(
            measured_peak_positions,
        )
    )

    if x_max == x_min:
        fit_x_values = np.asarray(
            [
                x_min,
                x_min * 1.01,
            ],
            dtype=float,
        )

    else:
        fit_x_values = np.linspace(
            x_min,
            x_max,
            200,
        )

    fit_y_values = slope * fit_x_values + intercept

    fit_mask = (
        np.isfinite(fit_x_values)
        & np.isfinite(fit_y_values)
        & (fit_y_values > 0.0)
    )

    if np.any(fit_mask):
        figure.add_trace(
            go.Scatter(
                x=fit_x_values[fit_mask],
                y=fit_y_values[fit_mask],
                mode="lines",
                name="Instrument response fit",
            )
        )

    figure.update_layout(
        title="Instrument response calibration",
        xaxis_title="Measured standard peak intensity [a.u.]",
        yaxis_title="Modeled optical coupling",
        separators=".,",
        hovermode="closest",
        uirevision="scattering_instrument_response_graph",
    )

    return figure


def build_core_shell_placeholder_figure(
    *,
    measured_peak_positions: np.ndarray,
    outer_diameters_nm: np.ndarray,
) -> go.Figure:
    """
    Build a temporary diagnostic figure for core shell calibration rows.
    """
    figure = go.Figure()

    measured_peak_positions = np.asarray(
        measured_peak_positions,
        dtype=float,
    ).reshape(-1)

    outer_diameters_nm = np.asarray(
        outer_diameters_nm,
        dtype=float,
    ).reshape(-1)

    valid_mask = (
        np.isfinite(measured_peak_positions)
        & np.isfinite(outer_diameters_nm)
        & (measured_peak_positions > 0.0)
        & (outer_diameters_nm > 0.0)
    )

    measured_peak_positions = measured_peak_positions[valid_mask]
    outer_diameters_nm = outer_diameters_nm[valid_mask]

    if measured_peak_positions.size == 0:
        return plottings._make_info_figure(
            "No valid core shell standard rows available."
        )

    figure.add_trace(
        go.Scatter(
            x=measured_peak_positions,
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
        title="Core shell standard rows",
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
    Build a dense calibration standard Mie relation for the right graph.
    """
    particle_diameters_nm = np.asarray(
        particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    if particle_diameters_nm.size == 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    if optical_parameters.particle_refractive_index is None:
        raise ValueError(
            "particle_refractive_index is required for Solid Sphere calibration."
        )

    diameter_min = float(
        np.min(
            particle_diameters_nm,
        )
    )

    diameter_max = float(
        np.max(
            particle_diameters_nm,
        )
    )

    if diameter_min <= 0.0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    if diameter_max <= 0.0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    if diameter_max == diameter_min:
        diameter_max = diameter_min * 1.01

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
        particle_refractive_index=float(
            optical_parameters.particle_refractive_index,
        ),
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


def build_calibration_standard_mie_relation_figure(
    *,
    particle_diameters_nm: np.ndarray,
    expected_coupling_values: np.ndarray,
    dense_particle_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    simulated_curve_point_count: int,
) -> go.Figure:
    """
    Build the calibration standard Mie relation figure.

    Axis scaling is intentionally not forced here. The Dash graph callbacks
    apply the selected linear or log display mode.
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
        & (point_x_values > 0.0)
        & (point_y_values > 0.0)
    )

    line_mask = (
        np.isfinite(line_x_values)
        & np.isfinite(line_y_values)
        & (line_x_values > 0.0)
        & (line_y_values > 0.0)
    )

    point_x_values = point_x_values[point_mask]
    point_y_values = point_y_values[point_mask]
    line_x_values = line_x_values[line_mask]
    line_y_values = line_y_values[line_mask]

    if point_x_values.size == 0 and line_x_values.size == 0:
        return plottings._make_info_figure(
            "No calibration standard Mie relation data available."
        )

    if line_x_values.size > 0:
        line_order = np.argsort(
            line_x_values,
        )

        line_x_values = line_x_values[line_order]
        line_y_values = line_y_values[line_order]

        figure.add_trace(
            go.Scatter(
                x=line_x_values,
                y=line_y_values,
                mode="lines",
                name=f"Mie relation ({int(simulated_curve_point_count)} points)",
            )
        )

    if point_x_values.size > 0:
        point_order = np.argsort(
            point_x_values,
        )

        point_x_values = point_x_values[point_order]
        point_y_values = point_y_values[point_order]

        figure.add_trace(
            go.Scatter(
                x=point_x_values,
                y=point_y_values,
                mode="markers+text",
                name="Calibration standards",
                text=[
                    f"{float(value):.6g} nm"
                    for value in point_x_values
                ],
                textposition="top center",
            )
        )

    figure.update_layout(
        title="Calibration standard Mie relation",
        xaxis_title="Standard particle diameter [nm]",
        yaxis_title="Modeled optical coupling",
        separators=".,",
        hovermode="closest",
        uirevision="scattering_standard_mie_relation_graph",
    )

    return figure


def build_missing_input_result(
    message: str,
) -> CalibrationResult:
    """
    Build a calibration result for missing required inputs.
    """
    left_figure = plottings._make_info_figure(
        message,
    )

    right_figure = plottings._make_info_figure(
        message,
    )

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
    """
    parsed_core_shell_rows = parse_core_shell_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_core_shell_rows.row_count < 2:
        left_figure = plottings._make_info_figure(
            "Enter at least 2 valid core shell standard rows with measured peak positions."
        )

        right_figure = plottings._make_info_figure(
            "Enter at least 2 valid core shell standard rows with measured peak positions."
        )

        return CalibrationResult(
            figure_store=left_figure.to_dict(),
            model_figure_store=right_figure.to_dict(),
            calibration_store=None,
            bead_table_data=None,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status="Need at least 2 valid core shell standard rows.",
        )

    left_figure = build_core_shell_placeholder_figure(
        measured_peak_positions=parsed_core_shell_rows.measured_peak_positions,
        outer_diameters_nm=parsed_core_shell_rows.outer_diameters_nm,
    )

    right_figure = plottings._make_info_figure(
        "Core/Shell Sphere instrument response fitting is not implemented yet."
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
    Run solid sphere scattering instrument response calibration.
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

    if parsed_sphere_rows.row_count < 2:
        left_figure = plottings._make_info_figure(
            "Enter at least 2 valid standard rows with particle diameter and measured peak position."
        )

        right_figure = plottings._make_info_figure(
            "You may need to click Compute Standard Coupling first."
        )

        return CalibrationResult(
            figure_store=left_figure.to_dict(),
            model_figure_store=right_figure.to_dict(),
            calibration_store=None,
            bead_table_data=None,
            slope_out="",
            intercept_out="",
            r_squared_out="",
            apply_status="Need at least 2 valid calibration standard rows.",
        )

    modeled_coupling_result = scattering_backend.compute_modeled_coupling_from_diameters(
        particle_diameters_nm=parsed_sphere_rows.particle_diameters_nm,
        wavelength_nm=optical_parameters.wavelength_nm,
        source_numerical_aperture=optical_parameters.source_numerical_aperture,
        optical_power_watt=optical_parameters.optical_power_watt,
        detector_numerical_aperture=optical_parameters.detector_numerical_aperture,
        medium_refractive_index=optical_parameters.medium_refractive_index,
        particle_refractive_index=float(
            optical_parameters.particle_refractive_index,
        ),
        detector_cache_numerical_aperture=optical_parameters.detector_cache_numerical_aperture,
        detector_phi_offset_degree=optical_parameters.detector_phi_angle_degree,
        detector_gamma_offset_degree=optical_parameters.detector_gamma_angle_degree,
        polarization_angle_degree=optical_parameters.polarization_angle_degree,
        detector_sampling=optical_parameters.detector_sampling,
    )

    measured_peak_positions = np.asarray(
        parsed_sphere_rows.measured_peak_positions,
        dtype=float,
    ).reshape(-1)

    particle_diameters_nm = np.asarray(
        modeled_coupling_result.particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    expected_coupling_values = np.asarray(
        modeled_coupling_result.expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    dense_particle_diameters_nm, dense_expected_coupling_values = build_dense_simulated_coupling_curve(
        particle_diameters_nm=particle_diameters_nm,
        optical_parameters=optical_parameters,
        simulated_curve_point_count=simulated_curve_point_count,
    )

    metadata = {
        "measured_channel": str(
            detector_column,
        ),
        "uploaded_fcs_path": str(
            uploaded_fcs_path,
        ),
    }

    build_result = build_solid_sphere_scattering_calibration_from_standard_data(
        detector_column=str(
            detector_column,
        ),
        current_table_rows=current_table_rows,
        measured_peak_positions=measured_peak_positions,
        particle_diameters_nm=particle_diameters_nm,
        expected_coupling_values=expected_coupling_values,
        dense_particle_diameters_nm=dense_particle_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        optical_parameters=optical_parameters,
        metadata=metadata,
        force_zero_intercept=True,
    )

    left_figure = build_instrument_response_figure(
        measured_peak_positions=build_result.measured_peak_positions,
        expected_coupling_values=build_result.standard_coupling_values,
        particle_diameters_nm=build_result.standard_diameters_nm,
        slope=build_result.instrument_response.slope,
        intercept=build_result.instrument_response.intercept,
    )

    right_figure = build_calibration_standard_mie_relation_figure(
        particle_diameters_nm=particle_diameters_nm,
        expected_coupling_values=expected_coupling_values,
        dense_particle_diameters_nm=dense_particle_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        simulated_curve_point_count=simulated_curve_point_count,
    )

    return CalibrationResult(
        figure_store=left_figure.to_dict(),
        model_figure_store=right_figure.to_dict(),
        calibration_store=build_result.calibration.to_dict(),
        bead_table_data=build_result.updated_table_rows,
        slope_out=f"{build_result.instrument_response.slope:.6g}",
        intercept_out=f"{build_result.instrument_response.intercept:.6g}",
        r_squared_out=f"{build_result.instrument_response.r_squared:.6g}",
        apply_status="Instrument response fitted successfully.",
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

    The saved scattering calibration is a version 2 payload containing an
    instrument response and a calibration standard Mie relation.
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
            if isinstance(row, dict)
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
            uploaded_fcs_path=str(
                uploaded_fcs_path,
            ),
            detector_column=str(
                detector_column,
            ),
            current_table_rows=current_table_rows,
            optical_parameters=optical_parameters,
            simulated_curve_point_count=simulated_curve_point_count,
        )

    except Exception as exc:
        logger.exception("Scattering instrument response calibration failed.")

        left_figure = plottings._make_info_figure(
            "Instrument response fitting failed."
        )

        right_figure = plottings._make_info_figure(
            "Calibration standard Mie relation failed."
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