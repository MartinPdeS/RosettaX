# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional
import logging

import numpy as np

from RosettaX.utils import casting
from RosettaX.workflow.calibration.mie_relation import MieRelation
from RosettaX.workflow.calibration.mie_relation import build_mie_parameter_payload
from RosettaX.workflow.calibration.mie_relation import build_mie_relation_from_arrays


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpticalParameters:
    """
    Parsed optical and particle parameters used for scattering calibration.

    These parameters describe the calibration standard model. They are used to
    compute the modeled coupling values of the standard particles.
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

    def to_parameter_payload(
        self,
        *,
        mie_model: str,
        particle_diameter_nm: Optional[list[float]] = None,
        core_diameter_nm: Optional[list[float]] = None,
        shell_thickness_nm: Optional[list[float]] = None,
        outer_diameter_nm: Optional[list[float]] = None,
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

        parameter_payload = build_mie_parameter_payload(
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


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Normalize the selected Mie model name.
    """
    mie_model_string = "" if mie_model is None else str(mie_model).strip()

    if mie_model_string == "Core/Shell Sphere":
        resolved_mie_model = "Core/Shell Sphere"
    else:
        resolved_mie_model = "Solid Sphere"

    logger.debug(
        "resolve_mie_model called with mie_model=%r resolved_mie_model=%r",
        mie_model,
        resolved_mie_model,
    )

    return resolved_mie_model


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
    """
    logger.debug(
        "parse_optical_parameters called with medium_refractive_index=%r "
        "particle_refractive_index=%r core_refractive_index=%r "
        "shell_refractive_index=%r wavelength_nm=%r "
        "detector_numerical_aperture=%r detector_cache_numerical_aperture=%r "
        "blocker_bar_numerical_aperture=%r detector_sampling=%r "
        "detector_phi_angle_degree=%r detector_gamma_angle_degree=%r",
        medium_refractive_index,
        particle_refractive_index,
        core_refractive_index,
        shell_refractive_index,
        wavelength_nm,
        detector_numerical_aperture,
        detector_cache_numerical_aperture,
        blocker_bar_numerical_aperture,
        detector_sampling,
        detector_phi_angle_degree,
        detector_gamma_angle_degree,
    )

    optical_parameters = OpticalParameters(
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

    logger.debug(
        "parse_optical_parameters returning optical_parameters=%r",
        optical_parameters,
    )

    return optical_parameters


def parse_sphere_rows_for_fit(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> ParsedSphereStandardRows:
    """
    Extract valid solid sphere calibration standard rows.
    """
    row_indices: list[int] = []
    particle_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    total_row_count = 0
    skipped_row_count = 0

    for row_index, row in enumerate(rows or []):
        total_row_count += 1

        if not isinstance(row, dict):
            logger.debug(
                "parse_sphere_rows_for_fit skipped row_index=%r because row is not a dictionary: %r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        try:
            raw_particle_diameter_nm = row.get(
                "particle_diameter_nm",
            )

            raw_measured_peak_position = row.get(
                "measured_peak_position",
            )

            if raw_particle_diameter_nm in ("", None):
                logger.debug(
                    "parse_sphere_rows_for_fit skipped row_index=%r because particle_diameter_nm is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            if raw_measured_peak_position in ("", None):
                logger.debug(
                    "parse_sphere_rows_for_fit skipped row_index=%r because measured_peak_position is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            particle_diameter_nm = float(
                raw_particle_diameter_nm,
            )

            measured_peak_position = float(
                raw_measured_peak_position,
            )

        except Exception:
            logger.exception(
                "parse_sphere_rows_for_fit skipped row_index=%r because conversion failed. row=%r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        if particle_diameter_nm <= 0.0:
            logger.debug(
                "parse_sphere_rows_for_fit skipped row_index=%r because particle_diameter_nm=%r is not positive.",
                row_index,
                particle_diameter_nm,
            )
            skipped_row_count += 1
            continue

        if measured_peak_position <= 0.0:
            logger.debug(
                "parse_sphere_rows_for_fit skipped row_index=%r because measured_peak_position=%r is not positive.",
                row_index,
                measured_peak_position,
            )
            skipped_row_count += 1
            continue

        row_indices.append(
            row_index,
        )

        particle_diameters_nm.append(
            particle_diameter_nm,
        )

        measured_peak_positions.append(
            measured_peak_position,
        )

    parsed_rows = ParsedSphereStandardRows(
        row_indices=row_indices,
        particle_diameters_nm=np.asarray(
            particle_diameters_nm,
            dtype=float,
        ),
        measured_peak_positions=np.asarray(
            measured_peak_positions,
            dtype=float,
        ),
    )

    logger.debug(
        "parse_sphere_rows_for_fit parsed total_row_count=%r valid_row_count=%r "
        "skipped_row_count=%r row_indices=%r",
        total_row_count,
        parsed_rows.row_count,
        skipped_row_count,
        parsed_rows.row_indices,
    )

    _log_array_summary(
        name="parsed_sphere_particle_diameters_nm",
        values=parsed_rows.particle_diameters_nm,
    )

    _log_array_summary(
        name="parsed_sphere_measured_peak_positions",
        values=parsed_rows.measured_peak_positions,
    )

    return parsed_rows


def parse_core_shell_rows_for_fit(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> ParsedCoreShellStandardRows:
    """
    Extract valid core shell calibration standard rows.
    """
    row_indices: list[int] = []
    core_diameters_nm: list[float] = []
    shell_thicknesses_nm: list[float] = []
    outer_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    total_row_count = 0
    skipped_row_count = 0

    for row_index, row in enumerate(rows or []):
        total_row_count += 1

        if not isinstance(row, dict):
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because row is not a dictionary: %r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        try:
            raw_core_diameter_nm = row.get(
                "core_diameter_nm",
            )

            raw_shell_thickness_nm = row.get(
                "shell_thickness_nm",
            )

            raw_measured_peak_position = row.get(
                "measured_peak_position",
            )

            if raw_core_diameter_nm in ("", None):
                logger.debug(
                    "parse_core_shell_rows_for_fit skipped row_index=%r because core_diameter_nm is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            if raw_shell_thickness_nm in ("", None):
                logger.debug(
                    "parse_core_shell_rows_for_fit skipped row_index=%r because shell_thickness_nm is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            if raw_measured_peak_position in ("", None):
                logger.debug(
                    "parse_core_shell_rows_for_fit skipped row_index=%r because measured_peak_position is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            core_diameter_nm = float(
                raw_core_diameter_nm,
            )

            shell_thickness_nm = float(
                raw_shell_thickness_nm,
            )

            measured_peak_position = float(
                raw_measured_peak_position,
            )

        except Exception:
            logger.exception(
                "parse_core_shell_rows_for_fit skipped row_index=%r because conversion failed. row=%r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        if core_diameter_nm <= 0.0:
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because core_diameter_nm=%r is not positive.",
                row_index,
                core_diameter_nm,
            )
            skipped_row_count += 1
            continue

        if shell_thickness_nm < 0.0:
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because shell_thickness_nm=%r is negative.",
                row_index,
                shell_thickness_nm,
            )
            skipped_row_count += 1
            continue

        if measured_peak_position <= 0.0:
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because measured_peak_position=%r is not positive.",
                row_index,
                measured_peak_position,
            )
            skipped_row_count += 1
            continue

        outer_diameter_nm = core_diameter_nm + 2.0 * shell_thickness_nm

        row_indices.append(
            row_index,
        )

        core_diameters_nm.append(
            core_diameter_nm,
        )

        shell_thicknesses_nm.append(
            shell_thickness_nm,
        )

        outer_diameters_nm.append(
            outer_diameter_nm,
        )

        measured_peak_positions.append(
            measured_peak_position,
        )

    parsed_rows = ParsedCoreShellStandardRows(
        row_indices=row_indices,
        core_diameters_nm=np.asarray(
            core_diameters_nm,
            dtype=float,
        ),
        shell_thicknesses_nm=np.asarray(
            shell_thicknesses_nm,
            dtype=float,
        ),
        outer_diameters_nm=np.asarray(
            outer_diameters_nm,
            dtype=float,
        ),
        measured_peak_positions=np.asarray(
            measured_peak_positions,
            dtype=float,
        ),
    )

    logger.debug(
        "parse_core_shell_rows_for_fit parsed total_row_count=%r valid_row_count=%r "
        "skipped_row_count=%r row_indices=%r",
        total_row_count,
        parsed_rows.row_count,
        skipped_row_count,
        parsed_rows.row_indices,
    )

    _log_array_summary(
        name="parsed_core_shell_core_diameters_nm",
        values=parsed_rows.core_diameters_nm,
    )

    _log_array_summary(
        name="parsed_core_shell_shell_thicknesses_nm",
        values=parsed_rows.shell_thicknesses_nm,
    )

    _log_array_summary(
        name="parsed_core_shell_outer_diameters_nm",
        values=parsed_rows.outer_diameters_nm,
    )

    _log_array_summary(
        name="parsed_core_shell_measured_peak_positions",
        values=parsed_rows.measured_peak_positions,
    )

    return parsed_rows


def write_expected_coupling_into_table(
    *,
    rows: list[dict[str, Any]],
    row_indices: list[int],
    expected_coupling_values: np.ndarray,
) -> list[dict[str, str]]:
    """
    Write modeled coupling values into the calibration standard table rows.
    """
    logger.debug(
        "write_expected_coupling_into_table called with row_count=%r row_indices=%r",
        len(rows),
        row_indices,
    )

    _log_array_summary(
        name="write_expected_coupling_values",
        values=expected_coupling_values,
    )

    updated_rows = [
        dict(row)
        for row in rows
    ]

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
            logger.debug(
                "write_expected_coupling_into_table skipped row_index=%r because updated_rows length is %r.",
                row_index,
                len(updated_rows),
            )
            continue

        updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling_value):.6g}"

    serialized_rows = [
        {
            str(key): "" if value is None else str(value)
            for key, value in row.items()
        }
        for row in updated_rows
    ]

    logger.debug(
        "write_expected_coupling_into_table returning row_count=%r",
        len(serialized_rows),
    )

    return serialized_rows


def write_expected_coupling_into_sphere_table(
    *,
    rows: list[dict[str, Any]],
    row_indices: list[int],
    expected_coupling_values: np.ndarray,
) -> list[dict[str, str]]:
    """
    Write modeled coupling values into the solid sphere calibration table rows.

    This wrapper is kept for existing imports and call sites.
    """
    logger.debug("write_expected_coupling_into_sphere_table called.")

    return write_expected_coupling_into_table(
        rows=rows,
        row_indices=row_indices,
        expected_coupling_values=expected_coupling_values,
    )


def build_reference_table_from_rows(
    *,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build a JSON serializable copy of the calibration standard table.
    """
    logger.debug(
        "build_reference_table_from_rows called with row_count=%r",
        len(rows),
    )

    reference_table: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            logger.debug(
                "build_reference_table_from_rows skipped row_index=%r because row is not a dictionary: %r",
                row_index,
                row,
            )
            continue

        reference_table.append(
            {
                str(key): value
                for key, value in row.items()
            }
        )

    logger.debug(
        "build_reference_table_from_rows returning row_count=%r",
        len(reference_table),
    )

    return reference_table


