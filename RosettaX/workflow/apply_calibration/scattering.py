# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from RosettaX.pages.p03_scattering.backend import BackEnd
from RosettaX.workflow.calibration.mie_relation import MieRelation
from RosettaX.workflow.calibration.mie_relation import build_diameter_grid
from RosettaX.workflow.calibration.mie_relation import build_mie_parameter_payload
from RosettaX.workflow.calibration.mie_relation import build_mie_relation_from_arrays
from RosettaX.workflow.calibration.mie_relation import relation_is_strictly_monotonic
from RosettaX.workflow.calibration.scattering import ScatteringCalibration


@dataclass(frozen=True)
class ScatteringTargetModelParameters:
    """
    Target particle model parameters used when applying a scattering calibration.
    """

    mie_model: str
    medium_refractive_index: float
    particle_refractive_index: float
    diameter_min_nm: float
    diameter_max_nm: float
    diameter_count: int

    @classmethod
    def from_raw_values(
        cls,
        *,
        target_mie_model: Any,
        target_medium_refractive_index: Any,
        target_particle_refractive_index: Any,
        target_diameter_min_nm: Any,
        target_diameter_max_nm: Any,
        target_diameter_count: Any,
    ) -> "ScatteringTargetModelParameters":
        """
        Parse target model values from Dash controls.
        """
        resolved_mie_model = str(
            target_mie_model or "Solid Sphere",
        ).strip()

        if resolved_mie_model != "Solid Sphere":
            raise ValueError(
                "Only Solid Sphere target scattering model is currently supported."
            )

        resolved_medium_refractive_index = float(
            target_medium_refractive_index,
        )

        resolved_particle_refractive_index = float(
            target_particle_refractive_index,
        )

        resolved_diameter_min_nm = float(
            target_diameter_min_nm,
        )

        resolved_diameter_max_nm = float(
            target_diameter_max_nm,
        )

        resolved_diameter_count = int(
            target_diameter_count,
        )

        if resolved_medium_refractive_index <= 0.0:
            raise ValueError("Target medium refractive index must be positive.")

        if resolved_particle_refractive_index <= 0.0:
            raise ValueError("Target particle refractive index must be positive.")

        if resolved_diameter_min_nm <= 0.0:
            raise ValueError("Target diameter min must be positive.")

        if resolved_diameter_max_nm <= resolved_diameter_min_nm:
            raise ValueError("Target diameter max must be greater than target diameter min.")

        if resolved_diameter_count < 2:
            raise ValueError("Target diameter count must be at least 2.")

        return cls(
            mie_model=resolved_mie_model,
            medium_refractive_index=resolved_medium_refractive_index,
            particle_refractive_index=resolved_particle_refractive_index,
            diameter_min_nm=resolved_diameter_min_nm,
            diameter_max_nm=resolved_diameter_max_nm,
            diameter_count=resolved_diameter_count,
        )


@dataclass(frozen=True)
class ScatteringOutputColumns:
    """
    Output column names produced by scattering calibration application.
    """

    estimated_coupling: str
    mie_equivalent_diameter_nm: str

    def as_list(self) -> list[str]:
        """
        Return output column names.
        """
        return [
            self.estimated_coupling,
            self.mie_equivalent_diameter_nm,
        ]


@dataclass(frozen=True)
class MonotonicDiameterInterval:
    """
    Strictly monotonic diameter interval in a Mie relation.

    The interval is a branch over which coupling to diameter inversion is
    unambiguous.
    """

    diameter_min_nm: float
    diameter_max_nm: float
    coupling_min: float
    coupling_max: float
    point_count: int
    trend: str
    start_index: int
    end_index: int

    @property
    def diameter_width_nm(self) -> float:
        """
        Diameter width of the branch.
        """
        return self.diameter_max_nm - self.diameter_min_nm

    def to_message_fragment(self) -> str:
        """
        Format the interval for user facing messages.
        """
        return (
            f"{self.diameter_min_nm:.6g} to {self.diameter_max_nm:.6g} nm "
            f"({self.trend}, {self.point_count} points)"
        )


