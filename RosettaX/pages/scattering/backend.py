# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import plotly.graph_objs as go
from scipy.signal import find_peaks

from PyMieSim.units import ureg
from PyMieSim.experiment.detector_set import PhotodiodeSet
from PyMieSim.experiment.scatterer_set import SphereSet
from PyMieSim.experiment.source_set import GaussianSet
from PyMieSim.experiment.polarization_set import PolarizationSet
from PyMieSim.experiment import Setup

from RosettaX.utils.reader import FCSFile


@dataclass(frozen=True)
class HistogramResult:
    values: np.ndarray
    counts: np.ndarray
    edges: np.ndarray
    centers: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "values": self.values.tolist(),
            "counts": self.counts.tolist(),
            "edges": self.edges.tolist(),
            "centers": self.centers.tolist(),
        }


@dataclass(frozen=True)
class PeakDetectionResult:
    peak_indices: np.ndarray
    peak_positions: np.ndarray
    peak_heights: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_indices": self.peak_indices.tolist(),
            "peak_positions": self.peak_positions.tolist(),
            "peak_heights": self.peak_heights.tolist(),
        }


@dataclass(frozen=True)
class ModeledCouplingResult:
    particle_diameters_nm: np.ndarray
    expected_coupling_values: np.ndarray
    model_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "particle_diameters_nm": self.particle_diameters_nm.tolist(),
            "expected_coupling_values": self.expected_coupling_values.tolist(),
            "model_metadata": self.model_metadata,
        }


@dataclass(frozen=True)
class ScatteringCalibrationFitResult:
    slope: float
    intercept: float
    prefactor: float
    r_squared: float
    measured_peak_positions: np.ndarray
    particle_diameters_nm: np.ndarray
    expected_coupling_values: np.ndarray
    measured_peak_positions_log10: np.ndarray
    expected_coupling_values_log10: np.ndarray
    fitted_expected_coupling_values_log10: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "slope": float(self.slope),
            "intercept": float(self.intercept),
            "prefactor": float(self.prefactor),
            "r_squared": float(self.r_squared),
            "measured_peak_positions": self.measured_peak_positions.tolist(),
            "particle_diameters_nm": self.particle_diameters_nm.tolist(),
            "expected_coupling_values": self.expected_coupling_values.tolist(),
            "measured_peak_positions_log10": self.measured_peak_positions_log10.tolist(),
            "expected_coupling_values_log10": self.expected_coupling_values_log10.tolist(),
            "fitted_expected_coupling_values_log10": self.fitted_expected_coupling_values_log10.tolist(),
        }


