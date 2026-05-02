# -*- coding: utf-8 -*-

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Optional
import logging
import time

import numpy as np

from PyMieSim.units import ureg
from PyMieSim import experiment as PyMieSim


logger = logging.getLogger(__name__)


SOLID_SPHERE_MODEL_NAME = "Solid Sphere"
CORE_SHELL_SPHERE_MODEL_NAME = "Core/Shell Sphere"


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
        logger.debug("Initialized Scattering BackEnd.")

    @staticmethod
    def _summarize_numeric_array(
        values: Any,
        *,
        preview_count: int = 5,
    ) -> dict[str, Any]:
        """
        Return a compact debug summary for numeric arrays.
        """
        array = np.asarray(values, dtype=float).reshape(-1)
        finite_array = array[np.isfinite(array)]

        return {
            "size": int(array.size),
            "finite_size": int(finite_array.size),
            "min": None if finite_array.size == 0 else float(np.min(finite_array)),
            "max": None if finite_array.size == 0 else float(np.max(finite_array)),
            "preview": finite_array[:preview_count].tolist(),
        }

    @staticmethod
    def compute_modeled_coupling(
        *,
        mie_model: str,
        particle_diameters_nm: Optional[np.ndarray] = None,
        core_diameters_nm: Optional[np.ndarray] = None,
        shell_thicknesses_nm: Optional[np.ndarray] = None,
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        medium_refractive_index: float,
        particle_refractive_index: Optional[float] = None,
        core_refractive_index: Optional[float] = None,
        shell_refractive_index: Optional[float] = None,
        detector_cache_numerical_aperture: Optional[float] = None,
        detector_phi_offset_degree: float = 0.0,
        detector_gamma_offset_degree: float = 0.0,
        polarization_angle_degree: float = 0.0,
        detector_sampling: int = 600,
    ) -> ModeledCouplingResult:
        """
        Compute modeled coupling values for the selected Mie scatterer model.

        Parameters
        ----------
        mie_model:
            Scattering model name. Supported values are ``Solid Sphere`` and
            ``Core/Shell Sphere``.

        particle_diameters_nm:
            Solid sphere diameters in nanometers.

        core_diameters_nm:
            Core diameters in nanometers for the core shell model.

        shell_thicknesses_nm:
            Shell thicknesses in nanometers for the core shell model.
        """
        resolved_mie_model = BackEnd._normalize_mie_model(mie_model)

        logger.debug(
            "compute_modeled_coupling called with mie_model=%r particle_diameters_nm=%r core_diameters_nm=%r shell_thicknesses_nm=%r wavelength_nm=%r source_numerical_aperture=%r optical_power_watt=%r detector_numerical_aperture=%r medium_refractive_index=%r particle_refractive_index=%r core_refractive_index=%r shell_refractive_index=%r detector_cache_numerical_aperture=%r detector_phi_offset_degree=%r detector_gamma_offset_degree=%r polarization_angle_degree=%r detector_sampling=%r",
            resolved_mie_model,
            None
            if particle_diameters_nm is None
            else BackEnd._summarize_numeric_array(particle_diameters_nm),
            None
            if core_diameters_nm is None
            else BackEnd._summarize_numeric_array(core_diameters_nm),
            None
            if shell_thicknesses_nm is None
            else BackEnd._summarize_numeric_array(shell_thicknesses_nm),
            wavelength_nm,
            source_numerical_aperture,
            optical_power_watt,
            detector_numerical_aperture,
            medium_refractive_index,
            particle_refractive_index,
            core_refractive_index,
            shell_refractive_index,
            detector_cache_numerical_aperture,
            detector_phi_offset_degree,
            detector_gamma_offset_degree,
            polarization_angle_degree,
            detector_sampling,
        )

        if resolved_mie_model == SOLID_SPHERE_MODEL_NAME:
            if particle_diameters_nm is None:
                raise ValueError("particle_diameters_nm must be provided for the Solid Sphere model.")

            if particle_refractive_index is None:
                raise ValueError("particle_refractive_index must be provided for the Solid Sphere model.")

            return BackEnd.compute_modeled_coupling_from_diameters(
                particle_diameters_nm=particle_diameters_nm,
                wavelength_nm=wavelength_nm,
                source_numerical_aperture=source_numerical_aperture,
                optical_power_watt=optical_power_watt,
                detector_numerical_aperture=detector_numerical_aperture,
                medium_refractive_index=medium_refractive_index,
                particle_refractive_index=particle_refractive_index,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                detector_phi_offset_degree=detector_phi_offset_degree,
                detector_gamma_offset_degree=detector_gamma_offset_degree,
                polarization_angle_degree=polarization_angle_degree,
                detector_sampling=detector_sampling,
            )

        if resolved_mie_model == CORE_SHELL_SPHERE_MODEL_NAME:
            if core_diameters_nm is None:
                raise ValueError("core_diameters_nm must be provided for the Core/Shell Sphere model.")

            if shell_thicknesses_nm is None:
                raise ValueError("shell_thicknesses_nm must be provided for the Core/Shell Sphere model.")

            if core_refractive_index is None:
                raise ValueError("core_refractive_index must be provided for the Core/Shell Sphere model.")

            if shell_refractive_index is None:
                raise ValueError("shell_refractive_index must be provided for the Core/Shell Sphere model.")

            return BackEnd.compute_modeled_coupling_from_core_shell_dimensions(
                core_diameters_nm=core_diameters_nm,
                shell_thicknesses_nm=shell_thicknesses_nm,
                wavelength_nm=wavelength_nm,
                source_numerical_aperture=source_numerical_aperture,
                optical_power_watt=optical_power_watt,
                detector_numerical_aperture=detector_numerical_aperture,
                medium_refractive_index=medium_refractive_index,
                core_refractive_index=core_refractive_index,
                shell_refractive_index=shell_refractive_index,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                detector_phi_offset_degree=detector_phi_offset_degree,
                detector_gamma_offset_degree=detector_gamma_offset_degree,
                polarization_angle_degree=polarization_angle_degree,
                detector_sampling=detector_sampling,
            )

        raise ValueError(f"Unsupported scattering model: {mie_model!r}")

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
        Compute modeled coupling values for solid sphere particle diameters.
        """
        logger.debug(
            "compute_modeled_coupling_from_diameters called with particle_diameters_nm=%r wavelength_nm=%r source_numerical_aperture=%r optical_power_watt=%r detector_numerical_aperture=%r medium_refractive_index=%r particle_refractive_index=%r detector_cache_numerical_aperture=%r detector_phi_offset_degree=%r detector_gamma_offset_degree=%r polarization_angle_degree=%r detector_sampling=%r",
            BackEnd._summarize_numeric_array(particle_diameters_nm),
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

        logger.debug(
            "Sanitized particle_diameters_nm=%r",
            BackEnd._summarize_numeric_array(particle_diameters_nm),
        )

        if particle_diameters_nm.size == 0:
            raise ValueError("No valid positive particle diameters were provided.")

        resolved_detector_cache_numerical_aperture = BackEnd._resolve_detector_cache_numerical_aperture(
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        )

        logger.debug(
            "Resolved detector cache numerical aperture=%r",
            resolved_detector_cache_numerical_aperture,
        )

        coupling_values = np.asarray(
            BackEnd._compute_cached_solid_sphere_coupling(
                particle_diameters_nm=tuple(float(value) for value in particle_diameters_nm.tolist()),
                wavelength_nm=float(wavelength_nm),
                source_numerical_aperture=float(source_numerical_aperture),
                optical_power_watt=float(optical_power_watt),
                detector_numerical_aperture=float(detector_numerical_aperture),
                medium_refractive_index=float(medium_refractive_index),
                particle_refractive_index=float(particle_refractive_index),
                detector_cache_numerical_aperture=float(resolved_detector_cache_numerical_aperture),
                detector_phi_offset_degree=float(detector_phi_offset_degree),
                detector_gamma_offset_degree=float(detector_gamma_offset_degree),
                polarization_angle_degree=float(polarization_angle_degree),
                detector_sampling=int(detector_sampling),
            ),
            dtype=float,
        )

        BackEnd._validate_coupling_size(
            coupling_values=coupling_values,
            expected_size=particle_diameters_nm.size,
            size_context="particle diameter",
        )

        model_metadata = {
            "mie_model": SOLID_SPHERE_MODEL_NAME,
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
            BackEnd._summarize_numeric_array(modeled_coupling_result.expected_coupling_values),
        )

        return modeled_coupling_result

    @staticmethod
    @lru_cache(maxsize=32)
    def _compute_cached_solid_sphere_coupling(
        *,
        particle_diameters_nm: tuple[float, ...],
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        medium_refractive_index: float,
        particle_refractive_index: float,
        detector_cache_numerical_aperture: float,
        detector_phi_offset_degree: float,
        detector_gamma_offset_degree: float,
        polarization_angle_degree: float,
        detector_sampling: int,
    ) -> tuple[float, ...]:
        """
        Cache solid-sphere coupling computations for deterministic inputs.
        """
        particle_diameter_array = np.asarray(particle_diameters_nm, dtype=float)

        def build_solid_sphere_scatterer_set() -> Any:
            logger.debug("Building cached SphereSet.")

            return PyMieSim.scatterer_set.SphereSet(
                diameter=particle_diameter_array * ureg.nanometer,
                material=[complex(float(particle_refractive_index), 0.0)],
                medium=[float(medium_refractive_index)],
            )

        coupling_values = BackEnd._compute_coupling_values_with_fallback(
            scatterer_set_builder=build_solid_sphere_scatterer_set,
            wavelength_nm=wavelength_nm,
            source_numerical_aperture=source_numerical_aperture,
            optical_power_watt=optical_power_watt,
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            detector_phi_offset_degree=detector_phi_offset_degree,
            detector_gamma_offset_degree=detector_gamma_offset_degree,
            polarization_angle_degree=polarization_angle_degree,
            detector_sampling=detector_sampling,
        )

        return tuple(float(value) for value in np.asarray(coupling_values, dtype=float).reshape(-1))

    @staticmethod
    def compute_modeled_coupling_from_core_shell_dimensions(
        core_diameters_nm: np.ndarray,
        shell_thicknesses_nm: np.ndarray,
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        medium_refractive_index: float,
        core_refractive_index: float,
        shell_refractive_index: float,
        detector_cache_numerical_aperture: Optional[float] = None,
        detector_phi_offset_degree: float = 0.0,
        detector_gamma_offset_degree: float = 0.0,
        polarization_angle_degree: float = 0.0,
        detector_sampling: int = 600,
    ) -> ModeledCouplingResult:
        """
        Compute modeled coupling values for paired core shell sphere rows.

        PyMieSim scatterer sets evaluate parameter combinations as a grid when
        several geometric arrays are passed at once. For a calibration table,
        the required behavior is row wise instead:

        - row 0 uses ``core_diameters_nm[0]`` with ``shell_thicknesses_nm[0]``
        - row 1 uses ``core_diameters_nm[1]`` with ``shell_thicknesses_nm[1]``

        This method therefore evaluates one paired core shell geometry at a
        time and concatenates the resulting coupling values.
        """
        logger.debug(
            "compute_modeled_coupling_from_core_shell_dimensions called with core_diameters_nm=%r shell_thicknesses_nm=%r wavelength_nm=%r source_numerical_aperture=%r optical_power_watt=%r detector_numerical_aperture=%r medium_refractive_index=%r core_refractive_index=%r shell_refractive_index=%r detector_cache_numerical_aperture=%r detector_phi_offset_degree=%r detector_gamma_offset_degree=%r polarization_angle_degree=%r detector_sampling=%r",
            BackEnd._summarize_numeric_array(core_diameters_nm),
            BackEnd._summarize_numeric_array(shell_thicknesses_nm),
            wavelength_nm,
            source_numerical_aperture,
            optical_power_watt,
            detector_numerical_aperture,
            medium_refractive_index,
            core_refractive_index,
            shell_refractive_index,
            detector_cache_numerical_aperture,
            detector_phi_offset_degree,
            detector_gamma_offset_degree,
            polarization_angle_degree,
            detector_sampling,
        )

        core_diameters_nm = BackEnd._sanitize_positive_float_array(
            core_diameters_nm,
            require_positive_values=True,
        )

        shell_thicknesses_nm = BackEnd._sanitize_positive_float_array(
            shell_thicknesses_nm,
            require_positive_values=True,
        )

        core_diameters_nm, shell_thicknesses_nm = BackEnd._broadcast_two_positive_arrays(
            first_values=core_diameters_nm,
            second_values=shell_thicknesses_nm,
            first_name="core_diameters_nm",
            second_name="shell_thicknesses_nm",
        )

        if core_diameters_nm.size == 0:
            raise ValueError("No valid positive core diameters were provided.")

        if shell_thicknesses_nm.size == 0:
            raise ValueError("No valid positive shell thicknesses were provided.")

        particle_diameters_nm = core_diameters_nm + 2.0 * shell_thicknesses_nm

        logger.debug(
            "Sanitized paired core shell dimensions with core_diameters_nm=%r shell_thicknesses_nm=%r particle_diameters_nm=%r",
            BackEnd._summarize_numeric_array(core_diameters_nm),
            BackEnd._summarize_numeric_array(shell_thicknesses_nm),
            BackEnd._summarize_numeric_array(particle_diameters_nm),
        )

        resolved_detector_cache_numerical_aperture = BackEnd._resolve_detector_cache_numerical_aperture(
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        )

        logger.debug(
            "Resolved detector cache numerical aperture=%r",
            resolved_detector_cache_numerical_aperture,
        )

        expected_coupling_values_array = np.asarray(
            BackEnd._compute_cached_core_shell_coupling(
                core_diameters_nm=tuple(float(value) for value in core_diameters_nm.tolist()),
                shell_thicknesses_nm=tuple(float(value) for value in shell_thicknesses_nm.tolist()),
                wavelength_nm=float(wavelength_nm),
                source_numerical_aperture=float(source_numerical_aperture),
                optical_power_watt=float(optical_power_watt),
                detector_numerical_aperture=float(detector_numerical_aperture),
                medium_refractive_index=float(medium_refractive_index),
                core_refractive_index=float(core_refractive_index),
                shell_refractive_index=float(shell_refractive_index),
                detector_cache_numerical_aperture=float(resolved_detector_cache_numerical_aperture),
                detector_phi_offset_degree=float(detector_phi_offset_degree),
                detector_gamma_offset_degree=float(detector_gamma_offset_degree),
                polarization_angle_degree=float(polarization_angle_degree),
                detector_sampling=int(detector_sampling),
            ),
            dtype=float,
        )

        BackEnd._validate_coupling_size(
            coupling_values=expected_coupling_values_array,
            expected_size=core_diameters_nm.size,
            size_context="core shell row",
        )

        model_metadata = {
            "mie_model": CORE_SHELL_SPHERE_MODEL_NAME,
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
            "core_refractive_index": float(core_refractive_index),
            "shell_refractive_index": float(shell_refractive_index),
            "core_diameters_nm": core_diameters_nm.tolist(),
            "shell_thicknesses_nm": shell_thicknesses_nm.tolist(),
            "particle_diameters_nm": particle_diameters_nm.tolist(),
        }

        modeled_coupling_result = ModeledCouplingResult(
            particle_diameters_nm=particle_diameters_nm,
            expected_coupling_values=expected_coupling_values_array,
            model_metadata=model_metadata,
        )

        logger.debug(
            "compute_modeled_coupling_from_core_shell_dimensions returning expected_coupling_values=%r",
            BackEnd._summarize_numeric_array(modeled_coupling_result.expected_coupling_values),
        )

        return modeled_coupling_result

    @staticmethod
    @lru_cache(maxsize=32)
    def _compute_cached_core_shell_coupling(
        *,
        core_diameters_nm: tuple[float, ...],
        shell_thicknesses_nm: tuple[float, ...],
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        medium_refractive_index: float,
        core_refractive_index: float,
        shell_refractive_index: float,
        detector_cache_numerical_aperture: float,
        detector_phi_offset_degree: float,
        detector_gamma_offset_degree: float,
        polarization_angle_degree: float,
        detector_sampling: int,
    ) -> tuple[float, ...]:
        """
        Cache row-wise core-shell coupling computations for deterministic inputs.
        """
        expected_coupling_values: list[float] = []

        for row_index, (core_diameter_nm, shell_thickness_nm) in enumerate(
            zip(core_diameters_nm, shell_thicknesses_nm, strict=True)
        ):
            logger.debug(
                "Computing paired cached CoreShellSet row_index=%r core_diameter_nm=%r shell_thickness_nm=%r.",
                row_index,
                float(core_diameter_nm),
                float(shell_thickness_nm),
            )

            def build_core_shell_scatterer_set() -> Any:
                logger.debug(
                    "Building cached CoreShellSet for row_index=%r.",
                    row_index,
                )

                return PyMieSim.scatterer_set.CoreShellSet(
                    core_diameter=[float(core_diameter_nm)] * ureg.nanometer,
                    shell_thickness=[float(shell_thickness_nm)] * ureg.nanometer,
                    core_material=[complex(float(core_refractive_index), 0.0)],
                    shell_material=[complex(float(shell_refractive_index), 0.0)],
                    medium=[float(medium_refractive_index)],
                )

            coupling_values = BackEnd._compute_coupling_values_with_fallback(
                scatterer_set_builder=build_core_shell_scatterer_set,
                wavelength_nm=wavelength_nm,
                source_numerical_aperture=source_numerical_aperture,
                optical_power_watt=optical_power_watt,
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                detector_phi_offset_degree=detector_phi_offset_degree,
                detector_gamma_offset_degree=detector_gamma_offset_degree,
                polarization_angle_degree=polarization_angle_degree,
                detector_sampling=detector_sampling,
            )

            if coupling_values.size != 1:
                raise ValueError(
                    "Core shell row wise coupling computation returned an unexpected "
                    f"number of values for row {row_index}. "
                    f"Expected 1 value, got {coupling_values.size} values."
                )

            expected_coupling_values.append(float(coupling_values[0]))

        return tuple(expected_coupling_values)

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
    def _compute_coupling_values_with_fallback(
        *,
        scatterer_set_builder: Callable[[], Any],
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        detector_cache_numerical_aperture: float,
        detector_phi_offset_degree: float,
        detector_gamma_offset_degree: float,
        polarization_angle_degree: float,
        detector_sampling: int,
    ) -> np.ndarray:
        """
        Compute coupling values with the requested detector sampling.

        If the primary computation fails, the computation is retried with a
        smaller detector sampling value. This keeps the previous backend
        behavior while sharing it across scatterer models.
        """
        try:
            return BackEnd._run_coupling_simulation(
                scatterer_set_builder=scatterer_set_builder,
                wavelength_nm=wavelength_nm,
                source_numerical_aperture=source_numerical_aperture,
                optical_power_watt=optical_power_watt,
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                detector_phi_offset_degree=detector_phi_offset_degree,
                detector_gamma_offset_degree=detector_gamma_offset_degree,
                polarization_angle_degree=polarization_angle_degree,
                detector_sampling=int(detector_sampling),
            )
        except Exception:
            logger.exception(
                "Primary coupling computation failed with detector_sampling=%r. Retrying with a smaller sampling value.",
                detector_sampling,
            )

            fallback_sampling = max(50, min(200, int(detector_sampling)))

            if fallback_sampling == int(detector_sampling):
                fallback_sampling = 100

            return BackEnd._run_coupling_simulation(
                scatterer_set_builder=scatterer_set_builder,
                wavelength_nm=wavelength_nm,
                source_numerical_aperture=source_numerical_aperture,
                optical_power_watt=optical_power_watt,
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                detector_phi_offset_degree=detector_phi_offset_degree,
                detector_gamma_offset_degree=detector_gamma_offset_degree,
                polarization_angle_degree=polarization_angle_degree,
                detector_sampling=fallback_sampling,
            )

    @staticmethod
    def _run_coupling_simulation(
        *,
        scatterer_set_builder: Callable[[], Any],
        wavelength_nm: float,
        source_numerical_aperture: float,
        optical_power_watt: float,
        detector_numerical_aperture: float,
        detector_cache_numerical_aperture: float,
        detector_phi_offset_degree: float,
        detector_gamma_offset_degree: float,
        polarization_angle_degree: float,
        detector_sampling: int,
    ) -> np.ndarray:
        """
        Build the PyMieSim experiment and return processed coupling values.
        """
        logger.debug("Building PolarizationSet with sampling=%r.", detector_sampling)

        polarization_set = PyMieSim.polarization_set.PolarizationSet(
            angles=[float(polarization_angle_degree)] * ureg.degree,
        )

        logger.debug("Building GaussianSet.")

        source_set = PyMieSim.source_set.GaussianSet(
            wavelength=[float(wavelength_nm)] * ureg.nanometer,
            polarization=polarization_set,
            optical_power=[float(optical_power_watt)] * ureg.watt,
            numerical_aperture=[float(source_numerical_aperture)],
        )

        scatterer_set = scatterer_set_builder()

        logger.debug("Building PhotodiodeSet.")

        detector_set = PyMieSim.detector_set.PhotodiodeSet(
            numerical_aperture=[float(detector_numerical_aperture)],
            cache_numerical_aperture=[float(detector_cache_numerical_aperture)],
            phi_offset=[float(detector_phi_offset_degree)] * ureg.degree,
            gamma_offset=[float(detector_gamma_offset_degree)] * ureg.degree,
            sampling=[int(detector_sampling)],
        )

        logger.debug("Building Setup.")

        experiment = PyMieSim.Setup(
            scatterer_set=scatterer_set,
            source_set=source_set,
            detector_set=detector_set,
        )

        logger.debug(
            "Calling experiment.get('coupling', as_numpy=True) with sampling=%r.",
            detector_sampling,
        )

        start_time = time.perf_counter()
        coupling_values = experiment.get("coupling", as_numpy=True)
        elapsed_time = time.perf_counter() - start_time

        logger.debug(
            "experiment.get('coupling') returned after %.3f s with raw type=%s",
            elapsed_time,
            type(coupling_values).__name__,
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
            "Processed coupling values with sampling=%r",
            detector_sampling,
        )

        return coupling_values

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
    def _broadcast_two_positive_arrays(
        *,
        first_values: np.ndarray,
        second_values: np.ndarray,
        first_name: str,
        second_name: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Broadcast two one dimensional positive arrays to a common length.

        A scalar array can be expanded to match the other array. If both arrays
        contain more than one value, their sizes must match.
        """
        first_values = np.asarray(first_values, dtype=float).reshape(-1)
        second_values = np.asarray(second_values, dtype=float).reshape(-1)

        if first_values.size == 0:
            raise ValueError(f"No valid positive values were provided for {first_name}.")

        if second_values.size == 0:
            raise ValueError(f"No valid positive values were provided for {second_name}.")

        if first_values.size == second_values.size:
            return first_values, second_values

        if first_values.size == 1:
            first_values = np.full(second_values.size, float(first_values[0]), dtype=float)
            return first_values, second_values

        if second_values.size == 1:
            second_values = np.full(first_values.size, float(second_values[0]), dtype=float)
            return first_values, second_values

        raise ValueError(
            f"{first_name} and {second_name} must have the same size, "
            f"or one of them must contain a single value. "
            f"Got {first_name} size {first_values.size} and {second_name} size {second_values.size}."
        )

    @staticmethod
    def _resolve_detector_cache_numerical_aperture(
        *,
        detector_numerical_aperture: float,
        detector_cache_numerical_aperture: Optional[float],
    ) -> float:
        """
        Resolve detector cache numerical aperture.

        If no explicit cache numerical aperture is provided, the detector
        numerical aperture is reused.
        """
        if detector_cache_numerical_aperture is None:
            return float(detector_numerical_aperture)

        return float(detector_cache_numerical_aperture)

    @staticmethod
    def _validate_coupling_size(
        *,
        coupling_values: np.ndarray,
        expected_size: int,
        size_context: str,
    ) -> None:
        """
        Validate that PyMieSim returned one coupling value per modeled particle.
        """
        if coupling_values.size == expected_size:
            return

        raise ValueError(
            "Modeled coupling result size does not match the provided "
            f"{size_context} size. Got {coupling_values.size} modeled values "
            f"for {expected_size} input values."
        )

    @staticmethod
    def _normalize_mie_model(mie_model: str) -> str:
        """
        Normalize supported scattering model names.
        """
        if mie_model is None:
            return SOLID_SPHERE_MODEL_NAME

        normalized_mie_model = str(mie_model).strip().lower()

        if normalized_mie_model in {"solid sphere", "sphere", "solid_sphere"}:
            return SOLID_SPHERE_MODEL_NAME

        if normalized_mie_model in {
            "core/shell sphere",
            "core-shell sphere",
            "core shell sphere",
            "coreshell sphere",
            "core_shell_sphere",
        }:
            return CORE_SHELL_SPHERE_MODEL_NAME

        raise ValueError(f"Unsupported scattering model: {mie_model!r}")

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