@dataclass(frozen=True)
class MonotonicRelationResolution:
    """
    Resolved monotonic target relation used for inversion.
    """

    target_mie_relation: MieRelation
    selected_interval: Optional[MonotonicDiameterInterval]
    used_auto_largest_branch: bool
    warnings: list[str]


@dataclass(frozen=True)
class ScatteringApplyResult:
    """
    Result of applying a scattering calibration to a dataframe.
    """

    dataframe: Any
    output_columns: list[str]
    warnings: list[str]
    target_mie_relation: MieRelation


def calibration_is_scattering_v2(
    calibration_payload: dict[str, Any],
) -> bool:
    """
    Return whether the payload is a scattering version 2 calibration.
    """
    if not isinstance(calibration_payload, dict):
        return False

    calibration_type = str(
        calibration_payload.get(
            "calibration_type",
            "",
        )
    ).strip()

    calibration_version = int(
        calibration_payload.get(
            "version",
            0,
        )
        or 0
    )

    return calibration_type == "scattering" and calibration_version >= 2


def build_scattering_output_columns(
    *,
    source_channel: str,
) -> ScatteringOutputColumns:
    """
    Build scattering output column names.
    """
    source_channel_string = str(
        source_channel,
    )

    return ScatteringOutputColumns(
        estimated_coupling=f"{source_channel_string}_estimated_coupling",
        mie_equivalent_diameter_nm=f"{source_channel_string}_mie_equivalent_diameter_nm",
    )


def apply_scattering_calibration_to_dataframe(
    *,
    dataframe: Any,
    source_channel: str,
    calibration_payload: dict[str, Any],
    target_model_parameters: ScatteringTargetModelParameters,
    metadata: Optional[dict[str, Any]] = None,
) -> ScatteringApplyResult:
    """
    Apply a scattering calibration to a dataframe.

    The source channel is preserved. Two derived columns are added:

    - estimated coupling
    - target model Mie equivalent diameter

    If the full target Mie relation is not strictly monotonic, the widest
    strictly monotonic branch is selected automatically. Diameter inversion uses
    linear extrapolation outside the selected branch coupling range.
    """
    del metadata

    if source_channel not in dataframe.columns:
        raise ValueError(
            f'Source channel "{source_channel}" is missing from the input dataframe.'
        )

    full_target_mie_relation = build_target_mie_relation(
        calibration_payload=calibration_payload,
        target_model_parameters=target_model_parameters,
    )

    relation_resolution = resolve_monotonic_target_mie_relation(
        target_mie_relation=full_target_mie_relation,
    )

    scattering_calibration = ScatteringCalibration.from_dict(
        calibration_payload,
    )

    source_values = dataframe[source_channel].to_numpy(
        copy=True,
    )

    estimated_coupling = scattering_calibration.measured_to_coupling(
        source_values,
    )

    mie_equivalent_diameter_nm = coupling_to_diameter_with_linear_extrapolation(
        target_mie_relation=relation_resolution.target_mie_relation,
        coupling_values=estimated_coupling,
    )

    output_columns = build_scattering_output_columns(
        source_channel=source_channel,
    )

    output_dataframe = dataframe.copy(
        deep=True,
    )

    output_dataframe[output_columns.estimated_coupling] = np.asarray(
        estimated_coupling,
        dtype=float,
    )

    output_dataframe[output_columns.mie_equivalent_diameter_nm] = np.asarray(
        mie_equivalent_diameter_nm,
        dtype=float,
    )

    return ScatteringApplyResult(
        dataframe=output_dataframe,
        output_columns=output_columns.as_list(),
        warnings=list(
            relation_resolution.warnings,
        ),
        target_mie_relation=relation_resolution.target_mie_relation,
    )