def build_calibration_standard_mie_relation(
    *,
    dense_particle_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    fallback_particle_diameters_nm: np.ndarray,
    fallback_expected_coupling_values: np.ndarray,
    mie_model: str,
    optical_parameters: OpticalParameters,
    fallback_core_diameters_nm: Optional[np.ndarray] = None,
    fallback_shell_thicknesses_nm: Optional[np.ndarray] = None,
) -> MieRelation:
    """
    Build the calibration standard Mie relation stored in the calibration payload.

    The relation itself is one dimensional and maps outer diameter to modeled
    coupling for core shell standards. The core shell geometry arrays are stored
    in the parameter payload for provenance.
    """
    logger.debug(
        "build_calibration_standard_mie_relation called with mie_model=%r",
        mie_model,
    )

    dense_particle_diameters_nm = _as_flat_float_array(
        name="dense_particle_diameters_nm",
        values=dense_particle_diameters_nm,
    )

    dense_expected_coupling_values = _as_flat_float_array(
        name="dense_expected_coupling_values",
        values=dense_expected_coupling_values,
    )

    fallback_particle_diameters_nm = _as_flat_float_array(
        name="fallback_particle_diameters_nm",
        values=fallback_particle_diameters_nm,
    )

    fallback_expected_coupling_values = _as_flat_float_array(
        name="fallback_expected_coupling_values",
        values=fallback_expected_coupling_values,
    )

    if dense_particle_diameters_nm.size >= 2 and dense_expected_coupling_values.size >= 2:
        logger.debug(
            "build_calibration_standard_mie_relation using dense relation arrays."
        )

        diameter_values = dense_particle_diameters_nm
        coupling_values = dense_expected_coupling_values

    else:
        logger.debug(
            "build_calibration_standard_mie_relation using fallback standard arrays because "
            "dense sizes are diameter=%r coupling=%r.",
            dense_particle_diameters_nm.size,
            dense_expected_coupling_values.size,
        )

        diameter_values = fallback_particle_diameters_nm
        coupling_values = fallback_expected_coupling_values

    _validate_same_size(
        first_values=diameter_values,
        second_values=coupling_values,
        first_name="mie_relation_diameter_values",
        second_name="mie_relation_coupling_values",
    )

    core_diameter_nm: Optional[list[float]] = None
    shell_thickness_nm: Optional[list[float]] = None

    if fallback_core_diameters_nm is not None:
        fallback_core_diameters_nm = _as_flat_float_array(
            name="fallback_core_diameters_nm",
            values=fallback_core_diameters_nm,
        )

        core_diameter_nm = [
            float(value)
            for value in fallback_core_diameters_nm
        ]

    if fallback_shell_thicknesses_nm is not None:
        fallback_shell_thicknesses_nm = _as_flat_float_array(
            name="fallback_shell_thicknesses_nm",
            values=fallback_shell_thicknesses_nm,
        )

        shell_thickness_nm = [
            float(value)
            for value in fallback_shell_thicknesses_nm
        ]

    parameter_payload = optical_parameters.to_parameter_payload(
        mie_model=mie_model,
        particle_diameter_nm=[
            float(value)
            for value in fallback_particle_diameters_nm
        ],
        core_diameter_nm=core_diameter_nm,
        shell_thickness_nm=shell_thickness_nm,
        outer_diameter_nm=[
            float(value)
            for value in fallback_particle_diameters_nm
        ],
    )

    logger.debug(
        "build_calibration_standard_mie_relation calling build_mie_relation_from_arrays "
        "with diameter_count=%r coupling_count=%r parameter_keys=%r",
        diameter_values.size,
        coupling_values.size,
        sorted(parameter_payload.keys()),
    )

    return build_mie_relation_from_arrays(
        diameter_nm=diameter_values,
        theoretical_coupling=coupling_values,
        mie_model=mie_model,
        parameters=parameter_payload,
        relation_role="calibration_standard",
    )