class BackEnd:
    def __init__(
        self,
        *,
        fcs_file_path: str,
        detector_column: str,
    ) -> None:
        self.fcs_file_path = str(fcs_file_path)
        self.detector_column = str(detector_column)

    def load_signal(
        self,
        *,
        max_events_for_analysis: Optional[int] = None,
        require_positive_values: bool = False,
    ) -> np.ndarray:
        with FCSFile(self.fcs_file_path, writable=False) as fcs_file:
            signal = fcs_file.column_copy(self.detector_column, dtype=float)

        signal = np.asarray(signal, dtype=float).reshape(-1)
        signal = signal[np.isfinite(signal)]

        if require_positive_values:
            signal = signal[signal > 0.0]

        if max_events_for_analysis is not None:
            signal = signal[: int(max_events_for_analysis)]

        return signal

    def build_histogram(
        self,
        *,
        n_bins_for_plots: int,
        max_events_for_analysis: Optional[int] = None,
    ) -> HistogramResult:
        values = self.load_signal(
            max_events_for_analysis=max_events_for_analysis,
            require_positive_values=False,
        )

        if values.size == 0:
            raise ValueError("No signal values available to build histogram.")

        counts, edges = np.histogram(values, bins=int(n_bins_for_plots))
        centers = 0.5 * (edges[:-1] + edges[1:])

        return HistogramResult(
            values=np.asarray(values, dtype=float),
            counts=np.asarray(counts, dtype=float),
            edges=np.asarray(edges, dtype=float),
            centers=np.asarray(centers, dtype=float),
        )

    def build_histogram_figure(
        self,
        *,
        histogram_result: HistogramResult,
        use_log_counts: bool = False,
        peak_positions: Optional[np.ndarray] = None,
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Bar(
                x=histogram_result.centers,
                y=histogram_result.counts,
                name="signal",
            )
        )

        for peak_position in np.asarray(peak_positions if peak_positions is not None else [], dtype=float):
            figure.add_vline(
                x=float(peak_position),
                line_width=2,
                line_dash="dash",
            )

        figure.update_layout(
            xaxis_title=f"{self.detector_column} [a.u.]",
            yaxis_title="Count",
            hovermode="closest",
            separators=".,",
            bargap=0.0,
        )
        figure.update_yaxes(type="log" if bool(use_log_counts) else "linear")

        return figure

    def find_histogram_peaks(
        self,
        *,
        histogram_result: HistogramResult,
        peak_count: int,
        minimum_peak_prominence_fraction: float = 0.03,
        minimum_peak_distance_bins: int = 5,
    ) -> PeakDetectionResult:
        counts = np.asarray(histogram_result.counts, dtype=float)
        centers = np.asarray(histogram_result.centers, dtype=float)

        if counts.size == 0:
            raise ValueError("Histogram counts are empty.")

        if peak_count < 1:
            raise ValueError("peak_count must be at least 1.")

        maximum_count = float(np.max(counts))
        if maximum_count <= 0.0:
            raise ValueError("Histogram contains no positive counts.")

        prominence_threshold = maximum_count * float(minimum_peak_prominence_fraction)

        peak_indices, peak_properties = find_peaks(
            counts,
            prominence=prominence_threshold,
            distance=int(minimum_peak_distance_bins),
        )

        if peak_indices.size == 0:
            raise ValueError("No peaks were detected in the scattering histogram.")

        peak_heights = counts[peak_indices]
        sort_indices = np.argsort(peak_heights)[::-1]
        peak_indices = peak_indices[sort_indices][: int(peak_count)]
        peak_heights = peak_heights[sort_indices][: int(peak_count)]

        peak_positions = centers[peak_indices]

        order_by_position = np.argsort(peak_positions)
        peak_indices = peak_indices[order_by_position]
        peak_heights = peak_heights[order_by_position]
        peak_positions = peak_positions[order_by_position]

        return PeakDetectionResult(
            peak_indices=np.asarray(peak_indices, dtype=int),
            peak_positions=np.asarray(peak_positions, dtype=float),
            peak_heights=np.asarray(peak_heights, dtype=float),
        )

    def compute_modeled_coupling_from_diameters(
        self,
        *,
        particle_diameters_nm: np.ndarray,
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        medium_refractive_index: float,
        particle_refractive_index: float,
        detector_cache_numerical_aperture: Optional[float] = None,
        detector_rotation_degree: float = 0.0,
        detector_phi_offset_degree: float = 0.0,
        detector_gamma_offset_degree: float = 0.0,
        polarization_angle_degree: float = 0.0,
        detector_sampling: int = 600,
    ) -> ModeledCouplingResult:
        particle_diameters_nm = np.asarray(particle_diameters_nm, dtype=float).reshape(-1)
        particle_diameters_nm = particle_diameters_nm[np.isfinite(particle_diameters_nm)]
        particle_diameters_nm = particle_diameters_nm[particle_diameters_nm > 0.0]

        if particle_diameters_nm.size == 0:
            raise ValueError("No valid positive particle diameters were provided.")

        resolved_detector_cache_numerical_aperture = (
            float(detector_numerical_aperture)
            if detector_cache_numerical_aperture is None
            else float(detector_cache_numerical_aperture)
        )

        polarization_set = PolarizationSet(
            angles=[float(polarization_angle_degree)] * ureg.degree,
        )

        source_set = GaussianSet(
            wavelength=[float(wavelength_nm)] * ureg.nanometer,
            polarization=polarization_set,
            optical_power=[float(optical_power_watt)] * ureg.watt,
            numerical_aperture=[float(source_numerical_aperture)],
        )

        scatterer_set = SphereSet(
            diameter=particle_diameters_nm * ureg.nanometer,
            material=[complex(float(particle_refractive_index), 0.0)],
            medium=[float(medium_refractive_index)],
        )

        detector_set = PhotodiodeSet(
            numerical_aperture=[float(detector_numerical_aperture)],
            cache_numerical_aperture=[resolved_detector_cache_numerical_aperture],
            rotation=[float(detector_rotation_degree)] * ureg.degree,
            phi_offset=[float(detector_phi_offset_degree)] * ureg.degree,
            gamma_offset=[float(detector_gamma_offset_degree)] * ureg.degree,
            sampling=[int(detector_sampling)],
        )

        experiment = Setup(
            scatterer_set=scatterer_set,
            source_set=source_set,
            detector_set=detector_set,
        )

        coupling_values = experiment.get("coupling", as_numpy=True).squeeze()
        coupling_values = np.asarray(coupling_values, dtype=float).reshape(-1)

        if coupling_values.size != particle_diameters_nm.size:
            raise ValueError(
                "Modeled coupling result size does not match the provided particle diameter size."
            )

        model_metadata = {
            "wavelength_nm": float(wavelength_nm),
            "source_numerical_aperture": float(source_numerical_aperture),
            "optical_power_watt": float(optical_power_watt),
            "detector_numerical_aperture": float(detector_numerical_aperture),
            "detector_cache_numerical_aperture": float(resolved_detector_cache_numerical_aperture),
            "detector_rotation_degree": float(detector_rotation_degree),
            "detector_phi_offset_degree": float(detector_phi_offset_degree),
            "detector_gamma_offset_degree": float(detector_gamma_offset_degree),
            "polarization_angle_degree": float(polarization_angle_degree),
            "detector_sampling": int(detector_sampling),
            "medium_refractive_index": float(medium_refractive_index),
            "particle_refractive_index": float(particle_refractive_index),
        }

        return ModeledCouplingResult(
            particle_diameters_nm=particle_diameters_nm,
            expected_coupling_values=np.asarray(coupling_values, dtype=float),
            model_metadata=model_metadata,
        )

    def fit_measured_peak_positions_to_modeled_coupling(
        self,
        *,
        measured_peak_positions: np.ndarray,
        modeled_coupling_result: ModeledCouplingResult,
    ) -> ScatteringCalibrationFitResult:
        measured_peak_positions = np.asarray(measured_peak_positions, dtype=float).reshape(-1)
        measured_peak_positions = measured_peak_positions[np.isfinite(measured_peak_positions)]
        measured_peak_positions = measured_peak_positions[measured_peak_positions > 0.0]

        particle_diameters_nm = np.asarray(
            modeled_coupling_result.particle_diameters_nm,
            dtype=float,
        ).reshape(-1)
        expected_coupling_values = np.asarray(
            modeled_coupling_result.expected_coupling_values,
            dtype=float,
        ).reshape(-1)

        finite_mask = np.isfinite(expected_coupling_values) & (expected_coupling_values > 0.0)
        particle_diameters_nm = particle_diameters_nm[finite_mask]
        expected_coupling_values = expected_coupling_values[finite_mask]

        if measured_peak_positions.size != expected_coupling_values.size:
            raise ValueError(
                "The number of measured peak positions must match the number of modeled coupling values."
            )

        if measured_peak_positions.size < 2:
            raise ValueError("Need at least 2 peaks to fit the scattering calibration.")

        measured_peak_positions_log10 = np.log10(measured_peak_positions)
        expected_coupling_values_log10 = np.log10(expected_coupling_values)

        slope, intercept = np.polyfit(
            measured_peak_positions_log10,
            expected_coupling_values_log10,
            1,
        )

        fitted_expected_coupling_values_log10 = (
            slope * measured_peak_positions_log10 + intercept
        )
        r_squared = self._compute_r_squared(
            y_true=expected_coupling_values_log10,
            y_pred=fitted_expected_coupling_values_log10,
        )
        prefactor = 10.0 ** float(intercept)

        return ScatteringCalibrationFitResult(
            slope=float(slope),
            intercept=float(intercept),
            prefactor=float(prefactor),
            r_squared=float(r_squared),
            measured_peak_positions=measured_peak_positions,
            particle_diameters_nm=particle_diameters_nm,
            expected_coupling_values=expected_coupling_values,
            measured_peak_positions_log10=measured_peak_positions_log10,
            expected_coupling_values_log10=expected_coupling_values_log10,
            fitted_expected_coupling_values_log10=fitted_expected_coupling_values_log10,
        )

    def build_calibration_figure(
        self,
        *,
        fit_result: ScatteringCalibrationFitResult,
    ) -> go.Figure:
        measured_peak_positions_log10_fit = np.linspace(
            float(np.min(fit_result.measured_peak_positions_log10)),
            float(np.max(fit_result.measured_peak_positions_log10)),
            200,
        )
        expected_coupling_values_log10_fit = (
            fit_result.slope * measured_peak_positions_log10_fit + fit_result.intercept
        )

        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=fit_result.measured_peak_positions_log10,
                y=fit_result.expected_coupling_values_log10,
                mode="markers",
                name="modeled reference points",
            )
        )

        figure.add_trace(
            go.Scatter(
                x=measured_peak_positions_log10_fit,
                y=expected_coupling_values_log10_fit,
                mode="lines",
                name="fit",
            )
        )

        figure.update_layout(
            xaxis_title=f"log10({self.detector_column} peak position [a.u.])",
            yaxis_title="log10(Expected coupling)",
            hovermode="closest",
            separators=".,",
        )

        return figure

    def build_calibration_payload(
        self,
        *,
        peak_detection_result: PeakDetectionResult,
        modeled_coupling_result: ModeledCouplingResult,
        fit_result: ScatteringCalibrationFitResult,
        notes: str = "",
    ) -> dict[str, Any]:
        reference_points = []

        for measured_peak_position, particle_diameter_nm, expected_coupling_value in zip(
            fit_result.measured_peak_positions,
            fit_result.particle_diameters_nm,
            fit_result.expected_coupling_values,
            strict=False,
        ):
            reference_points.append(
                {
                    "particle_diameter_nm": float(particle_diameter_nm),
                    "measured_peak_position": float(measured_peak_position),
                    "expected_coupling_value": float(expected_coupling_value),
                }
            )

        return {
            "schema": "rosettax_calibration_v1",
            "created_at": "",
            "kind": "scattering",
            "name": "",
            "payload": {
                "schema_version": "1.0",
                "calibration_type": "scattering",
                "created_at": "",
                "name": "",
                "source_file": Path(self.fcs_file_path).name,
                "source_channel": self.detector_column,
                "fit_model": "log10(expected_coupling)=slope*log10(measured_peak_position)+intercept",
                "fit_metrics": {
                    "r_squared": float(fit_result.r_squared),
                    "point_count": int(fit_result.measured_peak_positions.size),
                },
                "parameters": {
                    "slope": float(fit_result.slope),
                    "intercept": float(fit_result.intercept),
                    "prefactor": float(fit_result.prefactor),
                },
                "peak_positions": peak_detection_result.peak_positions.tolist(),
                "particle_diameters_nm": fit_result.particle_diameters_nm.tolist(),
                "expected_coupling_values": fit_result.expected_coupling_values.tolist(),
                "model_metadata": modeled_coupling_result.model_metadata,
                "reference_points": reference_points,
                "export_notes": str(notes),
                "payload": {
                    "slope": float(fit_result.slope),
                    "intercept": float(fit_result.intercept),
                    "prefactor": float(fit_result.prefactor),
                    "R_squared": float(fit_result.r_squared),
                    "model": "log10(expected_coupling)=slope*log10(measured_peak_position)+intercept",
                    "x_definition": f"{self.detector_column} peak position [a.u.]",
                    "y_definition": "Expected coupling",
                },
            },
        }

    @staticmethod
    def parse_particle_diameter_list(particle_diameter_list_text: str) -> np.ndarray:
        if particle_diameter_list_text is None:
            return np.asarray([], dtype=float)

        sanitized_text = str(particle_diameter_list_text).replace(";", ",")
        raw_parts = [part.strip() for part in sanitized_text.split(",")]

        particle_diameters_nm: list[float] = []

        for raw_part in raw_parts:
            if not raw_part:
                continue

            particle_diameters_nm.append(float(raw_part))

        return np.asarray(particle_diameters_nm, dtype=float)

    @staticmethod
    def _compute_r_squared(*, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        mask = np.isfinite(y_true) & np.isfinite(y_pred)
        y_true = y_true[mask]
        y_pred = y_pred[mask]

        if y_true.size < 2:
            return float("nan")

        residual_sum_of_squares = float(np.sum((y_true - y_pred) ** 2))
        total_sum_of_squares = float(np.sum((y_true - float(np.mean(y_true))) ** 2))

        if total_sum_of_squares <= 0.0:
            return float("nan")

        return 1.0 - residual_sum_of_squares / total_sum_of_squares