def resolve_monotonic_target_mie_relation(
    *,
    target_mie_relation: MieRelation,
) -> MonotonicRelationResolution:
    """
    Resolve the monotonic target relation used for diameter inversion.

    If the full relation is strictly monotonic, it is used directly. If not, the
    widest strictly monotonic branch is selected automatically.
    """
    diameter_values_nm, theoretical_coupling_values = get_finite_positive_mie_relation_arrays(
        target_mie_relation=target_mie_relation,
    )

    if relation_is_strictly_monotonic(
        values=theoretical_coupling_values,
    ):
        return MonotonicRelationResolution(
            target_mie_relation=target_mie_relation,
            selected_interval=None,
            used_auto_largest_branch=False,
            warnings=[],
        )

    monotonic_intervals = find_strictly_monotonic_diameter_intervals(
        diameter_nm=diameter_values_nm,
        theoretical_coupling=theoretical_coupling_values,
    )

    if not monotonic_intervals:
        raise ValueError(
            (
                "Target Mie relation is not strictly monotonic and no valid "
                "monotonic branch was detected. Try increasing the diameter point "
                "count or reducing the target diameter range."
            )
        )

    selected_interval = select_largest_monotonic_interval(
        monotonic_intervals=monotonic_intervals,
    )

    branch_mie_relation = build_monotonic_branch_mie_relation(
        target_mie_relation=target_mie_relation,
        selected_interval=selected_interval,
    )

    warning = (
        "Target Mie relation was not strictly monotonic over the full selected "
        "diameter range. RosettaX automatically selected the largest monotonic "
        f"branch: {selected_interval.to_message_fragment()}. Linear extrapolation "
        "is enabled outside the selected branch coupling range."
    )

    return MonotonicRelationResolution(
        target_mie_relation=branch_mie_relation,
        selected_interval=selected_interval,
        used_auto_largest_branch=True,
        warnings=[
            warning,
        ],
    )


def select_largest_monotonic_interval(
    *,
    monotonic_intervals: list[MonotonicDiameterInterval],
) -> MonotonicDiameterInterval:
    """
    Select the widest monotonic branch.

    Ties are resolved by keeping the branch with more points.
    """
    if not monotonic_intervals:
        raise ValueError("No monotonic intervals were provided.")

    return sorted(
        monotonic_intervals,
        key=lambda interval: (
            interval.diameter_width_nm,
            interval.point_count,
        ),
        reverse=True,
    )[0]


def build_monotonic_branch_mie_relation(
    *,
    target_mie_relation: MieRelation,
    selected_interval: MonotonicDiameterInterval,
) -> MieRelation:
    """
    Crop a Mie relation to one monotonic branch.
    """
    diameter_values_nm, theoretical_coupling_values = get_finite_positive_mie_relation_arrays(
        target_mie_relation=target_mie_relation,
    )

    branch_diameter_values_nm = diameter_values_nm[
        selected_interval.start_index : selected_interval.end_index + 1
    ]

    branch_coupling_values = theoretical_coupling_values[
        selected_interval.start_index : selected_interval.end_index + 1
    ]

    if branch_diameter_values_nm.size < 2:
        raise ValueError(
            "Selected monotonic branch has fewer than two points."
        )

    if not relation_is_strictly_monotonic(
        values=branch_coupling_values,
    ):
        raise ValueError(
            "Selected monotonic branch is not strictly monotonic."
        )

    parameters = dict(
        target_mie_relation.parameters,
    )

    parameters.update(
        {
            "auto_largest_monotonic_branch": True,
            "branch_diameter_min_nm": selected_interval.diameter_min_nm,
            "branch_diameter_max_nm": selected_interval.diameter_max_nm,
            "branch_coupling_min": selected_interval.coupling_min,
            "branch_coupling_max": selected_interval.coupling_max,
            "branch_trend": selected_interval.trend,
            "extrapolation_enabled": True,
        }
    )

    return build_mie_relation_from_arrays(
        diameter_nm=branch_diameter_values_nm,
        theoretical_coupling=branch_coupling_values,
        mie_model=target_mie_relation.mie_model,
        parameters=parameters,
        relation_role=target_mie_relation.relation_role,
    )