def fit_linear_instrument_response(
    *,
    measured_peak_values: np.ndarray,
    theoretical_coupling_values: np.ndarray,
    measured_channel: str,
    force_zero_intercept: bool = True,
) -> ScatteringInstrumentResponse:
    """
    Fit the linear instrument response from measured peaks to modeled coupling.

    The fitted model is:

        theoretical_coupling = slope * measured_peak + intercept

    If force_zero_intercept is True, the intercept is fixed to zero.
    """
    logger.debug(
        "fit_linear_instrument_response called with measured_channel=%r "
        "force_zero_intercept=%r",
        measured_channel,
        force_zero_intercept,
    )

    measured_array = _as_flat_float_array(
        name="fit_measured_peak_values_before_mask",
        values=measured_peak_values,
    )

    coupling_array = _as_flat_float_array(
        name="fit_theoretical_coupling_values_before_mask",
        values=theoretical_coupling_values,
    )

    _validate_same_size(
        first_values=measured_array,
        second_values=coupling_array,
        first_name="measured_peak_values",
        second_name="theoretical_coupling_values",
    )

    valid_mask = (
        np.isfinite(
            measured_array,
        )
        & np.isfinite(
            coupling_array,
        )
    )

    logger.debug(
        "fit_linear_instrument_response finite valid_count=%r total_count=%r",
        int(np.sum(valid_mask)),
        measured_array.size,
    )

    measured_array = measured_array[valid_mask]
    coupling_array = coupling_array[valid_mask]

    if measured_array.size < 2:
        logger.error(
            "fit_linear_instrument_response failed because finite calibration point count=%r.",
            measured_array.size,
        )
        raise ValueError("At least two valid calibration points are required.")

    if force_zero_intercept:
        nonzero_mask = measured_array != 0.0

        logger.debug(
            "fit_linear_instrument_response zero intercept nonzero_count=%r total_count=%r",
            int(np.sum(nonzero_mask)),
            measured_array.size,
        )

        measured_array = measured_array[nonzero_mask]
        coupling_array = coupling_array[nonzero_mask]

    if measured_array.size < 2:
        logger.error(
            "fit_linear_instrument_response failed because nonzero calibration point count=%r.",
            measured_array.size,
        )
        raise ValueError("At least two nonzero measured values are required.")

    if force_zero_intercept:
        denominator = float(
            np.sum(
                measured_array * measured_array,
            )
        )

        logger.debug(
            "fit_linear_instrument_response zero intercept denominator=%r",
            denominator,
        )

        if denominator == 0.0:
            logger.error(
                "fit_linear_instrument_response failed because denominator is zero."
            )
            raise ValueError("Cannot fit zero intercept response with zero denominator.")

        slope = float(
            np.sum(
                measured_array * coupling_array,
            )
            / denominator
        )

        intercept = 0.0

    else:
        slope, intercept = np.polyfit(
            measured_array,
            coupling_array,
            deg=1,
        )

        slope = float(
            slope,
        )

        intercept = float(
            intercept,
        )

    predicted_coupling = slope * measured_array + intercept

    r_squared = compute_r_squared(
        observed_values=coupling_array,
        predicted_values=predicted_coupling,
    )

    logger.debug(
        "fit_linear_instrument_response fitted slope=%r intercept=%r r_squared=%r "
        "used_point_count=%r",
        slope,
        intercept,
        r_squared,
        measured_array.size,
    )

    return ScatteringInstrumentResponse(
        measured_channel=measured_channel,
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        force_zero_intercept=force_zero_intercept,
    )


