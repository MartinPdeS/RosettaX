# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional

import numpy as np

from RosettaX.utils import casting
from RosettaX.workflow.calibration.mie_relation import MieRelation
from RosettaX.workflow.calibration.mie_relation import build_mie_parameter_payload
from RosettaX.workflow.calibration.mie_relation import build_mie_relation_from_arrays


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
    ) -> dict[str, Any]:
        """
        Convert the optical parameters into a serializable Mie parameter payload.
        """
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

    The standard use case is calibration with standardized beads. The standard
    model is only used to estimate the expected coupling of the standards. The
    resulting instrument response can then be applied to other particles using a
    target particle model.
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

        return self.slope * measured_array + self.intercept

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the instrument response into a JSON serializable dictionary.
        """
        return asdict(
            self,
        )

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ScatteringInstrumentResponse":
        """
        Build an instrument response from a dictionary payload.
        """
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

    A scattering calibration stores the instrument response inferred from a
    calibration standard, plus the Mie relation used to compute the standard
    optical coupling values.

    The calibration standard Mie relation documents the bead calibration. It
    should not be blindly reused as the target particle relation for unknown
    samples.
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

        Returns both the intermediate optical coupling and the final target
        model equivalent diameter.
        """
        estimated_coupling = self.measured_to_coupling(
            measured_values,
        )

        mie_equivalent_diameter_nm = target_mie_relation.coupling_to_diameter(
            estimated_coupling,
        )

        return {
            "estimated_coupling": estimated_coupling,
            "mie_equivalent_diameter_nm": mie_equivalent_diameter_nm,
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the scattering calibration into a JSON serializable dictionary.

        source_channel is intentionally exposed at the top level so the
        apply and export workflow can use a common calibration contract.
        """
        source_channel = self.source_channel

        metadata = dict(
            self.metadata,
        )

        metadata["measured_channel"] = source_channel

        return {
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

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "ScatteringCalibration":
        """
        Build a scattering calibration from a dictionary payload.
        """
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

        return cls(
            instrument_response=instrument_response,
            calibration_standard_mie_relation=MieRelation.from_dict(
                payload.get(
                    "calibration_standard_mie_relation",
                    {},
                )
            ),
            reference_table=[
                dict(row)
                for row in payload.get(
                    "reference_table",
                    [],
                )
                if isinstance(row, dict)
            ],
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
        return {
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


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Normalize the selected Mie model name.
    """
    mie_model_string = "" if mie_model is None else str(mie_model).strip()

    if mie_model_string == "Core/Shell Sphere":
        return "Core/Shell Sphere"

    return "Solid Sphere"


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
) -> ParsedSphereStandardRows:
    """
    Extract valid solid sphere calibration standard rows.
    """
    row_indices: list[int] = []
    particle_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    for row_index, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue

        try:
            raw_particle_diameter_nm = row.get(
                "particle_diameter_nm",
            )

            raw_measured_peak_position = row.get(
                "measured_peak_position",
            )

            if raw_particle_diameter_nm in ("", None):
                continue

            if raw_measured_peak_position in ("", None):
                continue

            particle_diameter_nm = float(
                raw_particle_diameter_nm,
            )

            measured_peak_position = float(
                raw_measured_peak_position,
            )

        except Exception:
            continue

        if particle_diameter_nm <= 0.0:
            continue

        if measured_peak_position <= 0.0:
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

    return ParsedSphereStandardRows(
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

    for row_index, row in enumerate(rows or []):
        if not isinstance(row, dict):
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
                continue

            if raw_shell_thickness_nm in ("", None):
                continue

            if raw_measured_peak_position in ("", None):
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
            continue

        if core_diameter_nm <= 0.0:
            continue

        if shell_thickness_nm < 0.0:
            continue

        if measured_peak_position <= 0.0:
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

    return ParsedCoreShellStandardRows(
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


def write_expected_coupling_into_sphere_table(
    *,
    rows: list[dict[str, Any]],
    row_indices: list[int],
    expected_coupling_values: np.ndarray,
) -> list[dict[str, str]]:
    """
    Write modeled coupling values into the calibration standard table rows.
    """
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
            continue

        updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling_value):.6g}"

    return [
        {
            str(key): "" if value is None else str(value)
            for key, value in row.items()
        }
        for row in updated_rows
    ]


