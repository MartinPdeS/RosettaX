# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils.peak_detection import PeakDetectionResult, find_1d_signal_peaks
from RosettaX.utils.reader import FCSFile

from PyMieSim.units import ureg
from PyMieSim.experiment.detector_set import PhotodiodeSet
from PyMieSim.experiment.scatterer_set import SphereSet
from PyMieSim.experiment.source_set import GaussianSet
from PyMieSim.experiment.polarization_set import PolarizationSet
from PyMieSim.experiment import Setup


logger = logging.getLogger(__name__)


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
    """
    Numerical backend for scattering histogram construction, peak detection,
    modeled coupling computation, and calibration fitting.

    Design
    ------
    This backend is file bound, not detector bound.

    The FCS file is the stable context owned by the upload section.
    The selected detector column is UI state and is therefore passed explicitly
    to the methods that need it.
    """

    def __init__(
        self,
        *,
        fcs_file_path: str,
    ) -> None:
        self.fcs_file_path = str(fcs_file_path)

        logger.debug(
            "Initialized Scattering BackEnd with fcs_file_path=%r",
            self.fcs_file_path,
        )

    def get_column_names(self) -> list[str]:
        logger.debug("get_column_names called for fcs_file_path=%r", self.fcs_file_path)

        with FCSFile(self.fcs_file_path, writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            parameter_count = int(fcs_file.text["Keywords"]["$PAR"])

            column_names = [
                str(detectors[index].get("N", f"P{index}"))
                for index in range(1, parameter_count + 1)
            ]

        logger.debug("get_column_names returning n_columns=%r", len(column_names))
        return column_names

    def load_signal(
        self,
        *,
        detector_column: str,
        max_events_for_analysis: Optional[int] = None,
        require_positive_values: bool = False,
    ) -> np.ndarray:
        """
        Load a detector signal from the FCS file.
        """
        resolved_detector_column = str(detector_column).strip()

        if not resolved_detector_column:
            raise ValueError("detector_column must be a non empty string.")

        logger.debug(
            "load_signal called with detector_column=%r max_events_for_analysis=%r require_positive_values=%r",
            resolved_detector_column,
            max_events_for_analysis,
            require_positive_values,
        )

        with FCSFile(self.fcs_file_path, writable=False) as fcs_file:
            signal = fcs_file.column_copy(resolved_detector_column, dtype=float)

        signal = np.asarray(signal, dtype=float).reshape(-1)
        signal = signal[np.isfinite(signal)]

        if require_positive_values:
            signal = signal[signal > 0.0]

        if max_events_for_analysis is not None:
            signal = signal[: int(max_events_for_analysis)]

        logger.debug(
            "load_signal returning detector_column=%r n_values=%r min=%r max=%r",
            resolved_detector_column,
            signal.size,
            None if signal.size == 0 else float(np.min(signal)),
            None if signal.size == 0 else float(np.max(signal)),
        )

        return signal

    def build_histogram(
        self,
        *,
        detector_column: str,
        n_bins_for_plots: int,
        max_events_for_analysis: Optional[int] = None,
    ) -> HistogramResult:
        """
        Build a 1D histogram from the detector signal.
        """
        resolved_detector_column = str(detector_column).strip()

        logger.debug(
            "build_histogram called with detector_column=%r n_bins_for_plots=%r max_events_for_analysis=%r",
            resolved_detector_column,
            n_bins_for_plots,
            max_events_for_analysis,
        )

        values = self.load_signal(
            detector_column=resolved_detector_column,
            max_events_for_analysis=max_events_for_analysis,
            require_positive_values=False,
        )

        if values.size == 0:
            raise ValueError("No signal values available to build histogram.")

        counts, edges = np.histogram(values, bins=int(n_bins_for_plots))
        centers = 0.5 * (edges[:-1] + edges[1:])

        histogram_result = HistogramResult(
            values=np.asarray(values, dtype=float),
            counts=np.asarray(counts, dtype=float),
            edges=np.asarray(edges, dtype=float),
            centers=np.asarray(centers, dtype=float),
        )

        logger.debug(
            "build_histogram returning detector_column=%r n_values=%r n_bins=%r nonzero_bins=%r",
            resolved_detector_column,
            histogram_result.values.size,
            histogram_result.counts.size,
            int(np.count_nonzero(histogram_result.counts)),
        )

        return histogram_result

    def build_histogram_figure(
        self,
        *,
        detector_column: str,
        histogram_result: HistogramResult,
        use_log_counts: bool = False,
        peak_positions: Optional[np.ndarray] = None,
    ) -> go.Figure:
        """
        Build a Plotly histogram figure.
        """
        resolved_detector_column = str(detector_column).strip()

        logger.debug(
            "build_histogram_figure called with detector_column=%r use_log_counts=%r peak_count=%r",
            resolved_detector_column,
            use_log_counts,
            0 if peak_positions is None else len(np.asarray(peak_positions).reshape(-1)),
        )

        figure = go.Figure()

        figure.add_trace(
            go.Bar(
                x=histogram_result.centers,
                y=histogram_result.counts,
                name="signal",
            )
        )

        for peak_position in np.asarray(
            peak_positions if peak_positions is not None else [],
            dtype=float,
        ):
            figure.add_vline(
                x=float(peak_position),
                line_width=2,
                line_dash="dash",
            )

        figure.update_layout(
            xaxis_title=f"{resolved_detector_column} [a.u.]",
            yaxis_title="Count",
            hovermode="closest",
            separators=".,",
            bargap=0.0,
        )
        figure.update_yaxes(type="log" if bool(use_log_counts) else "linear")

        return figure

    def find_scattering_peaks(
        self,
        *,
        detector_column: str,
        max_peaks: int,
        min_cluster_size: int = 100,
        threshold: float = 0.0,
        max_events_for_analysis: Optional[int] = None,
        debug: bool = False,
    ) -> PeakDetectionResult:
        """
        Detect peaks in the 1D detector signal.
        """
        resolved_detector_column = str(detector_column).strip()

        logger.debug(
            "find_scattering_peaks called with detector_column=%r max_peaks=%r min_cluster_size=%r threshold=%r max_events_for_analysis=%r debug=%r",
            resolved_detector_column,
            max_peaks,
            min_cluster_size,
            threshold,
            max_events_for_analysis,
            debug,
        )

        values = self.load_signal(
            detector_column=resolved_detector_column,
            max_events_for_analysis=max_events_for_analysis,
            require_positive_values=False,
        )

        peak_detection_result = find_1d_signal_peaks(
            values=values,
            max_peaks=max_peaks,
            min_cluster_size=min_cluster_size,
            threshold=threshold,
            debug=debug,
        )

        logger.debug(
            "find_scattering_peaks returning detector_column=%r peak_positions=%r",
            resolved_detector_column,
            peak_detection_result.peak_positions.tolist(),
        )

        return peak_detection_result

    @staticmethod
    def compute_modeled_coupling_from_diameters(
        particle_diameters_nm: np.ndarray,
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        medium_refractive_index: float,
        particle_refractive_index: float,
        detector_cache_numerical_aperture: Optional[float] = None,
        detector_phi_offset_degree: float = 0.0,
        detector_gamma_offset_degree: float = 0.0,
        polarization_angle_degree: float = 0.0,
        detector_sampling: int = 600,
    ) -> ModeledCouplingResult:
        """
        Compute modeled coupling values for a list of particle diameters.
        """
        import time

        logger.debug(
            "compute_modeled_coupling_from_diameters called with particle_diameters_nm=%r wavelength_nm=%r source_numerical_aperture=%r optical_power_watt=%r detector_numerical_aperture=%r medium_refractive_index=%r particle_refractive_index=%r detector_cache_numerical_aperture=%r detector_phi_offset_degree=%r detector_gamma_offset_degree=%r polarization_angle_degree=%r detector_sampling=%r",
            np.asarray(particle_diameters_nm).tolist(),
            wavelength_nm,
            source_numerical_aperture,
            optical_power_watt,
            detector_numerical_aperture,
            medium_refractive_index,
            particle_refractive_index,
            detector_cache_numerical_aperture,
            detector_phi_offset_degree,
            detector_gamma_offset_degree,
            polarization_angle_degree,
            detector_sampling,
        )

        particle_diameters_nm = np.asarray(particle_diameters_nm, dtype=float).reshape(-1)
        particle_diameters_nm = particle_diameters_nm[np.isfinite(particle_diameters_nm)]
        particle_diameters_nm = particle_diameters_nm[particle_diameters_nm > 0.0]

        logger.debug("Sanitized particle_diameters_nm=%r", particle_diameters_nm.tolist())

        if particle_diameters_nm.size == 0:
            raise ValueError("No valid positive particle diameters were provided.")

        resolved_detector_cache_numerical_aperture = (
            float(detector_numerical_aperture)
            if detector_cache_numerical_aperture is None
            else float(detector_cache_numerical_aperture)
        )

        logger.debug(
            "Resolved detector cache numerical aperture=%r",
            resolved_detector_cache_numerical_aperture,
        )

        def _run_coupling(simulation_sampling: int) -> np.ndarray:
            logger.debug("Building PolarizationSet with sampling=%r.", simulation_sampling)
            polarization_set = PolarizationSet(
                angles=[float(polarization_angle_degree)] * ureg.degree,
            )

            logger.debug("Building GaussianSet.")
            source_set = GaussianSet(
                wavelength=[float(wavelength_nm)] * ureg.nanometer,
                polarization=polarization_set,
                optical_power=[float(optical_power_watt)] * ureg.watt,
                numerical_aperture=[float(source_numerical_aperture)],
            )

            logger.debug("Building SphereSet.")
            scatterer_set = SphereSet(
                diameter=particle_diameters_nm * ureg.nanometer,
                material=[complex(float(particle_refractive_index), 0.0)],
                medium=[float(medium_refractive_index)],
            )

            logger.debug("Building PhotodiodeSet.")
            detector_set = PhotodiodeSet(
                numerical_aperture=[float(detector_numerical_aperture)],
                cache_numerical_aperture=[resolved_detector_cache_numerical_aperture],
                phi_offset=[float(detector_phi_offset_degree)] * ureg.degree,
                gamma_offset=[float(detector_gamma_offset_degree)] * ureg.degree,
                sampling=[int(simulation_sampling)],
            )

            logger.debug("Building Setup.")
            experiment = Setup(
                scatterer_set=scatterer_set,
                source_set=source_set,
                detector_set=detector_set,
            )

            logger.debug(
                "Calling experiment.get('coupling', as_numpy=True) with sampling=%r.",
                simulation_sampling,
            )
            start_time = time.perf_counter()
            coupling_values = experiment.get("coupling", as_numpy=True)
            elapsed_time = time.perf_counter() - start_time

            logger.debug(
                "experiment.get('coupling') returned after %.3f s with raw type=%s value=%r",
                elapsed_time,
                type(coupling_values).__name__,
                coupling_values,
            )

            coupling_values = np.asarray(coupling_values).squeeze()
            logger.debug(
                "Coupling after squeeze type=%s shape=%r dtype=%r",
                type(coupling_values).__name__,
                getattr(coupling_values, "shape", None),
                getattr(coupling_values, "dtype", None),
            )

            coupling_values = np.real_if_close(coupling_values, tol=1000)
            coupling_values = np.asarray(coupling_values, dtype=float).reshape(-1)

            logger.debug(
                "Processed coupling values with sampling=%r => %r",
                simulation_sampling,
                coupling_values.tolist(),
            )

            return coupling_values

        try:
            coupling_values = _run_coupling(int(detector_sampling))
        except Exception:
            logger.exception(
                "Primary coupling computation failed with detector_sampling=%r. Retrying with a smaller sampling value.",
                detector_sampling,
            )

            fallback_sampling = max(50, min(200, int(detector_sampling)))
            if fallback_sampling == int(detector_sampling):
                fallback_sampling = 100

            coupling_values = _run_coupling(fallback_sampling)

        if coupling_values.size != particle_diameters_nm.size:
            raise ValueError(
                "Modeled coupling result size does not match the provided particle diameter size. "
                f"Got {coupling_values.size} modeled values for {particle_diameters_nm.size} diameters."
            )

        model_metadata = {
            "wavelength_nm": float(wavelength_nm),
            "source_numerical_aperture": float(source_numerical_aperture),
            "optical_power_watt": float(optical_power_watt),
            "detector_numerical_aperture": float(detector_numerical_aperture),
            "detector_cache_numerical_aperture": float(resolved_detector_cache_numerical_aperture),
            "detector_phi_offset_degree": float(detector_phi_offset_degree),
            "detector_gamma_offset_degree": float(detector_gamma_offset_degree),
            "polarization_angle_degree": float(polarization_angle_degree),
            "detector_sampling": int(detector_sampling),
            "medium_refractive_index": float(medium_refractive_index),
            "particle_refractive_index": float(particle_refractive_index),
        }

        modeled_coupling_result = ModeledCouplingResult(
            particle_diameters_nm=particle_diameters_nm,
            expected_coupling_values=coupling_values,
            model_metadata=model_metadata,
        )

        logger.debug(
            "compute_modeled_coupling_from_diameters returning expected_coupling_values=%r",
            modeled_coupling_result.expected_coupling_values.tolist(),
        )

        return modeled_coupling_result

    def fit_measured_peak_positions_to_modeled_coupling(
        self,
        *,
        measured_peak_positions: np.ndarray,
        modeled_coupling_result: ModeledCouplingResult,
    ) -> ScatteringCalibrationFitResult:
        """
        Fit a log10 to log10 calibration model between measured peak positions
        and expected coupling values.
        """
        logger.debug(
            "fit_measured_peak_positions_to_modeled_coupling called with measured_peak_positions=%r modeled_particle_diameters_nm=%r modeled_expected_coupling_values=%r",
            np.asarray(measured_peak_positions).tolist(),
            modeled_coupling_result.particle_diameters_nm.tolist(),
            modeled_coupling_result.expected_coupling_values.tolist(),
        )

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

        fit_result = ScatteringCalibrationFitResult(
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

        logger.debug(
            "fit_measured_peak_positions_to_modeled_coupling returning slope=%r intercept=%r prefactor=%r r_squared=%r",
            fit_result.slope,
            fit_result.intercept,
            fit_result.prefactor,
            fit_result.r_squared,
        )

        return fit_result

    def build_calibration_figure(
        self,
        *,
        detector_column: str,
        fit_result: ScatteringCalibrationFitResult,
    ) -> go.Figure:
        """
        Build the calibration fit figure.
        """
        resolved_detector_column = str(detector_column).strip()

        logger.debug(
            "build_calibration_figure called with detector_column=%r n_points=%r",
            resolved_detector_column,
            fit_result.measured_peak_positions.size,
        )

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
            xaxis_title=f"log10({resolved_detector_column} peak position [a.u.])",
            yaxis_title="log10(Expected coupling)",
            hovermode="closest",
            separators=".,",
        )

        return figure

    def build_calibration_payload(
        self,
        *,
        detector_column: str,
        peak_detection_result: PeakDetectionResult,
        modeled_coupling_result: ModeledCouplingResult,
        fit_result: ScatteringCalibrationFitResult,
        notes: str = "",
    ) -> dict[str, Any]:
        """
        Build the serialized calibration payload.
        """
        resolved_detector_column = str(detector_column).strip()

        logger.debug(
            "build_calibration_payload called with detector_column=%r n_reference_points=%r",
            resolved_detector_column,
            fit_result.measured_peak_positions.size,
        )

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

        payload = {
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
                "source_channel": resolved_detector_column,
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
                    "x_definition": f"{resolved_detector_column} peak position [a.u.]",
                    "y_definition": "Expected coupling",
                },
            },
        }

        logger.debug(
            "build_calibration_payload returning payload keys=%r",
            list(payload.keys()),
        )

        return payload

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