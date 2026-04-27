# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging
import time

import numpy as np

from PyMieSim.units import ureg
from PyMieSim.experiment.detector_set import PhotodiodeSet
from PyMieSim.experiment.scatterer_set import SphereSet
from PyMieSim.experiment.source_set import GaussianSet
from PyMieSim.experiment.polarization_set import PolarizationSet
from PyMieSim.experiment import Setup


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModeledCouplingResult:
    """
    Container for modeled scattering coupling values.
    """

    particle_diameters_nm: np.ndarray
    expected_coupling_values: np.ndarray
    model_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the modeled coupling result to a JSON safe dictionary.
        """
        return {
            "particle_diameters_nm": self.particle_diameters_nm.tolist(),
            "expected_coupling_values": self.expected_coupling_values.tolist(),
            "model_metadata": self.model_metadata,
        }


@dataclass(frozen=True)
class ScatteringCalibrationFitResult:
    """
    Container for the scattering calibration fit.
    """

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
        """
        Convert the fit result to a JSON safe dictionary.
        """
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
    Numerical backend for the scattering calibration page.

    Responsibilities
    ----------------
    - Read detector columns from the uploaded FCS file.
    - Build signal histograms.
    - Build histogram figures.
    - Compute modeled scattering coupling values with PyMieSim.
    - Fit measured peak positions to modeled coupling values.
    - Build calibration fit figures.
    - Build serialized scattering calibration payloads.

    Non responsibilities
    --------------------
    - This backend does not perform peak detection.
    - This backend does not execute peak scripts.
    - This backend does not own manual peak selection behavior.

    Peak detection and manual peak selection are owned by the shared peak workflow
    layer. The scattering backend only consumes the resulting peak positions.
    """

    def __init__(self) -> None:

        logger.debug(
            "Initialized Scattering BackEnd with fcs_file_path=%r",
        )

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

        particle_diameters_nm = BackEnd._sanitize_positive_float_array(
            particle_diameters_nm,
            require_positive_values=True,
        )

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

        def run_coupling_simulation(simulation_sampling: int) -> np.ndarray:
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
            coupling_values = run_coupling_simulation(int(detector_sampling))
        except Exception:
            logger.exception(
                "Primary coupling computation failed with detector_sampling=%r. Retrying with a smaller sampling value.",
                detector_sampling,
            )

            fallback_sampling = max(50, min(200, int(detector_sampling)))

            if fallback_sampling == int(detector_sampling):
                fallback_sampling = 100

            coupling_values = run_coupling_simulation(fallback_sampling)

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


    @staticmethod
    def parse_particle_diameter_list(particle_diameter_list_text: str) -> np.ndarray:
        """
        Parse a comma or semicolon separated particle diameter list.
        """
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
    def _extract_peak_positions_from_result(peak_detection_result: Any) -> np.ndarray:
        """
        Extract peak positions from a shared peak workflow result.

        Supported forms
        ---------------
        - Object with ``peak_positions`` attribute.
        - Dictionary with ``peak_positions`` key.
        - Raw array like object.
        """
        if peak_detection_result is None:
            return np.asarray([], dtype=float)

        if isinstance(peak_detection_result, dict):
            raw_peak_positions = peak_detection_result.get("peak_positions", [])
        elif hasattr(peak_detection_result, "peak_positions"):
            raw_peak_positions = peak_detection_result.peak_positions
        else:
            raw_peak_positions = peak_detection_result

        return BackEnd._sanitize_positive_float_array(
            raw_peak_positions,
            require_positive_values=False,
        )

    @staticmethod
    def _sanitize_positive_float_array(
        values: Any,
        *,
        require_positive_values: bool,
    ) -> np.ndarray:
        """
        Convert input values to a finite float array.

        Parameters
        ----------
        values:
            Input array like object.
        require_positive_values:
            If true, remove values smaller than or equal to zero.
        """
        values = np.asarray(values, dtype=float).reshape(-1)
        values = values[np.isfinite(values)]

        if require_positive_values:
            values = values[values > 0.0]

        return values

    @staticmethod
    def _compute_r_squared(
        *,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> float:
        """
        Compute the coefficient of determination.
        """
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