def compute_r_squared(
    *,
    observed_values: np.ndarray,
    predicted_values: np.ndarray,
) -> float:
    """
    Compute coefficient of determination.
    """
    observed_array = _as_flat_float_array(
        name="r_squared_observed_values",
        values=observed_values,
    )

    predicted_array = _as_flat_float_array(
        name="r_squared_predicted_values",
        values=predicted_values,
    )

    _validate_same_size(
        first_values=observed_array,
        second_values=predicted_array,
        first_name="observed_values",
        second_name="predicted_values",
    )

    residual_sum_of_squares = float(
        np.sum(
            np.square(
                observed_array - predicted_array,
            )
        )
    )

    total_sum_of_squares = float(
        np.sum(
            np.square(
                observed_array - np.mean(
                    observed_array,
                )
            )
        )
    )

    logger.debug(
        "compute_r_squared residual_sum_of_squares=%r total_sum_of_squares=%r",
        residual_sum_of_squares,
        total_sum_of_squares,
    )

    if total_sum_of_squares == 0.0:
        logger.debug(
            "compute_r_squared returning nan because total_sum_of_squares is zero."
        )
        return np.nan

    return 1.0 - residual_sum_of_squares / total_sum_of_squares


def build_scattering_calibration(
    *,
    measured_peak_values: np.ndarray,
    theoretical_coupling_values: np.ndarray,
    measured_channel: str,
    calibration_standard_mie_relation: MieRelation,
    reference_table: list[dict[str, Any]],
    metadata: Optional[dict[str, Any]] = None,
    force_zero_intercept: bool = True,
) -> ScatteringCalibration:
    """
    Build a saved scattering calibration from standard data.
    """
    logger.debug(
        "build_scattering_calibration called with measured_channel=%r "
        "reference_table_count=%r metadata_keys=%r force_zero_intercept=%r",
        measured_channel,
        len(reference_table),
        sorted((metadata or {}).keys()),
        force_zero_intercept,
    )

    instrument_response = fit_linear_instrument_response(
        measured_peak_values=measured_peak_values,
        theoretical_coupling_values=theoretical_coupling_values,
        measured_channel=measured_channel,
        force_zero_intercept=force_zero_intercept,
    )

    calibration = ScatteringCalibration(
        instrument_response=instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        reference_table=[
            dict(row)
            for row in reference_table
        ],
        metadata=dict(
            metadata or {},
        ),
    )

    logger.debug(
        "build_scattering_calibration returning calibration source_channel=%r",
        calibration.source_channel,
    )

    return calibration


