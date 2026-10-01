"""Scattering calibration models."""

import logging
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from . import mie_relation
from .mie_relation import MieRelation
from .numerical_arrays import _log_array_summary

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE = 0.0


@dataclass(frozen=True)
class OpticalParameters:
    """
    Parsed optical and particle parameters used for scattering calibration.

    These parameters describe the calibration standard model. They are used to
    compute the modeled coupling values of the standard particles.
    """

    medium_refractive_index: float
    particle_refractive_index: float | None
    core_refractive_index: float | None
    shell_refractive_index: float | None
    wavelength_nm: float
    detector_numerical_aperture: float
    detector_cache_numerical_aperture: float
    blocker_bar_numerical_aperture: float
    detector_sampling: int
    detector_phi_angle_degree: float
    detector_gamma_angle_degree: float
    optical_power_watt: float = 1.0
    source_numerical_aperture: float = 0.1
    polarization_angle_degree: float = DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE
    detector_configuration_preset_name: str = ""
    detector_angular_weights: np.ndarray | None = None
    effective_detector_cache_numerical_aperture: float | None = None
    effective_blocker_bar_numerical_aperture: float | None = None

    @property
    def modeling_detector_cache_numerical_aperture(self) -> float:
        if self.effective_detector_cache_numerical_aperture is None:
            return self.detector_cache_numerical_aperture

        return self.effective_detector_cache_numerical_aperture

    @property
    def modeling_blocker_bar_numerical_aperture(self) -> float:
        if self.effective_blocker_bar_numerical_aperture is None:
            return self.blocker_bar_numerical_aperture

        return self.effective_blocker_bar_numerical_aperture

    def to_parameter_payload(
        self,
        *,
        mie_model: str,
        particle_diameter_nm: list[float] | None = None,
        core_diameter_nm: list[float] | None = None,
        shell_thickness_nm: list[float] | None = None,
        outer_diameter_nm: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Convert the optical parameters into a serializable Mie parameter payload.
        """
        logger.debug(
            "OpticalParameters.to_parameter_payload called with mie_model=%r "
            "particle_diameter_nm_count=%r core_diameter_nm_count=%r "
            "shell_thickness_nm_count=%r outer_diameter_nm_count=%r",
            mie_model,
            None if particle_diameter_nm is None else len(particle_diameter_nm),
            None if core_diameter_nm is None else len(core_diameter_nm),
            None if shell_thickness_nm is None else len(shell_thickness_nm),
            None if outer_diameter_nm is None else len(outer_diameter_nm),
        )

        parameter_payload = mie_relation.build_mie_parameter_payload(
            mie_model=mie_model,
            medium_refractive_index=self.medium_refractive_index,
            particle_refractive_index=self.particle_refractive_index,
            core_refractive_index=self.core_refractive_index,
            shell_refractive_index=self.shell_refractive_index,
            wavelength_nm=self.wavelength_nm,
            detector_numerical_aperture=self.detector_numerical_aperture,
            detector_cache_numerical_aperture=self.detector_cache_numerical_aperture,
            blocker_bar_numerical_aperture=self.blocker_bar_numerical_aperture,
            detector_sampling=self.detector_sampling,
            detector_phi_angle_degree=self.detector_phi_angle_degree,
            detector_gamma_angle_degree=self.detector_gamma_angle_degree,
        )

        parameter_payload.update(
            {
                "optical_power_watt": self.optical_power_watt,
                "source_numerical_aperture": self.source_numerical_aperture,
                "polarization_angle_degree": self.polarization_angle_degree,
                "detector_configuration_preset_name": self.detector_configuration_preset_name,
                "effective_detector_cache_numerical_aperture": self.effective_detector_cache_numerical_aperture,
                "effective_blocker_bar_numerical_aperture": self.effective_blocker_bar_numerical_aperture,
                "detector_has_angular_weights": self.detector_angular_weights is not None,
            }
        )

        if particle_diameter_nm is not None:
            parameter_payload["particle_diameter_nm"] = particle_diameter_nm

        if core_diameter_nm is not None:
            parameter_payload["core_diameter_nm"] = core_diameter_nm

        if shell_thickness_nm is not None:
            parameter_payload["shell_thickness_nm"] = shell_thickness_nm

        if outer_diameter_nm is not None:
            parameter_payload["outer_diameter_nm"] = outer_diameter_nm

        logger.debug(
            "OpticalParameters.to_parameter_payload returning keys=%r",
            sorted(parameter_payload.keys()),
        )

        return parameter_payload


@dataclass(frozen=True)
class ParsedSphereStandardRows:
    """
    Parsed solid sphere calibration standard rows.
    """

    row_indices: list[int]
    particle_diameters_nm: np.ndarray
    measured_peak_positions: np.ndarray

    @property
    def row_count(self) -> int:
        """
        Number of valid parsed rows.
        """
        return len(
            self.row_indices,
        )


@dataclass(frozen=True)
class ParsedCoreShellStandardRows:
    """
    Parsed core shell calibration standard rows.
    """

    row_indices: list[int]
    core_diameters_nm: np.ndarray
    shell_thicknesses_nm: np.ndarray
    outer_diameters_nm: np.ndarray
    measured_peak_positions: np.ndarray

    @property
    def row_count(self) -> int:
        """
        Number of valid parsed rows.
        """
        return len(
            self.row_indices,
        )


@dataclass(frozen=True)
class ScatteringInstrumentResponse:
    """
    Instrument response calibration for scattering measurements.

    This object maps a measured cytometry signal, expressed in arbitrary
    instrument units, to a modeled optical coupling value.
    """

    measured_channel: str
    slope: float
    intercept: float
    r_squared: float
    force_zero_intercept: bool = True
    input_quantity: str = "measured_peak_intensity"
    output_quantity: str = "optical_coupling"
    model_name: str = "linear"

    def measured_to_coupling(
        self,
        measured_values: np.ndarray,
    ) -> np.ndarray:
        """
        Convert measured instrument values into estimated optical coupling.
        """
        measured_array = np.asarray(
            measured_values,
            dtype=float,
        )

        logger.debug(
            "ScatteringInstrumentResponse.measured_to_coupling called with "
            "measured_values_shape=%r slope=%r intercept=%r",
            measured_array.shape,
            self.slope,
            self.intercept,
        )

        return self.slope * measured_array + self.intercept

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the instrument response into a JSON serializable dictionary.
        """
        payload = asdict(
            self,
        )

        logger.debug(
            "ScatteringInstrumentResponse.to_dict returning payload=%r",
            payload,
        )

        return payload

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ScatteringInstrumentResponse":
        """
        Build an instrument response from a dictionary payload.
        """
        logger.debug(
            "ScatteringInstrumentResponse.from_dict called with payload_type=%s keys=%r",
            type(payload).__name__,
            sorted(payload.keys()) if isinstance(payload, dict) else None,
        )

        if not isinstance(payload, dict):
            raise TypeError("ScatteringInstrumentResponse payload must be a dictionary.")

        return cls(
            measured_channel=str(
                payload.get(
                    "measured_channel",
                    "",
                )
            ),
            slope=float(
                payload.get(
                    "slope",
                    0.0,
                )
            ),
            intercept=float(
                payload.get(
                    "intercept",
                    0.0,
                )
            ),
            r_squared=float(
                payload.get(
                    "r_squared",
                    np.nan,
                )
            ),
            force_zero_intercept=bool(
                payload.get(
                    "force_zero_intercept",
                    True,
                )
            ),
            input_quantity=str(
                payload.get(
                    "input_quantity",
                    "measured_peak_intensity",
                )
            ),
            output_quantity=str(
                payload.get(
                    "output_quantity",
                    "optical_coupling",
                )
            ),
            model_name=str(
                payload.get(
                    "model_name",
                    payload.get(
                        "model",
                        "linear",
                    ),
                )
            ),
        )


@dataclass(frozen=True)
class ScatteringCalibration:
    """
    Saved scattering calibration object.
    """

    instrument_response: ScatteringInstrumentResponse
    calibration_standard_mie_relation: MieRelation
    reference_table: list[dict[str, Any]]
    metadata: dict[str, Any]
    calibration_type: str = "scattering"
    version: int = 2

    @property
    def source_channel(self) -> str:
        """
        Return the canonical measured source channel for this calibration.
        """
        return str(
            self.instrument_response.measured_channel,
        ).strip()

    def measured_to_coupling(
        self,
        measured_values: np.ndarray,
    ) -> np.ndarray:
        """
        Convert measured values into estimated optical coupling.
        """
        logger.debug(
            "ScatteringCalibration.measured_to_coupling called with source_channel=%r",
            self.source_channel,
        )

        return self.instrument_response.measured_to_coupling(
            measured_values,
        )

    def measured_to_equivalent_diameter(
        self,
        *,
        measured_values: np.ndarray,
        target_mie_relation: MieRelation,
    ) -> np.ndarray:
        """
        Convert measured values into target model equivalent diameter.
        """
        logger.debug(
            "ScatteringCalibration.measured_to_equivalent_diameter called with source_channel=%r",
            self.source_channel,
        )

        estimated_coupling = self.measured_to_coupling(
            measured_values,
        )

        return target_mie_relation.coupling_to_diameter(
            estimated_coupling,
        )

    def apply_to_measured_values(
        self,
        *,
        measured_values: np.ndarray,
        target_mie_relation: MieRelation,
    ) -> dict[str, np.ndarray]:
        """
        Apply the scattering calibration to measured values.
        """
        measured_values_array = np.asarray(
            measured_values,
            dtype=float,
        )

        logger.debug(
            "ScatteringCalibration.apply_to_measured_values called with "
            "measured_values_shape=%r target_relation_mie_model=%r",
            measured_values_array.shape,
            getattr(target_mie_relation, "mie_model", None),
        )

        estimated_coupling = self.measured_to_coupling(
            measured_values_array,
        )

        mie_equivalent_diameter_nm = target_mie_relation.coupling_to_diameter(
            estimated_coupling,
        )

        _log_array_summary(
            name="estimated_coupling",
            values=estimated_coupling,
        )

        _log_array_summary(
            name="mie_equivalent_diameter_nm",
            values=mie_equivalent_diameter_nm,
        )

        return {
            "estimated_coupling": estimated_coupling,
            "mie_equivalent_diameter_nm": mie_equivalent_diameter_nm,
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the scattering calibration into a JSON serializable dictionary.
        """
        source_channel = self.source_channel

        metadata = dict(
            self.metadata,
        )

        metadata["measured_channel"] = source_channel

        payload = {
            "calibration_type": self.calibration_type,
            "version": self.version,
            "source_channel": source_channel,
            "output_quantity": "estimated_coupling",
            "instrument_response": self.instrument_response.to_dict(),
            "calibration_standard_mie_relation": self.calibration_standard_mie_relation.to_dict(),
            "reference_table": [
                dict(row)
                for row in self.reference_table
            ],
            "metadata": metadata,
        }

        logger.debug(
            "ScatteringCalibration.to_dict returning source_channel=%r "
            "reference_table_count=%r metadata_keys=%r payload_keys=%r",
            source_channel,
            len(payload["reference_table"]),
            sorted(metadata.keys()),
            sorted(payload.keys()),
        )

        return payload

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ScatteringCalibration":
        """
        Build a scattering calibration from a dictionary payload.
        """
        logger.debug(
            "ScatteringCalibration.from_dict called with payload_type=%s keys=%r",
            type(payload).__name__,
            sorted(payload.keys()) if isinstance(payload, dict) else None,
        )

        if not isinstance(payload, dict):
            raise TypeError("ScatteringCalibration payload must be a dictionary.")

        calibration_type = str(
            payload.get(
                "calibration_type",
                "",
            )
        )

        if calibration_type and calibration_type != "scattering":
            raise ValueError(
                f"Expected scattering calibration payload, got {calibration_type!r}."
            )

        version = int(
            payload.get(
                "version",
                1,
            )
        )

        if version < 2:
            raise ValueError(
                "This scattering calibration uses an older schema. "
                "Expected version 2 with instrument_response and "
                "calibration_standard_mie_relation."
            )

        source_channel = str(
            payload.get(
                "source_channel",
                "",
            )
        ).strip()

        instrument_response = ScatteringInstrumentResponse.from_dict(
            payload.get(
                "instrument_response",
                {},
            )
        )

        if source_channel and not str(instrument_response.measured_channel).strip():
            logger.debug(
                "ScatteringCalibration.from_dict injecting source_channel=%r into instrument_response.",
                source_channel,
            )

            instrument_response = ScatteringInstrumentResponse(
                measured_channel=source_channel,
                slope=instrument_response.slope,
                intercept=instrument_response.intercept,
                r_squared=instrument_response.r_squared,
                force_zero_intercept=instrument_response.force_zero_intercept,
                input_quantity=instrument_response.input_quantity,
                output_quantity=instrument_response.output_quantity,
                model_name=instrument_response.model_name,
            )

        metadata = dict(
            payload.get(
                "metadata",
                {},
            )
        )

        if source_channel:
            metadata["measured_channel"] = source_channel

        reference_table = [
            dict(row)
            for row in payload.get(
                "reference_table",
                [],
            )
            if isinstance(row, dict)
        ]

        logger.debug(
            "ScatteringCalibration.from_dict parsed version=%r source_channel=%r "
            "reference_table_count=%r metadata_keys=%r",
            version,
            source_channel,
            len(reference_table),
            sorted(metadata.keys()),
        )

        return cls(
            instrument_response=instrument_response,
            calibration_standard_mie_relation=MieRelation.from_dict(
                payload.get(
                    "calibration_standard_mie_relation",
                    {},
                )
            ),
            reference_table=reference_table,
            metadata=metadata,
            calibration_type="scattering",
            version=version,
        )


@dataclass(frozen=True)
class ScatteringCalibrationBuildResult:
    """
    Result produced by building a scattering calibration from standard rows.
    """

    calibration: ScatteringCalibration
    instrument_response: ScatteringInstrumentResponse
    calibration_standard_mie_relation: MieRelation
    updated_table_rows: list[dict[str, str]]
    measured_peak_positions: np.ndarray
    standard_diameters_nm: np.ndarray
    standard_coupling_values: np.ndarray


@dataclass(frozen=True)
class ScatteringApplicationResult:
    """
    Result produced when applying a scattering calibration to measured data.
    """

    estimated_coupling: list[float]
    mie_equivalent_diameter_nm: list[float]
    target_mie_relation: MieRelation
    warnings: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the application result into a JSON serializable dictionary.
        """
        payload = {
            "estimated_coupling": list(
                self.estimated_coupling,
            ),
            "mie_equivalent_diameter_nm": list(
                self.mie_equivalent_diameter_nm,
            ),
            "target_mie_relation": self.target_mie_relation.to_dict(),
            "warnings": list(
                self.warnings,
            ),
            "metadata": dict(
                self.metadata,
            ),
        }

        logger.debug(
            "ScatteringApplicationResult.to_dict returning estimated_coupling_count=%r "
            "mie_equivalent_diameter_count=%r warning_count=%r metadata_keys=%r",
            len(payload["estimated_coupling"]),
            len(payload["mie_equivalent_diameter_nm"]),
            len(payload["warnings"]),
            sorted(payload["metadata"].keys()),
        )

        return payload
