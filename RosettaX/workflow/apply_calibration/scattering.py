# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np

from RosettaX.pages.p03_scattering.backend import BackEnd
from RosettaX.workflow.calibration.mie_relation import MieRelation
from RosettaX.workflow.calibration.mie_relation import build_diameter_grid
from RosettaX.workflow.calibration.mie_relation import build_mie_parameter_payload
from RosettaX.workflow.calibration.mie_relation import build_mie_relation_from_arrays
from RosettaX.workflow.calibration.mie_relation import relation_is_strictly_monotonic
from RosettaX.workflow.calibration.scattering import ScatteringCalibration


logger = logging.getLogger(__name__)


SOLID_SPHERE_MODEL_NAME = "Solid Sphere"
CORE_SHELL_SPHERE_MODEL_NAME = "Core/Shell Sphere"


@dataclass(frozen=True)
class ScatteringTargetModelParameters:
    """
    Target particle model parameters used when applying a scattering calibration.

    For the solid sphere model, ``particle_refractive_index`` is required and
    the diameter grid is interpreted as the solid sphere diameter.

    For the core shell sphere model, ``core_refractive_index``,
    ``shell_refractive_index``, and ``shell_thickness_nm`` are required. The
    diameter grid is interpreted as the core diameter grid. The shell thickness
    is constant and provided by the user.
    """

    mie_model: str
    medium_refractive_index: float
    diameter_min_nm: float
    diameter_max_nm: float
    diameter_count: int
    particle_refractive_index: Optional[float] = None
    core_refractive_index: Optional[float] = None
    shell_refractive_index: Optional[float] = None
    shell_thickness_nm: Optional[float] = None

    @classmethod
    def from_raw_values(
        cls,
        *,
        target_mie_model: Any,
        target_medium_refractive_index: Any,
        target_particle_refractive_index: Any = None,
        target_core_refractive_index: Any = None,
        target_shell_refractive_index: Any = None,
        target_shell_thickness_nm: Any = None,
        target_diameter_min_nm: Any,
        target_diameter_max_nm: Any,
        target_diameter_count: Any,
    ) -> "ScatteringTargetModelParameters":
        """
        Parse target model values from Dash controls.
        """
        logger.debug(
            "ScatteringTargetModelParameters.from_raw_values called with "
            "target_mie_model=%r target_medium_refractive_index=%r "
            "target_particle_refractive_index=%r target_core_refractive_index=%r "
            "target_shell_refractive_index=%r target_shell_thickness_nm=%r "
            "target_diameter_min_nm=%r target_diameter_max_nm=%r "
            "target_diameter_count=%r",
            target_mie_model,
            target_medium_refractive_index,
            target_particle_refractive_index,
            target_core_refractive_index,
            target_shell_refractive_index,
            target_shell_thickness_nm,
            target_diameter_min_nm,
            target_diameter_max_nm,
            target_diameter_count,
        )

        resolved_mie_model = resolve_target_mie_model(
            target_mie_model,
        )

        resolved_medium_refractive_index = _required_positive_float(
            value=target_medium_refractive_index,
            name="target_medium_refractive_index",
        )

        resolved_diameter_min_nm = _required_positive_float(
            value=target_diameter_min_nm,
            name="target_diameter_min_nm",
        )

        resolved_diameter_max_nm = _required_positive_float(
            value=target_diameter_max_nm,
            name="target_diameter_max_nm",
        )

        resolved_diameter_count = _required_integer(
            value=target_diameter_count,
            name="target_diameter_count",
        )

        if resolved_diameter_max_nm <= resolved_diameter_min_nm:
            raise ValueError("Target diameter max must be greater than target diameter min.")

        if resolved_diameter_count < 2:
            raise ValueError("Target diameter count must be at least 2.")

        if resolved_mie_model == SOLID_SPHERE_MODEL_NAME:
            resolved_particle_refractive_index = _required_positive_float(
                value=target_particle_refractive_index,
                name="target_particle_refractive_index",
            )

            parameters = cls(
                mie_model=resolved_mie_model,
                medium_refractive_index=resolved_medium_refractive_index,
                particle_refractive_index=resolved_particle_refractive_index,
                diameter_min_nm=resolved_diameter_min_nm,
                diameter_max_nm=resolved_diameter_max_nm,
                diameter_count=resolved_diameter_count,
            )

            logger.debug(
                "ScatteringTargetModelParameters.from_raw_values returning solid sphere parameters=%r",
                parameters,
            )

            return parameters

        resolved_core_refractive_index = _required_positive_float(
            value=target_core_refractive_index,
            name="target_core_refractive_index",
        )

        resolved_shell_refractive_index = _required_positive_float(
            value=target_shell_refractive_index,
            name="target_shell_refractive_index",
        )

        resolved_shell_thickness_nm = _required_non_negative_float(
            value=target_shell_thickness_nm,
            name="target_shell_thickness_nm",
        )

        parameters = cls(
            mie_model=resolved_mie_model,
            medium_refractive_index=resolved_medium_refractive_index,
            core_refractive_index=resolved_core_refractive_index,
            shell_refractive_index=resolved_shell_refractive_index,
            shell_thickness_nm=resolved_shell_thickness_nm,
            diameter_min_nm=resolved_diameter_min_nm,
            diameter_max_nm=resolved_diameter_max_nm,
            diameter_count=resolved_diameter_count,
        )

        logger.debug(
            "ScatteringTargetModelParameters.from_raw_values returning core shell parameters=%r",
            parameters,
        )

        return parameters


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
        logger.debug(
            "calibration_is_scattering_v2 returning False because payload is not a dict. "
            "payload_type=%s",
            type(calibration_payload).__name__,
        )
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

    result = calibration_type == "scattering" and calibration_version >= 2

    logger.debug(
        "calibration_is_scattering_v2 calibration_type=%r calibration_version=%r result=%r",
        calibration_type,
        calibration_version,
        result,
    )

    return result


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

    output_columns = ScatteringOutputColumns(
        estimated_coupling=f"{source_channel_string}_estimated_coupling",
        mie_equivalent_diameter_nm=f"{source_channel_string}_mie_equivalent_diameter_nm",
    )

    logger.debug(
        "build_scattering_output_columns returning output_columns=%r",
        output_columns,
    )

    return output_columns


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
    logger.debug(
        "apply_scattering_calibration_to_dataframe called with source_channel=%r "
        "dataframe_shape=%r target_model_parameters=%r metadata_keys=%r",
        source_channel,
        getattr(dataframe, "shape", None),
        target_model_parameters,
        sorted((metadata or {}).keys()),
    )

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

    _log_array_summary(
        name="apply_source_values",
        values=source_values,
    )

    estimated_coupling = scattering_calibration.measured_to_coupling(
        source_values,
    )

    _log_array_summary(
        name="apply_estimated_coupling",
        values=estimated_coupling,
    )

    mie_equivalent_diameter_nm = coupling_to_diameter_with_linear_extrapolation(
        target_mie_relation=relation_resolution.target_mie_relation,
        coupling_values=estimated_coupling,
    )

    _log_array_summary(
        name="apply_mie_equivalent_diameter_nm",
        values=mie_equivalent_diameter_nm,
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

    logger.debug(
        "apply_scattering_calibration_to_dataframe returning output_dataframe_shape=%r "
        "output_columns=%r warning_count=%r",
        getattr(output_dataframe, "shape", None),
        output_columns.as_list(),
        len(relation_resolution.warnings),
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
    logger.debug(
        "resolve_monotonic_target_mie_relation called with mie_model=%r relation_role=%r",
        getattr(target_mie_relation, "mie_model", None),
        getattr(target_mie_relation, "relation_role", None),
    )

    diameter_values_nm, theoretical_coupling_values = get_finite_positive_mie_relation_arrays(
        target_mie_relation=target_mie_relation,
    )

    if relation_is_strictly_monotonic(
        values=theoretical_coupling_values,
    ):
        logger.debug(
            "resolve_monotonic_target_mie_relation using full relation because it is strictly monotonic."
        )

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

    logger.debug(
        "resolve_monotonic_target_mie_relation found monotonic_interval_count=%r",
        len(monotonic_intervals),
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

    logger.debug(
        "resolve_monotonic_target_mie_relation selected_interval=%r",
        selected_interval,
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

    selected_interval = sorted(
        monotonic_intervals,
        key=lambda interval: (
            interval.diameter_width_nm,
            interval.point_count,
        ),
        reverse=True,
    )[0]

    logger.debug(
        "select_largest_monotonic_interval selected_interval=%r from interval_count=%r",
        selected_interval,
        len(monotonic_intervals),
    )

    return selected_interval


def build_monotonic_branch_mie_relation(
    *,
    target_mie_relation: MieRelation,
    selected_interval: MonotonicDiameterInterval,
) -> MieRelation:
    """
    Crop a Mie relation to one monotonic branch.
    """
    logger.debug(
        "build_monotonic_branch_mie_relation called with selected_interval=%r",
        selected_interval,
    )

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

    logger.debug(
        "coupling_to_diameter_with_linear_extrapolation called with "
        "coupling_array_shape=%r diameter_grid_size=%r coupling_grid_size=%r",
        coupling_array.shape,
        diameter_grid.size,
        coupling_grid.size,
    )

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

    _log_array_summary(
        name="coupling_to_diameter_interpolated_diameter",
        values=interpolated_diameter,
    )

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

    sorted_diameter_values_nm = diameter_values_nm[sorting_indices]
    sorted_theoretical_coupling_values = theoretical_coupling_values[sorting_indices]

    _log_array_summary(
        name="finite_positive_mie_relation_diameter_values_nm",
        values=sorted_diameter_values_nm,
    )

    _log_array_summary(
        name="finite_positive_mie_relation_theoretical_coupling_values",
        values=sorted_theoretical_coupling_values,
    )

    return (
        sorted_diameter_values_nm,
        sorted_theoretical_coupling_values,
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

    logger.debug(
        "find_strictly_monotonic_diameter_intervals returning interval_count=%r",
        len(intervals),
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

    interval = MonotonicDiameterInterval(
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

    logger.debug(
        "build_interval_if_valid accepted interval=%r",
        interval,
    )

    return [
        interval,
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

    For solid sphere targets, the relation diameter axis is particle diameter.

    For core shell targets, the relation diameter axis is core diameter. Shell
    thickness is kept constant and stored in the relation parameters.
    """
    logger.debug(
        "build_target_mie_relation called with target_model_parameters=%r",
        target_model_parameters,
    )

    calibration_standard_parameters = get_calibration_standard_parameters(
        calibration_payload,
    )

    logger.debug(
        "build_target_mie_relation calibration_standard_parameter_keys=%r",
        sorted(calibration_standard_parameters.keys()),
    )

    diameter_grid_nm = build_diameter_grid(
        diameter_min_nm=target_model_parameters.diameter_min_nm,
        diameter_max_nm=target_model_parameters.diameter_max_nm,
        diameter_count=target_model_parameters.diameter_count,
    )

    _log_array_summary(
        name="target_diameter_grid_nm",
        values=diameter_grid_nm,
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

    if target_model_parameters.mie_model == CORE_SHELL_SPHERE_MODEL_NAME:
        modeled_coupling_result = _build_core_shell_target_modeled_coupling(
            core_diameter_grid_nm=diameter_grid_nm,
            target_model_parameters=target_model_parameters,
            wavelength_nm=wavelength_nm,
            source_numerical_aperture=source_numerical_aperture,
            optical_power_watt=optical_power_watt,
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
            polarization_angle_degree=polarization_angle_degree,
            detector_sampling=detector_sampling,
        )

        relation_diameter_nm = np.asarray(
            diameter_grid_nm,
            dtype=float,
        ).reshape(-1)

    else:
        modeled_coupling_result = _build_solid_sphere_target_modeled_coupling(
            diameter_grid_nm=diameter_grid_nm,
            target_model_parameters=target_model_parameters,
            wavelength_nm=wavelength_nm,
            source_numerical_aperture=source_numerical_aperture,
            optical_power_watt=optical_power_watt,
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
            polarization_angle_degree=polarization_angle_degree,
            detector_sampling=detector_sampling,
        )

        relation_diameter_nm = np.asarray(
            modeled_coupling_result.particle_diameters_nm,
            dtype=float,
        ).reshape(-1)

    modeled_coupling_values = np.asarray(
        modeled_coupling_result.expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    _validate_same_size(
        first_values=relation_diameter_nm,
        second_values=modeled_coupling_values,
        first_name="relation_diameter_nm",
        second_name="modeled_coupling_values",
    )

    _log_array_summary(
        name="target_relation_diameter_nm",
        values=relation_diameter_nm,
    )

    _log_array_summary(
        name="target_modeled_coupling_values",
        values=modeled_coupling_values,
    )

    target_relation_parameters = build_mie_parameter_payload(
        mie_model=target_model_parameters.mie_model,
        medium_refractive_index=target_model_parameters.medium_refractive_index,
        particle_refractive_index=target_model_parameters.particle_refractive_index,
        core_refractive_index=target_model_parameters.core_refractive_index,
        shell_refractive_index=target_model_parameters.shell_refractive_index,
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

    if target_model_parameters.mie_model == CORE_SHELL_SPHERE_MODEL_NAME:
        if target_model_parameters.shell_thickness_nm is None:
            raise ValueError("target shell_thickness_nm is required for Core/Shell Sphere.")

        target_relation_parameters.update(
            {
                "diameter_axis": "core_diameter_nm",
                "shell_thickness_nm": float(
                    target_model_parameters.shell_thickness_nm,
                ),
                "core_diameter_min_nm": float(
                    target_model_parameters.diameter_min_nm,
                ),
                "core_diameter_max_nm": float(
                    target_model_parameters.diameter_max_nm,
                ),
                "outer_diameter_min_nm": float(
                    target_model_parameters.diameter_min_nm
                    + 2.0 * target_model_parameters.shell_thickness_nm
                ),
                "outer_diameter_max_nm": float(
                    target_model_parameters.diameter_max_nm
                    + 2.0 * target_model_parameters.shell_thickness_nm
                ),
            }
        )

    else:
        target_relation_parameters.update(
            {
                "diameter_axis": "particle_diameter_nm",
            }
        )

    logger.debug(
        "build_target_mie_relation calling build_mie_relation_from_arrays with "
        "diameter_axis=%r diameter_count=%r coupling_count=%r parameter_keys=%r",
        target_relation_parameters.get("diameter_axis"),
        relation_diameter_nm.size,
        modeled_coupling_values.size,
        sorted(target_relation_parameters.keys()),
    )

    return build_mie_relation_from_arrays(
        diameter_nm=relation_diameter_nm,
        theoretical_coupling=modeled_coupling_values,
        mie_model=target_model_parameters.mie_model,
        parameters=target_relation_parameters,
        relation_role="target_particle",
    )


def _build_solid_sphere_target_modeled_coupling(
    *,
    diameter_grid_nm: np.ndarray,
    target_model_parameters: ScatteringTargetModelParameters,
    wavelength_nm: float,
    source_numerical_aperture: float,
    optical_power_watt: float,
    detector_numerical_aperture: float,
    detector_cache_numerical_aperture: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    polarization_angle_degree: float,
    detector_sampling: int,
) -> Any:
    """
    Build modeled coupling for a solid sphere target relation.
    """
    if target_model_parameters.particle_refractive_index is None:
        raise ValueError("target_particle_refractive_index is required for Solid Sphere.")

    logger.debug(
        "_build_solid_sphere_target_modeled_coupling called with diameter_count=%r",
        np.asarray(diameter_grid_nm).size,
    )

    return BackEnd.compute_modeled_coupling_from_diameters(
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


def _build_core_shell_target_modeled_coupling(
    *,
    core_diameter_grid_nm: np.ndarray,
    target_model_parameters: ScatteringTargetModelParameters,
    wavelength_nm: float,
    source_numerical_aperture: float,
    optical_power_watt: float,
    detector_numerical_aperture: float,
    detector_cache_numerical_aperture: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    polarization_angle_degree: float,
    detector_sampling: int,
) -> Any:
    """
    Build modeled coupling for a core shell target relation.

    The diameter grid is interpreted as a core diameter grid. Shell thickness is
    constant and provided by the user.
    """
    if target_model_parameters.core_refractive_index is None:
        raise ValueError("target_core_refractive_index is required for Core/Shell Sphere.")

    if target_model_parameters.shell_refractive_index is None:
        raise ValueError("target_shell_refractive_index is required for Core/Shell Sphere.")

    if target_model_parameters.shell_thickness_nm is None:
        raise ValueError("target_shell_thickness_nm is required for Core/Shell Sphere.")

    core_diameters_nm = np.asarray(
        core_diameter_grid_nm,
        dtype=float,
    ).reshape(-1)

    shell_thickness_nm = float(
        target_model_parameters.shell_thickness_nm,
    )

    valid_mask = (
        np.isfinite(core_diameters_nm)
        & (core_diameters_nm > 0.0)
    )

    core_diameters_nm = core_diameters_nm[valid_mask]

    shell_thicknesses_nm = np.full(
        core_diameters_nm.size,
        shell_thickness_nm,
        dtype=float,
    )

    if core_diameters_nm.size < 2:
        raise ValueError(
            "Core shell target relation has fewer than two valid core diameter points."
        )

    outer_diameters_nm = core_diameters_nm + 2.0 * shell_thickness_nm

    logger.debug(
        "_build_core_shell_target_modeled_coupling using shell_thickness_nm=%r "
        "core_diameter_count=%r outer_diameter_min_nm=%r outer_diameter_max_nm=%r",
        shell_thickness_nm,
        core_diameters_nm.size,
        float(np.min(outer_diameters_nm)),
        float(np.max(outer_diameters_nm)),
    )

    _log_array_summary(
        name="target_core_shell_core_diameters_nm",
        values=core_diameters_nm,
    )

    _log_array_summary(
        name="target_core_shell_shell_thicknesses_nm",
        values=shell_thicknesses_nm,
    )

    _log_array_summary(
        name="target_core_shell_outer_diameters_nm",
        values=outer_diameters_nm,
    )

    return BackEnd.compute_modeled_coupling_from_core_shell_dimensions(
        core_diameters_nm=core_diameters_nm,
        shell_thicknesses_nm=shell_thicknesses_nm,
        wavelength_nm=wavelength_nm,
        source_numerical_aperture=source_numerical_aperture,
        optical_power_watt=optical_power_watt,
        detector_numerical_aperture=detector_numerical_aperture,
        medium_refractive_index=target_model_parameters.medium_refractive_index,
        core_refractive_index=target_model_parameters.core_refractive_index,
        shell_refractive_index=target_model_parameters.shell_refractive_index,
        detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        detector_phi_offset_degree=detector_phi_angle_degree,
        detector_gamma_offset_degree=detector_gamma_angle_degree,
        polarization_angle_degree=polarization_angle_degree,
        detector_sampling=detector_sampling,
    )


def get_calibration_standard_parameters(
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve optical geometry parameters stored in a scattering calibration.
    """
    logger.debug(
        "get_calibration_standard_parameters called with payload_keys=%r",
        sorted(calibration_payload.keys()) if isinstance(calibration_payload, dict) else None,
    )

    mie_relation_payload = calibration_payload.get(
        "calibration_standard_mie_relation",
    )

    if isinstance(mie_relation_payload, dict):
        relation_parameters = mie_relation_payload.get(
            "parameters",
        )

        if isinstance(relation_parameters, dict):
            logger.debug(
                "get_calibration_standard_parameters using calibration_standard_mie_relation parameters keys=%r",
                sorted(relation_parameters.keys()),
            )

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
            logger.debug(
                "get_calibration_standard_parameters using metadata calibration_standard_parameters keys=%r",
                sorted(calibration_standard_parameters.keys()),
            )

            return dict(
                calibration_standard_parameters,
            )

    raise ValueError(
        "Scattering calibration payload is missing calibration standard optical parameters."
    )


def resolve_target_mie_model(
    mie_model: Any,
) -> str:
    """
    Normalize target Mie model names.
    """
    mie_model_string = str(
        mie_model or SOLID_SPHERE_MODEL_NAME,
    ).strip()

    normalized_mie_model = mie_model_string.lower()

    if normalized_mie_model in {
        "core/shell sphere",
        "core shell sphere",
        "core-shell sphere",
        "coreshell sphere",
        "core_shell_sphere",
    }:
        return CORE_SHELL_SPHERE_MODEL_NAME

    return SOLID_SPHERE_MODEL_NAME


def _required_positive_float(
    *,
    value: Any,
    name: str,
) -> float:
    """
    Parse a strictly positive float.
    """
    try:
        parsed_value = float(
            value,
        )
    except Exception:
        logger.exception(
            "Failed to parse %s as float. value=%r",
            name,
            value,
        )
        raise

    if not np.isfinite(
        parsed_value,
    ):
        raise ValueError(f"{name} must be finite.")

    if parsed_value <= 0.0:
        raise ValueError(f"{name} must be positive.")

    return parsed_value


def _required_non_negative_float(
    *,
    value: Any,
    name: str,
) -> float:
    """
    Parse a non negative float.
    """
    try:
        parsed_value = float(
            value,
        )
    except Exception:
        logger.exception(
            "Failed to parse %s as float. value=%r",
            name,
            value,
        )
        raise

    if not np.isfinite(
        parsed_value,
    ):
        raise ValueError(f"{name} must be finite.")

    if parsed_value < 0.0:
        raise ValueError(f"{name} must be non negative.")

    return parsed_value


def _required_integer(
    *,
    value: Any,
    name: str,
) -> int:
    """
    Parse an integer.
    """
    try:
        parsed_value = int(
            value,
        )
    except Exception:
        logger.exception(
            "Failed to parse %s as int. value=%r",
            name,
            value,
        )
        raise

    return parsed_value


def _validate_same_size(
    *,
    first_values: np.ndarray,
    second_values: np.ndarray,
    first_name: str,
    second_name: str,
) -> None:
    """
    Validate that two arrays have the same flattened size.
    """
    first_values = np.asarray(
        first_values,
    ).reshape(-1)

    second_values = np.asarray(
        second_values,
    ).reshape(-1)

    if first_values.size == second_values.size:
        return

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
        "%s summary: size=%r finite_count=%r nan_count=%r inf_count=%r min=%r max=%r first_values=%r",
        name,
        array.size,
        finite_values.size,
        int(np.sum(np.isnan(array))),
        int(np.sum(np.isinf(array))),
        float(np.min(finite_values)),
        float(np.max(finite_values)),
        array[:10].tolist(),
    )