def build_solid_sphere_scattering_calibration_from_standard_data(
    *,
    detector_column: str,
    current_table_rows: list[dict[str, Any]],
    measured_peak_positions: np.ndarray,
    particle_diameters_nm: np.ndarray,
    expected_coupling_values: np.ndarray,
    dense_particle_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    optical_parameters: OpticalParameters,
    metadata: Optional[dict[str, Any]] = None,
    force_zero_intercept: bool = True,
) -> ScatteringCalibrationBuildResult:
    """
    Build a solid sphere scattering calibration from already computed standard data.
    """
    logger.debug(
        "build_solid_sphere_scattering_calibration_from_standard_data called with "
        "detector_column=%r current_table_row_count=%r",
        detector_column,
        len(current_table_rows),
    )

    measured_peak_positions = _as_flat_float_array(
        name="solid_measured_peak_positions",
        values=measured_peak_positions,
    )

    particle_diameters_nm = _as_flat_float_array(
        name="solid_particle_diameters_nm",
        values=particle_diameters_nm,
    )

    expected_coupling_values = _as_flat_float_array(
        name="solid_expected_coupling_values",
        values=expected_coupling_values,
    )

    if measured_peak_positions.size < 2:
        logger.error(
            "Solid sphere calibration failed because measured_peak_positions.size=%r.",
            measured_peak_positions.size,
        )
        raise ValueError("At least two measured peak positions are required.")

    _validate_same_size(
        first_values=particle_diameters_nm,
        second_values=measured_peak_positions,
        first_name="particle_diameters_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=expected_coupling_values,
        second_values=measured_peak_positions,
        first_name="expected_coupling_values",
        second_name="measured_peak_positions",
    )

    parsed_rows = parse_sphere_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_rows.row_count < 2:
        logger.error(
            "Solid sphere calibration failed because parsed row count=%r.",
            parsed_rows.row_count,
        )
        raise ValueError("At least two valid solid sphere standard rows are required.")

    updated_table_rows = write_expected_coupling_into_table(
        rows=current_table_rows,
        row_indices=parsed_rows.row_indices,
        expected_coupling_values=expected_coupling_values,
    )

    calibration_standard_mie_relation = build_calibration_standard_mie_relation(
        dense_particle_diameters_nm=dense_particle_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        fallback_particle_diameters_nm=particle_diameters_nm,
        fallback_expected_coupling_values=expected_coupling_values,
        mie_model="Solid Sphere",
        optical_parameters=optical_parameters,
    )

    resolved_metadata = dict(
        metadata or {},
    )

    resolved_metadata["measured_channel"] = str(
        detector_column,
    )

    resolved_metadata.setdefault(
        "calibration_standard",
        "Solid Sphere",
    )

    resolved_metadata.setdefault(
        "calibration_standard_parameters",
        optical_parameters.to_parameter_payload(
            mie_model="Solid Sphere",
            particle_diameter_nm=[
                float(value)
                for value in particle_diameters_nm
            ],
        ),
    )

    resolved_metadata.setdefault(
        "application_note",
        (
            "This calibration stores the instrument response inferred from the "
            "calibration standard. When applying it to unknown particles, build "
            "a target Mie relation from the target particle model."
        ),
    )

    logger.debug(
        "Solid sphere calibration metadata_keys=%r",
        sorted(resolved_metadata.keys()),
    )

    calibration = build_scattering_calibration(
        measured_peak_values=measured_peak_positions,
        theoretical_coupling_values=expected_coupling_values,
        measured_channel=str(
            detector_column,
        ),
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        reference_table=build_reference_table_from_rows(
            rows=updated_table_rows,
        ),
        metadata=resolved_metadata,
        force_zero_intercept=force_zero_intercept,
    )

    build_result = ScatteringCalibrationBuildResult(
        calibration=calibration,
        instrument_response=calibration.instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        updated_table_rows=updated_table_rows,
        measured_peak_positions=measured_peak_positions,
        standard_diameters_nm=particle_diameters_nm,
        standard_coupling_values=expected_coupling_values,
    )

    logger.debug(
        "build_solid_sphere_scattering_calibration_from_standard_data returning "
        "slope=%r intercept=%r r_squared=%r updated_table_row_count=%r",
        build_result.instrument_response.slope,
        build_result.instrument_response.intercept,
        build_result.instrument_response.r_squared,
        len(build_result.updated_table_rows),
    )

    return build_result


