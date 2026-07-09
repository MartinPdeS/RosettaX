# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from RosettaX.workflow import scattering

from .models import (
    MonotonicDiameterInterval,
    MonotonicRelationResolution,
    ScatteringTargetModelParameters,
)


logger = logging.getLogger(__name__)


def resolve_monotonic_target_mie_relation(
    *,
    target_mie_relation: scattering.MieRelation,
    target_model_parameters: Optional[ScatteringTargetModelParameters] = None,
) -> MonotonicRelationResolution:
    """
    Resolve the monotonic target relation used for diameter inversion.

    If the full relation is strictly monotonic, it is used directly. If not, the
    widest strictly monotonic branch is selected automatically and expanded into
    a monotone approximation across the full diameter range.
    """
    logger.debug(
        "resolve_monotonic_target_mie_relation called with mie_model=%r relation_role=%r",
        getattr(target_mie_relation, "mie_model", None),
        getattr(target_mie_relation, "relation_role", None),
    )

    diameter_values_nm, theoretical_coupling_values = get_finite_positive_mie_relation_arrays(
        target_mie_relation=target_mie_relation,
    )

    if scattering.relation_is_strictly_monotonic(
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

    approximated_mie_relation = build_monotonic_approximation_mie_relation(
        target_mie_relation=target_mie_relation,
        selected_interval=selected_interval,
        target_model_parameters=target_model_parameters,
    )

    smoothing_is_enabled = bool(
        target_model_parameters is not None
        and target_model_parameters.advanced_monotonic_mode_enabled
        and target_model_parameters.use_monotonic_smoothing_kernel
    )

    warning = (
        "Target Mie relation was not strictly monotonic over the full selected "
        "diameter range. RosettaX automatically selected the left-most monotonic "
        f"branch: {selected_interval.to_message_fragment()}. A monotone "
        "approximation based on that branch is used across the selected "
        "diameter range."
    )

    if smoothing_is_enabled:
        warning = (
            f"{warning[:-1]} A Gaussian smoothing kernel "
            f"(sigma={target_model_parameters.monotonic_smoothing_sigma_points:.3g} points) "
            "was then applied to soften sharp transitions."
        )

    logger.debug(
        "resolve_monotonic_target_mie_relation selected_interval=%r",
        selected_interval,
    )

    return MonotonicRelationResolution(
        target_mie_relation=approximated_mie_relation,
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
    Select the left-most monotonic branch.

    If multiple intervals start at the same index, keep the widest one, then
    the one with more points.
    """
    if not monotonic_intervals:
        raise ValueError("No monotonic intervals were provided.")

    selected_interval = sorted(
        monotonic_intervals,
        key=lambda interval: (
            interval.start_index,
            -interval.diameter_width_nm,
            -interval.point_count,
        ),
    )[0]

    logger.debug(
        "select_largest_monotonic_interval selected left-most interval=%r from interval_count=%r",
        selected_interval,
        len(monotonic_intervals),
    )

    return selected_interval


def build_monotonic_branch_mie_relation(
    *,
    target_mie_relation: scattering.MieRelation,
    selected_interval: MonotonicDiameterInterval,
) -> scattering.MieRelation:
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

    if not scattering.relation_is_strictly_monotonic(
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

    return scattering.build_mie_relation_from_arrays(
        diameter_nm=branch_diameter_values_nm,
        theoretical_coupling=branch_coupling_values,
        mie_model=target_mie_relation.mie_model,
        parameters=parameters,
        relation_role=target_mie_relation.relation_role,
    )


def build_monotonic_approximation_mie_relation(
    *,
    target_mie_relation: scattering.MieRelation,
    selected_interval: MonotonicDiameterInterval,
    target_model_parameters: Optional[ScatteringTargetModelParameters] = None,
) -> scattering.MieRelation:
    """
    Build a monotone approximation of the full Mie relation.

    The selected strictly monotonic branch is preserved exactly. Outside that
    branch, the original curve is converted into a monotone envelope that keeps
    following the same overall Mie-curve shape without introducing straight-line
    segments across the whole rejected region.
    """
    diameter_values_nm, theoretical_coupling_values = get_finite_positive_mie_relation_arrays(
        target_mie_relation=target_mie_relation,
    )

    approximated_coupling_values = build_monotonic_coupling_approximation(
        theoretical_coupling_values=theoretical_coupling_values,
        selected_interval=selected_interval,
        target_model_parameters=target_model_parameters,
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
            "monotonic_approximation_enabled": True,
            "monotonic_approximation_strategy": "cumulative_envelope",
            "monotonic_smoothing_enabled": bool(
                target_model_parameters is not None
                and target_model_parameters.advanced_monotonic_mode_enabled
                and target_model_parameters.use_monotonic_smoothing_kernel
            ),
            "monotonic_smoothing_sigma_points": (
                float(target_model_parameters.monotonic_smoothing_sigma_points)
                if target_model_parameters is not None
                else 0.0
            ),
        }
    )

    return scattering.build_mie_relation_from_arrays(
        diameter_nm=diameter_values_nm,
        theoretical_coupling=approximated_coupling_values,
        mie_model=target_mie_relation.mie_model,
        parameters=parameters,
        relation_role=target_mie_relation.relation_role,
    )


def build_monotonic_coupling_approximation(
    *,
    theoretical_coupling_values: np.ndarray,
    selected_interval: MonotonicDiameterInterval,
    target_model_parameters: Optional[ScatteringTargetModelParameters] = None,
) -> np.ndarray:
    """
    Build a monotone coupling envelope anchored on the selected branch.
    """
    coupling_values = np.asarray(
        theoretical_coupling_values,
        dtype=float,
    ).reshape(-1)

    approximated_coupling_values = coupling_values.copy()

    branch_values = coupling_values[
        selected_interval.start_index : selected_interval.end_index + 1
    ]

    if branch_values.size < 2:
        raise ValueError("Selected monotonic branch has fewer than two points.")

    if selected_interval.trend == "increasing":
        left_values = coupling_values[: selected_interval.start_index]

        if left_values.size > 0:
            approximated_coupling_values[: selected_interval.start_index] = np.minimum(
                np.maximum.accumulate(left_values),
                branch_values[0],
            )

        right_values = coupling_values[selected_interval.end_index + 1 :]

        if right_values.size > 0:
            approximated_coupling_values[selected_interval.end_index + 1 :] = (
                np.maximum.accumulate(
                    np.concatenate(
                        (
                            np.asarray([branch_values[-1]], dtype=float),
                            right_values,
                        )
                    )
                )[1:]
            )

    else:
        left_values = coupling_values[: selected_interval.start_index]

        if left_values.size > 0:
            approximated_coupling_values[: selected_interval.start_index] = np.maximum(
                np.minimum.accumulate(left_values),
                branch_values[0],
            )

        right_values = coupling_values[selected_interval.end_index + 1 :]

        if right_values.size > 0:
            approximated_coupling_values[selected_interval.end_index + 1 :] = (
                np.minimum.accumulate(
                    np.concatenate(
                        (
                            np.asarray([branch_values[-1]], dtype=float),
                            right_values,
                        )
                    )
                )[1:]
            )

    if (
        target_model_parameters is not None
        and target_model_parameters.advanced_monotonic_mode_enabled
        and target_model_parameters.use_monotonic_smoothing_kernel
    ):
        flattened_mask = np.ones(
            approximated_coupling_values.shape,
            dtype=bool,
        )
        flattened_mask[
            selected_interval.start_index : selected_interval.end_index + 1
        ] = False

        approximated_coupling_values = smooth_monotonic_coupling_approximation(
            approximated_coupling_values=approximated_coupling_values,
            selected_interval=selected_interval,
            sigma_points=target_model_parameters.monotonic_smoothing_sigma_points,
            smoothing_mask=flattened_mask,
        )

    return approximated_coupling_values


def smooth_monotonic_coupling_approximation(
    *,
    approximated_coupling_values: np.ndarray,
    selected_interval: MonotonicDiameterInterval,
    sigma_points: float,
    smoothing_mask: np.ndarray,
) -> np.ndarray:
    """
    Smooth a monotone approximation and project it back onto a monotone curve.
    """
    coupling_values = np.asarray(
        approximated_coupling_values,
        dtype=float,
    ).reshape(-1)
    mask_values = np.asarray(
        smoothing_mask,
        dtype=bool,
    ).reshape(-1)

    if coupling_values.size < 3:
        return coupling_values

    if coupling_values.size != mask_values.size or not np.any(mask_values):
        return coupling_values

    gaussian_kernel = build_gaussian_kernel_1d(
        sigma_points=sigma_points,
    )

    padding_radius = gaussian_kernel.size // 2

    padded_values = np.pad(
        coupling_values,
        pad_width=padding_radius,
        mode="edge",
    )

    smoothed_values = np.convolve(
        padded_values,
        gaussian_kernel,
        mode="valid",
    )

    blended_values = coupling_values.copy()
    blended_values[mask_values] = smoothed_values[mask_values]

    start_index = selected_interval.start_index
    end_index = selected_interval.end_index
    branch_values = coupling_values[start_index : end_index + 1]
    blended_values[start_index : end_index + 1] = branch_values

    transition_point_count = max(
        8,
        int(np.ceil(float(sigma_points))),
    )

    if selected_interval.trend == "increasing":
        blended_values = blend_transition_window(
            blended_values=blended_values,
            start_index=start_index,
            end_index=end_index,
            boundary_value=branch_values[0],
            transition_point_count=transition_point_count,
            trend="increasing",
            side="left",
        )
        blended_values = blend_transition_window(
            blended_values=blended_values,
            start_index=start_index,
            end_index=end_index,
            boundary_value=branch_values[-1],
            transition_point_count=transition_point_count,
            trend="increasing",
            side="right",
        )

    else:
        blended_values = blend_transition_window(
            blended_values=blended_values,
            start_index=start_index,
            end_index=end_index,
            boundary_value=branch_values[0],
            transition_point_count=transition_point_count,
            trend="decreasing",
            side="left",
        )
        blended_values = blend_transition_window(
            blended_values=blended_values,
            start_index=start_index,
            end_index=end_index,
            boundary_value=branch_values[-1],
            transition_point_count=transition_point_count,
            trend="decreasing",
            side="right",
        )

    if selected_interval.trend == "increasing":
        if start_index > 0:
            left_values = np.maximum.accumulate(
                blended_values[:start_index],
            )
            left_values = np.minimum(
                left_values,
                branch_values[0],
            )
            blended_values[:start_index] = left_values

        if end_index + 1 < blended_values.size:
            right_values = np.maximum.accumulate(
                np.concatenate(
                    (
                        np.asarray([branch_values[-1]], dtype=float),
                        blended_values[end_index + 1 :],
                    )
                )
            )[1:]
            blended_values[end_index + 1 :] = right_values

    else:
        if start_index > 0:
            left_values = np.minimum.accumulate(
                blended_values[:start_index],
            )
            left_values = np.maximum(
                left_values,
                branch_values[0],
            )
            blended_values[:start_index] = left_values

        if end_index + 1 < blended_values.size:
            right_values = np.minimum.accumulate(
                np.concatenate(
                    (
                        np.asarray([branch_values[-1]], dtype=float),
                        blended_values[end_index + 1 :],
                    )
                )
            )[1:]
            blended_values[end_index + 1 :] = right_values

    return blended_values


def blend_transition_window(
    *,
    blended_values: np.ndarray,
    start_index: int,
    end_index: int,
    boundary_value: float,
    transition_point_count: int,
    trend: str,
    side: str,
) -> np.ndarray:
    """
    Blend a short transition window around the monotonic branch boundary.

    The exact branch values stay unchanged; only the points immediately outside
    the branch are eased toward the boundary value to reduce visible kinks.
    """
    values = np.asarray(
        blended_values,
        dtype=float,
    ).copy()

    if transition_point_count < 1:
        return values

    if side == "left":
        window_start = max(
            0,
            start_index - transition_point_count,
        )
        window_end = start_index
        if window_end <= window_start:
            return values

        window_values = values[window_start:window_end]
        if window_values.size == 0:
            return values

        if trend == "increasing":
            values[window_start:window_end] = np.minimum(
                window_values + _smoothstep_weights(window_values.size) * (
                    boundary_value - window_values
                ),
                boundary_value,
            )
        else:
            values[window_start:window_end] = np.maximum(
                window_values + _smoothstep_weights(window_values.size) * (
                    boundary_value - window_values
                ),
                boundary_value,
            )

    elif side == "right":
        window_start = end_index + 1
        window_end = min(
            values.size,
            end_index + 1 + transition_point_count,
        )
        if window_end <= window_start:
            return values

        window_values = values[window_start:window_end]
        if window_values.size == 0:
            return values

        if trend == "increasing":
            values[window_start:window_end] = np.minimum(
                boundary_value + _smoothstep_weights(window_values.size) * (
                    window_values - boundary_value
                ),
                window_values,
            )
        else:
            values[window_start:window_end] = np.maximum(
                boundary_value + _smoothstep_weights(window_values.size) * (
                    window_values - boundary_value
                ),
                window_values,
            )

    return values


def _smoothstep_weights(count: int) -> np.ndarray:
    """
    Build a smoothstep ramp from 0 to 1 over the requested count.
    """
    if count <= 1:
        return np.ones((count,), dtype=float)

    t_values = np.linspace(
        0.0,
        1.0,
        count,
        dtype=float,
    )

    return t_values * t_values * (3.0 - 2.0 * t_values)


def build_gaussian_kernel_1d(
    *,
    sigma_points: float,
) -> np.ndarray:
    """
    Build a normalized 1-D Gaussian kernel in index space.
    """
    resolved_sigma_points = max(
        float(sigma_points),
        1e-6,
    )

    kernel_radius = max(
        1,
        int(np.ceil(3.0 * resolved_sigma_points)),
    )

    offsets = np.arange(
        -kernel_radius,
        kernel_radius + 1,
        dtype=float,
    )

    kernel = np.exp(
        -0.5 * np.square(offsets / resolved_sigma_points),
    )

    kernel_sum = float(
        np.sum(kernel),
    )

    if kernel_sum <= 0.0 or not np.isfinite(kernel_sum):
        return np.asarray(
            [1.0],
            dtype=float,
        )

    return kernel / kernel_sum


def coupling_to_diameter_with_linear_extrapolation(
    *,
    target_mie_relation: scattering.MieRelation,
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
        logger.debug(
            "coupling_to_diameter_with_linear_extrapolation returning nan array because filtered grid has fewer than 2 points."
        )

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
        logger.debug(
            "coupling_to_diameter_with_linear_extrapolation returning nan array because unique coupling grid has fewer than 2 points."
        )

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
    target_mie_relation: scattering.MieRelation,
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

    if scattering.relation_is_strictly_monotonic(
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
    target_mie_relation: scattering.MieRelation,
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

    if not scattering.relation_is_strictly_monotonic(
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
