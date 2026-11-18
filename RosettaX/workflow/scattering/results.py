"""Structured results for scattering modeling and calibration."""

import numpy as np
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModeledCouplingResult:
    """
    Container for modeled scattering coupling values.
    """

    particle_diameters_nm: np.ndarray
    expected_coupling_values: np.ndarray
    expected_cross_section_nm2_values: np.ndarray
    model_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the modeled coupling result to a JSON safe dictionary.
        """
        return {
            "particle_diameters_nm": self.particle_diameters_nm.tolist(),
            "expected_coupling_values": self.expected_coupling_values.tolist(),
            "expected_cross_section_nm2_values": self.expected_cross_section_nm2_values.tolist(),
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