def build_core_shell_scattering_calibration_from_standard_data(
    *,
    detector_column: str,
    current_table_rows: list[dict[str, Any]],
    measured_peak_positions: np.ndarray,
    core_diameters_nm: np.ndarray,
    shell_thicknesses_nm: np.ndarray,
    outer_diameters_nm: np.ndarray,
    expected_coupling_values: np.ndarray,
    dense_outer_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    optical_parameters: OpticalParameters,
    metadata: Optional[dict[str, Any]] = None,
    force_zero_intercept: bool = True,
) -> ScatteringCalibrationBuildResult:
    """
    Build a core shell scattering calibration from already computed standard data.
    """
    logger.debug(
        "build_core_shell_scattering_calibration_from_standard_data called with "
        "detector_column=%r current_table_row_count=%r",
        detector_column,
        len(current_table_rows),
    )

    measured_peak_positions = _as_flat_float_array(
        name="core_shell_measured_peak_positions",
        values=measured_peak_positions,
    )

    core_diameters_nm = _as_flat_float_array(
        name="core_shell_core_diameters_nm",
        values=core_diameters_nm,
    )

    shell_thicknesses_nm = _as_flat_float_array(
        name="core_shell_shell_thicknesses_nm",
        values=shell_thicknesses_nm,
    )

    outer_diameters_nm = _as_flat_float_array(
        name="core_shell_outer_diameters_nm",
        values=outer_diameters_nm,
    )

    expected_coupling_values = _as_flat_float_array(
        name="core_shell_expected_coupling_values",
        values=expected_coupling_values,
    )

    dense_outer_diameters_nm = _as_flat_float_array(
        name="core_shell_dense_outer_diameters_nm",
        values=dense_outer_diameters_nm,
    )

    dense_expected_coupling_values = _as_flat_float_array(
        name="core_shell_dense_expected_coupling_values",
        values=dense_expected_coupling_values,
    )

    if measured_peak_positions.size < 2:
        logger.error(
            "Core shell calibration failed because measured_peak_positions.size=%r.",
            measured_peak_positions.size,
        )
        raise ValueError("At least two measured peak positions are required.")

    _validate_same_size(
        first_values=core_diameters_nm,
        second_values=measured_peak_positions,
        first_name="core_diameters_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=shell_thicknesses_nm,
        second_values=measured_peak_positions,
        first_name="shell_thicknesses_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=outer_diameters_nm,
        second_values=measured_peak_positions,
        first_name="outer_diameters_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=expected_coupling_values,
        second_values=measured_peak_positions,
        first_name="expected_coupling_values",
        second_name="measured_peak_positions",
    )

    parsed_rows = parse_core_shell_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_rows.row_count < 2:
        logger.error(
            "Core shell calibration failed because parsed row count=%r.",
            parsed_rows.row_count,
        )
        raise ValueError("At least two valid core shell standard rows are required.")

    updated_table_rows = write_expected_coupling_into_table(
        rows=current_table_rows,
        row_indices=parsed_rows.row_indices,
        expected_coupling_values=expected_coupling_values,
    )

    calibration_standard_mie_relation = build_calibration_standard_mie_relation(
        dense_particle_diameters_nm=dense_outer_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        fallback_particle_diameters_nm=outer_diameters_nm,
        fallback_expected_coupling_values=expected_coupling_values,
        mie_model="Core/Shell Sphere",
        optical_parameters=optical_parameters,
        fallback_core_diameters_nm=core_diameters_nm,
        fallback_shell_thicknesses_nm=shell_thicknesses_nm,
    )

    resolved_metadata = dict(
        metadata or {},
    )

    resolved_metadata["measured_channel"] = str(
        detector_column,
    )

    resolved_metadata.setdefault(
        "calibration_standard",
        "Core/Shell Sphere",
    )

    resolved_metadata.setdefault(
        "calibration_standard_parameters",
        optical_parameters.to_parameter_payload(
            mie_model="Core/Shell Sphere",
            particle_diameter_nm=[
                float(value)
                for value in outer_diameters_nm
            ],
            core_diameter_nm=[
                float(value)
                for value in core_diameters_nm
            ],
            shell_thickness_nm=[
                float(value)
                for value in shell_thicknesses_nm
            ],
            outer_diameter_nm=[
                float(value)
                for value in outer_diameters_nm
            ],
        ),
    )

    resolved_metadata.setdefault(
        "application_note",
        (
            "This calibration stores the instrument response inferred from the "
            "core shell calibration standard. The calibration standard Mie "
            "relation is stored against outer diameter. When applying it to "
            "unknown particles, build a target Mie relation from the target "
            "particle model."
        ),
    )

    logger.debug(
        "Core shell calibration metadata_keys=%r",
        sorted(resolved_metadata.keys()),
    )

    calibration = build_scattering_calibration(
        measured_peak_values=measured_peak_positions,
        theoretical_coupling_values=expected_coupling_values,
        measured_channel=str(
            detector_column,
        ),
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        reference_table=build_reference_table_from_rows(
            rows=updated_table_rows,
        ),
        metadata=resolved_metadata,
        force_zero_intercept=force_zero_intercept,
    )

    build_result = ScatteringCalibrationBuildResult(
        calibration=calibration,
        instrument_response=calibration.instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        updated_table_rows=updated_table_rows,
        measured_peak_positions=measured_peak_positions,
        standard_diameters_nm=outer_diameters_nm,
        standard_coupling_values=expected_coupling_values,
    )

    logger.debug(
        "build_core_shell_scattering_calibration_from_standard_data returning "
        "slope=%r intercept=%r r_squared=%r updated_table_row_count=%r",
        build_result.instrument_response.slope,
        build_result.instrument_response.intercept,
        build_result.instrument_response.r_squared,
        len(build_result.updated_table_rows),
    )

    return build_result