def coupling_to_diameter_with_linear_extrapolation(
    *,
    target_mie_relation: MieRelation,
    coupling_values: Any,
) -> np.ndarray:
    """
    Convert coupling to diameter with linear extrapolation.

    This assumes the target relation is strictly monotonic. Coupling values
    outside the branch range are extrapolated using the first or last two points.
    """
    coupling_array = np.asarray(
        coupling_values,
        dtype=float,
    )

    diameter_grid = np.asarray(
        target_mie_relation.diameter_nm,
        dtype=float,
    ).reshape(-1)

    coupling_grid = np.asarray(
        target_mie_relation.theoretical_coupling,
        dtype=float,
    ).reshape(-1)

    if diameter_grid.size != coupling_grid.size:
        raise ValueError(
            "diameter_nm and theoretical_coupling must have the same length."
        )

    finite_mask = (
        np.isfinite(diameter_grid)
        & np.isfinite(coupling_grid)
    )

    diameter_grid = diameter_grid[finite_mask]
    coupling_grid = coupling_grid[finite_mask]

    if diameter_grid.size < 2:
        return np.full_like(
            coupling_array,
            np.nan,
            dtype=float,
        )

    sorting_indices = np.argsort(
        coupling_grid,
    )

    sorted_coupling_grid = coupling_grid[sorting_indices]
    sorted_diameter_grid = diameter_grid[sorting_indices]

    unique_coupling_grid, unique_indices = np.unique(
        sorted_coupling_grid,
        return_index=True,
    )

    unique_diameter_grid = sorted_diameter_grid[unique_indices]

    if unique_coupling_grid.size < 2:
        return np.full_like(
            coupling_array,
            np.nan,
            dtype=float,
        )

    interpolated_diameter = np.interp(
        coupling_array,
        unique_coupling_grid,
        unique_diameter_grid,
    )

    lower_mask = coupling_array < unique_coupling_grid[0]
    upper_mask = coupling_array > unique_coupling_grid[-1]

    if np.any(lower_mask):
        interpolated_diameter[lower_mask] = extrapolate_linearly(
            x_values=coupling_array[lower_mask],
            x0=unique_coupling_grid[0],
            y0=unique_diameter_grid[0],
            x1=unique_coupling_grid[1],
            y1=unique_diameter_grid[1],
        )

    if np.any(upper_mask):
        interpolated_diameter[upper_mask] = extrapolate_linearly(
            x_values=coupling_array[upper_mask],
            x0=unique_coupling_grid[-2],
            y0=unique_diameter_grid[-2],
            x1=unique_coupling_grid[-1],
            y1=unique_diameter_grid[-1],
        )

    interpolated_diameter[
        ~np.isfinite(
            coupling_array,
        )
    ] = np.nan

    return interpolated_diameter