def build_reference_table_from_rows(
    *,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build a JSON serializable copy of the calibration standard table.
    """
    reference_table: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        reference_table.append(
            {
                str(key): value
                for key, value in row.items()
            }
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
) -> MieRelation:
    """
    Build the calibration standard Mie relation stored in the calibration payload.
    """
    dense_particle_diameters_nm = np.asarray(
        dense_particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    dense_expected_coupling_values = np.asarray(
        dense_expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    if dense_particle_diameters_nm.size >= 2 and dense_expected_coupling_values.size >= 2:
        diameter_values = dense_particle_diameters_nm
        coupling_values = dense_expected_coupling_values

    else:
        diameter_values = np.asarray(
            fallback_particle_diameters_nm,
            dtype=float,
        ).reshape(-1)

        coupling_values = np.asarray(
            fallback_expected_coupling_values,
            dtype=float,
        ).reshape(-1)

    parameter_payload = optical_parameters.to_parameter_payload(
        mie_model=mie_model,
        particle_diameter_nm=[
            float(value)
            for value in np.asarray(
                fallback_particle_diameters_nm,
                dtype=float,
            ).reshape(-1)
        ],
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
    measured_array = np.asarray(
        measured_peak_values,
        dtype=float,
    )

    coupling_array = np.asarray(
        theoretical_coupling_values,
        dtype=float,
    )

    valid_mask = (
        np.isfinite(
            measured_array,
        )
        & np.isfinite(
            coupling_array,
        )
    )

    measured_array = measured_array[valid_mask]
    coupling_array = coupling_array[valid_mask]

    if measured_array.size < 2:
        raise ValueError("At least two valid calibration points are required.")

    if force_zero_intercept:
        nonzero_mask = measured_array != 0.0
        measured_array = measured_array[nonzero_mask]
        coupling_array = coupling_array[nonzero_mask]

    if measured_array.size < 2:
        raise ValueError("At least two nonzero measured values are required.")

    if force_zero_intercept:
        denominator = float(
            np.sum(
                measured_array * measured_array,
            )
        )

        if denominator == 0.0:
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
    observed_array = np.asarray(
        observed_values,
        dtype=float,
    )

    predicted_array = np.asarray(
        predicted_values,
        dtype=float,
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

    if total_sum_of_squares == 0.0:
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
    instrument_response = fit_linear_instrument_response(
        measured_peak_values=measured_peak_values,
        theoretical_coupling_values=theoretical_coupling_values,
        measured_channel=measured_channel,
        force_zero_intercept=force_zero_intercept,
    )

    return ScatteringCalibration(
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

    This function does not compute Mie coupling. It receives the coupling arrays
    from the caller and builds the saved calibration object, updated table rows,
    instrument response, and calibration standard Mie relation.
    """
    measured_peak_positions = np.asarray(
        measured_peak_positions,
        dtype=float,
    ).reshape(-1)

    particle_diameters_nm = np.asarray(
        particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    expected_coupling_values = np.asarray(
        expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    if measured_peak_positions.size < 2:
        raise ValueError("At least two measured peak positions are required.")

    if particle_diameters_nm.size != measured_peak_positions.size:
        raise ValueError("particle_diameters_nm and measured_peak_positions must have the same length.")

    if expected_coupling_values.size != measured_peak_positions.size:
        raise ValueError("expected_coupling_values and measured_peak_positions must have the same length.")

    parsed_rows = parse_sphere_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_rows.row_count < 2:
        raise ValueError("At least two valid solid sphere standard rows are required.")

    updated_table_rows = write_expected_coupling_into_sphere_table(
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

    return ScatteringCalibrationBuildResult(
        calibration=calibration,
        instrument_response=calibration.instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        updated_table_rows=updated_table_rows,
        measured_peak_positions=measured_peak_positions,
        standard_diameters_nm=particle_diameters_nm,
        standard_coupling_values=expected_coupling_values,
    )


def apply_scattering_calibration(
    *,
    calibration: ScatteringCalibration,
    measured_values: np.ndarray,
    target_mie_relation: MieRelation,
    metadata: Optional[dict[str, Any]] = None,
) -> ScatteringApplicationResult:
    """
    Apply a scattering calibration using a target particle Mie relation.

    The target relation is intentionally supplied at application time. This is
    the default workflow for applying standard based instrument calibration to
    other particle classes.
    """
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