def apply_scattering_calibration(
    *,
    calibration: ScatteringCalibration,
    measured_values: np.ndarray,
    target_mie_relation: MieRelation,
    metadata: Optional[dict[str, Any]] = None,
) -> ScatteringApplicationResult:
    """
    Apply a scattering calibration using a target particle Mie relation.
    """
    logger.debug(
        "apply_scattering_calibration called with calibration_source_channel=%r metadata_keys=%r",
        calibration.source_channel,
        sorted((metadata or {}).keys()),
    )

    application_payload = calibration.apply_to_measured_values(
        measured_values=measured_values,
        target_mie_relation=target_mie_relation,
    )

    estimated_coupling = application_payload["estimated_coupling"]
    mie_equivalent_diameter_nm = application_payload["mie_equivalent_diameter_nm"]

    warnings: list[str] = []

    if not target_mie_relation.is_monotonic:
        warnings.append(
            "Target Mie relation is not monotonic. Diameter inversion may be ambiguous."
        )

    if np.any(
        ~np.isfinite(
            mie_equivalent_diameter_nm,
        )
    ):
        warnings.append(
            "Some measured values are outside the valid target Mie relation range."
        )

    logger.debug(
        "apply_scattering_calibration produced estimated_coupling_count=%r "
        "mie_equivalent_diameter_count=%r warnings=%r",
        len(estimated_coupling),
        len(mie_equivalent_diameter_nm),
        warnings,
    )

    return ScatteringApplicationResult(
        estimated_coupling=[
            float(value)
            for value in estimated_coupling
        ],
        mie_equivalent_diameter_nm=[
            float(value)
            if np.isfinite(
                value,
            )
            else np.nan
            for value in mie_equivalent_diameter_nm
        ],
        target_mie_relation=target_mie_relation,
        warnings=warnings,
        metadata=dict(
            metadata or {},
        ),
    )