def extrapolate_linearly(
    *,
    x_values: np.ndarray,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> np.ndarray:
    """
    Linear extrapolation through two points.
    """
    if x1 == x0:
        return np.full_like(
            np.asarray(
                x_values,
                dtype=float,
            ),
            np.nan,
            dtype=float,
        )

    slope = (y1 - y0) / (x1 - x0)

    return y0 + slope * (
        np.asarray(
            x_values,
            dtype=float,
        )
        - x0
    )


def validate_target_mie_relation_for_diameter_inversion(
    *,
    target_mie_relation: MieRelation,
    target_model_parameters: ScatteringTargetModelParameters,
) -> None:
    """
    Validate that the target Mie relation can be inverted unambiguously.

    This function is kept for callers that still want strict validation. The
    apply workflow now uses ``resolve_monotonic_target_mie_relation`` instead.
    """
    diameter_values_nm, theoretical_coupling_values = get_finite_positive_mie_relation_arrays(
        target_mie_relation=target_mie_relation,
    )

    if relation_is_strictly_monotonic(
        values=theoretical_coupling_values,
    ):
        return

    monotonic_intervals = find_strictly_monotonic_diameter_intervals(
        diameter_nm=diameter_values_nm,
        theoretical_coupling=theoretical_coupling_values,
    )

    interval_message = format_monotonic_interval_suggestions(
        monotonic_intervals=monotonic_intervals,
        max_interval_count=8,
    )

    raise ValueError(
        (
            "Target Mie relation is not strictly monotonic over the selected "
            f"diameter range [{target_model_parameters.diameter_min_nm:.6g}, "
            f"{target_model_parameters.diameter_max_nm:.6g}] nm. "
            "Diameter inversion would be ambiguous because several diameters "
            "can produce the same coupling. Reduce the target diameter range "
            "to one monotonic interval. "
            f"{interval_message}"
        )
    )


def get_finite_positive_mie_relation_arrays(
    *,
    target_mie_relation: MieRelation,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return finite positive diameter and coupling arrays from a Mie relation.
    """
    diameter_values_nm = np.asarray(
        target_mie_relation.diameter_nm,
        dtype=float,
    ).reshape(-1)

    theoretical_coupling_values = np.asarray(
        target_mie_relation.theoretical_coupling,
        dtype=float,
    ).reshape(-1)

    if diameter_values_nm.size != theoretical_coupling_values.size:
        raise ValueError(
            "Target Mie relation is invalid: diameter and coupling arrays have different lengths."
        )

    finite_positive_mask = (
        np.isfinite(diameter_values_nm)
        & np.isfinite(theoretical_coupling_values)
        & (diameter_values_nm > 0.0)
        & (theoretical_coupling_values > 0.0)
    )

    diameter_values_nm = diameter_values_nm[finite_positive_mask]
    theoretical_coupling_values = theoretical_coupling_values[finite_positive_mask]

    if diameter_values_nm.size < 2:
        raise ValueError(
            "Target Mie relation is invalid: fewer than two finite positive coupling points were computed."
        )

    sorting_indices = np.argsort(
        diameter_values_nm,
    )

    return (
        diameter_values_nm[sorting_indices],
        theoretical_coupling_values[sorting_indices],
    )


def find_strictly_monotonic_diameter_intervals(
    *,
    diameter_nm: Any,
    theoretical_coupling: Any,
    minimum_point_count: int = 3,
) -> list[MonotonicDiameterInterval]:
    """
    Find strictly monotonic diameter intervals in a Mie relation.

    The algorithm splits the curve whenever the sign of the local coupling
    derivative changes. Flat points are treated as branch boundaries because
    strict monotonic inversion cannot include repeated coupling values.
    """
    diameter_values_nm = np.asarray(
        diameter_nm,
        dtype=float,
    ).reshape(-1)

    theoretical_coupling_values = np.asarray(
        theoretical_coupling,
        dtype=float,
    ).reshape(-1)

    if diameter_values_nm.size != theoretical_coupling_values.size:
        raise ValueError(
            "diameter_nm and theoretical_coupling must have the same length."
        )

    finite_positive_mask = (
        np.isfinite(diameter_values_nm)
        & np.isfinite(theoretical_coupling_values)
        & (diameter_values_nm > 0.0)
        & (theoretical_coupling_values > 0.0)
    )

    diameter_values_nm = diameter_values_nm[finite_positive_mask]
    theoretical_coupling_values = theoretical_coupling_values[finite_positive_mask]

    if diameter_values_nm.size < minimum_point_count:
        return []

    sorting_indices = np.argsort(
        diameter_values_nm,
    )

    diameter_values_nm = diameter_values_nm[sorting_indices]
    theoretical_coupling_values = theoretical_coupling_values[sorting_indices]

    coupling_differences = np.diff(
        theoretical_coupling_values,
    )

    difference_signs = np.sign(
        coupling_differences,
    )

    intervals: list[MonotonicDiameterInterval] = []

    start_index = 0
    current_sign = 0.0

    for difference_index, difference_sign in enumerate(difference_signs):
        if difference_sign == 0.0:
            intervals.extend(
                build_interval_if_valid(
                    diameter_values_nm=diameter_values_nm,
                    theoretical_coupling_values=theoretical_coupling_values,
                    start_index=start_index,
                    end_index=difference_index,
                    minimum_point_count=minimum_point_count,
                )
            )

            start_index = difference_index + 1
            current_sign = 0.0
            continue

        if current_sign == 0.0:
            current_sign = difference_sign
            continue

        if difference_sign != current_sign:
            intervals.extend(
                build_interval_if_valid(
                    diameter_values_nm=diameter_values_nm,
                    theoretical_coupling_values=theoretical_coupling_values,
                    start_index=start_index,
                    end_index=difference_index,
                    minimum_point_count=minimum_point_count,
                )
            )

            start_index = difference_index
            current_sign = difference_sign

    intervals.extend(
        build_interval_if_valid(
            diameter_values_nm=diameter_values_nm,
            theoretical_coupling_values=theoretical_coupling_values,
            start_index=start_index,
            end_index=diameter_values_nm.size - 1,
            minimum_point_count=minimum_point_count,
        )
    )

    return intervals


def build_interval_if_valid(
    *,
    diameter_values_nm: np.ndarray,
    theoretical_coupling_values: np.ndarray,
    start_index: int,
    end_index: int,
    minimum_point_count: int,
) -> list[MonotonicDiameterInterval]:
    """
    Build one monotonic interval if it is valid.
    """
    start_index = int(
        start_index,
    )

    end_index = int(
        end_index,
    )

    if end_index <= start_index:
        return []

    interval_diameter_values_nm = diameter_values_nm[start_index : end_index + 1]
    interval_coupling_values = theoretical_coupling_values[start_index : end_index + 1]

    if interval_diameter_values_nm.size < minimum_point_count:
        return []

    if not relation_is_strictly_monotonic(
        values=interval_coupling_values,
    ):
        return []

    if interval_coupling_values[-1] > interval_coupling_values[0]:
        trend = "increasing"

    else:
        trend = "decreasing"

    return [
        MonotonicDiameterInterval(
            diameter_min_nm=float(
                interval_diameter_values_nm[0],
            ),
            diameter_max_nm=float(
                interval_diameter_values_nm[-1],
            ),
            coupling_min=float(
                np.min(
                    interval_coupling_values,
                )
            ),
            coupling_max=float(
                np.max(
                    interval_coupling_values,
                )
            ),
            point_count=int(
                interval_diameter_values_nm.size,
            ),
            trend=trend,
            start_index=start_index,
            end_index=end_index,
        )
    ]


def format_monotonic_interval_suggestions(
    *,
    monotonic_intervals: list[MonotonicDiameterInterval],
    max_interval_count: int = 8,
) -> str:
    """
    Format monotonic interval suggestions for an error or status message.
    """
    if not monotonic_intervals:
        return (
            "No valid monotonic interval with enough points was detected. "
            "Try increasing the diameter point count or choosing a narrower diameter range."
        )

    sorted_intervals = sorted(
        monotonic_intervals,
        key=lambda interval: (
            interval.diameter_width_nm,
            interval.point_count,
        ),
        reverse=True,
    )

    selected_intervals = sorted_intervals[: int(max_interval_count)]

    interval_fragments = [
        interval.to_message_fragment()
        for interval in selected_intervals
    ]

    interval_text = "; ".join(
        interval_fragments,
    )

    if len(sorted_intervals) > len(selected_intervals):
        remaining_count = len(sorted_intervals) - len(selected_intervals)

        return (
            f"Suggested monotonic intervals: {interval_text}. "
            f"{remaining_count} additional shorter interval(s) were omitted."
        )

    return f"Suggested monotonic intervals: {interval_text}."


def build_target_mie_relation(
    *,
    calibration_payload: dict[str, Any],
    target_model_parameters: ScatteringTargetModelParameters,
) -> MieRelation:
    """
    Build the target particle Mie relation used for diameter inversion.
    """
    calibration_standard_parameters = get_calibration_standard_parameters(
        calibration_payload,
    )

    diameter_grid_nm = build_diameter_grid(
        diameter_min_nm=target_model_parameters.diameter_min_nm,
        diameter_max_nm=target_model_parameters.diameter_max_nm,
        diameter_count=target_model_parameters.diameter_count,
    )

    optical_power_watt = float(
        calibration_standard_parameters.get(
            "optical_power_watt",
            1.0,
        )
    )

    source_numerical_aperture = float(
        calibration_standard_parameters.get(
            "source_numerical_aperture",
            0.1,
        )
    )

    wavelength_nm = float(
        calibration_standard_parameters.get(
            "wavelength_nm",
        )
    )

    detector_numerical_aperture = float(
        calibration_standard_parameters.get(
            "detector_numerical_aperture",
        )
    )

    detector_cache_numerical_aperture = float(
        calibration_standard_parameters.get(
            "detector_cache_numerical_aperture",
            0.0,
        )
    )

    detector_phi_angle_degree = float(
        calibration_standard_parameters.get(
            "detector_phi_angle_degree",
            0.0,
        )
    )

    detector_gamma_angle_degree = float(
        calibration_standard_parameters.get(
            "detector_gamma_angle_degree",
            0.0,
        )
    )

    polarization_angle_degree = float(
        calibration_standard_parameters.get(
            "polarization_angle_degree",
            0.0,
        )
    )

    detector_sampling = int(
        calibration_standard_parameters.get(
            "detector_sampling",
            600,
        )
    )

    modeled_coupling_result = BackEnd.compute_modeled_coupling_from_diameters(
        particle_diameters_nm=diameter_grid_nm,
        wavelength_nm=wavelength_nm,
        source_numerical_aperture=source_numerical_aperture,
        optical_power_watt=optical_power_watt,
        detector_numerical_aperture=detector_numerical_aperture,
        medium_refractive_index=target_model_parameters.medium_refractive_index,
        particle_refractive_index=target_model_parameters.particle_refractive_index,
        detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        detector_phi_offset_degree=detector_phi_angle_degree,
        detector_gamma_offset_degree=detector_gamma_angle_degree,
        polarization_angle_degree=polarization_angle_degree,
        detector_sampling=detector_sampling,
    )

    target_relation_parameters = build_mie_parameter_payload(
        mie_model=target_model_parameters.mie_model,
        medium_refractive_index=target_model_parameters.medium_refractive_index,
        particle_refractive_index=target_model_parameters.particle_refractive_index,
        wavelength_nm=wavelength_nm,
        detector_numerical_aperture=detector_numerical_aperture,
        detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        blocker_bar_numerical_aperture=calibration_standard_parameters.get(
            "blocker_bar_numerical_aperture",
            None,
        ),
        detector_sampling=detector_sampling,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
        diameter_min_nm=target_model_parameters.diameter_min_nm,
        diameter_max_nm=target_model_parameters.diameter_max_nm,
        diameter_count=target_model_parameters.diameter_count,
    )

    target_relation_parameters.update(
        {
            "optical_power_watt": optical_power_watt,
            "source_numerical_aperture": source_numerical_aperture,
            "polarization_angle_degree": polarization_angle_degree,
            "extrapolation_enabled": True,
            "non_monotonic_policy": "auto_largest_branch",
        }
    )

    return build_mie_relation_from_arrays(
        diameter_nm=np.asarray(
            modeled_coupling_result.particle_diameters_nm,
            dtype=float,
        ),
        theoretical_coupling=np.asarray(
            modeled_coupling_result.expected_coupling_values,
            dtype=float,
        ),
        mie_model=target_model_parameters.mie_model,
        parameters=target_relation_parameters,
        relation_role="target_particle",
    )


def get_calibration_standard_parameters(
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve optical geometry parameters stored in a scattering calibration.
    """
    mie_relation_payload = calibration_payload.get(
        "calibration_standard_mie_relation",
    )

    if isinstance(mie_relation_payload, dict):
        relation_parameters = mie_relation_payload.get(
            "parameters",
        )

        if isinstance(relation_parameters, dict):
            return dict(
                relation_parameters,
            )

    metadata = calibration_payload.get(
        "metadata",
    )

    if isinstance(metadata, dict):
        calibration_standard_parameters = metadata.get(
            "calibration_standard_parameters",
        )

        if isinstance(calibration_standard_parameters, dict):
            return dict(
                calibration_standard_parameters,
            )

    raise ValueError(
        "Scattering calibration payload is missing calibration standard optical parameters."
    )