def _as_flat_float_array(
    *,
    name: str,
    values: Any,
) -> np.ndarray:
    """
    Convert values to a one dimensional float array and log its content summary.
    """
    try:
        array = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)
    except Exception:
        logger.exception(
            "_as_flat_float_array failed for %s with values=%r",
            name,
            values,
        )
        raise

    _log_array_summary(
        name=name,
        values=array,
    )

    return array


def _validate_same_size(
    *,
    first_values: np.ndarray,
    second_values: np.ndarray,
    first_name: str,
    second_name: str,
) -> None:
    """
    Validate that two arrays have the same size.
    """
    first_values = np.asarray(
        first_values,
    ).reshape(-1)

    second_values = np.asarray(
        second_values,
    ).reshape(-1)

    if first_values.size == second_values.size:
        logger.debug(
            "_validate_same_size passed for %s and %s with size=%r",
            first_name,
            second_name,
            first_values.size,
        )
        return

    logger.error(
        "_validate_same_size failed: %s size=%r, %s size=%r",
        first_name,
        first_values.size,
        second_name,
        second_values.size,
    )

    raise ValueError(
        f"{first_name} and {second_name} must have the same length. "
        f"Got {first_values.size} and {second_values.size}."
    )


def _log_array_summary(
    *,
    name: str,
    values: Any,
) -> None:
    """
    Log a compact numerical summary of an array.
    """
    try:
        array = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)
    except Exception:
        logger.debug(
            "%s summary unavailable because conversion to float array failed. raw_type=%s",
            name,
            type(values).__name__,
        )
        return

    finite_mask = np.isfinite(
        array,
    )

    finite_values = array[finite_mask]

    if finite_values.size == 0:
        logger.debug(
            "%s summary: size=%r finite_count=0 nan_count=%r inf_count=%r values=%r",
            name,
            array.size,
            int(np.sum(np.isnan(array))),
            int(np.sum(np.isinf(array))),
            array.tolist(),
        )
        return

    logger.debug(
        "%s summary: size=%r finite_count=%r nan_count=%r inf_count=%r "
        "min=%r max=%r first_values=%r",
        name,
        array.size,
        finite_values.size,
        int(np.sum(np.isnan(array))),
        int(np.sum(np.isinf(array))),
        float(np.min(finite_values)),
        float(np.max(finite_values)),
        array[:10].tolist(),
    )