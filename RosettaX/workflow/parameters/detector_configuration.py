# -*- coding: utf-8 -*-

from typing import Any
import logging

import numpy as np

from . import loader
from .optical_preview import build_pymiesim_photodiode_mesh_coordinates


logger = logging.getLogger(__name__)


CUSTOM_DETECTOR_PRESET_NAME = "Generic detector"


def build_detector_preset_options() -> list[dict[str, str]]:
    """
    Build detector preset dropdown options from disk.

    JSON files are read every time this function is called, so preset edits are
    visible without restarting the app after clicking Reload detector presets.
    """
    return [
        {
            "label": CUSTOM_DETECTOR_PRESET_NAME,
            "value": CUSTOM_DETECTOR_PRESET_NAME,
        },
        *loader.load_detector_configuration_preset_options(),
    ]


def detector_preset_is_custom(preset_name: Any) -> bool:
    """
    Return True when the selected detector preset corresponds to editable custom values.
    """
    return preset_name == CUSTOM_DETECTOR_PRESET_NAME


def resolve_detector_configuration_visibility_style(
    *,
    preset_name: Any,
) -> dict[str, str]:
    """
    Resolve the visibility style for the manual detector configuration block.
    """
    if detector_preset_is_custom(preset_name):
        return {"display": "block"}

    return {"display": "none"}


def resolve_detector_configuration_values(
    *,
    preset_name: Any,
    current_detector_numerical_aperture: Any,
    current_detector_cache_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
    current_detector_sampling: Any,
    current_detector_phi_angle_degree: Any,
    current_detector_gamma_angle_degree: Any,
) -> tuple[Any, Any, Any, Any, Any, Any]:
    """
    Resolve detector values from either editable fields or a JSON backed preset.

    detector_cache_numerical_aperture and blocker_bar_numerical_aperture are
    separate physical/configuration parameters and must not be aliased.
    """
    current_values = (
        current_detector_numerical_aperture,
        current_detector_cache_numerical_aperture,
        current_blocker_bar_numerical_aperture,
        current_detector_sampling,
        current_detector_phi_angle_degree,
        current_detector_gamma_angle_degree,
    )

    if detector_preset_is_custom(preset_name):
        resolved_custom_values = (
            current_detector_numerical_aperture,
            0.0,
            current_blocker_bar_numerical_aperture,
            current_detector_sampling,
            current_detector_phi_angle_degree,
            current_detector_gamma_angle_degree,
        )

        logger.debug(
            "Resolved custom detector preset values for preset_name=%r values=%r",
            preset_name,
            resolved_custom_values,
        )

        return resolved_custom_values

    preset = loader.load_detector_configuration_preset(
        preset_name,
    )

    resolved_values = (
        _resolve_preset_value(
            preset=preset,
            key="detector_numerical_aperture",
            fallback=current_detector_numerical_aperture,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_cache_numerical_aperture",
            fallback=current_detector_cache_numerical_aperture,
        ),
        _resolve_preset_value(
            preset=preset,
            key="blocker_bar_numerical_aperture",
            fallback=current_blocker_bar_numerical_aperture,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_sampling",
            fallback=current_detector_sampling,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_phi_angle_degree",
            fallback=current_detector_phi_angle_degree,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_gamma_angle_degree",
            fallback=current_detector_gamma_angle_degree,
        ),
    )

    logger.debug(
        "Resolved detector preset values for preset_name=%r values=%r preset=%r",
        preset_name,
        resolved_values,
        preset,
    )

    return resolved_values


def resolve_detector_angular_weights(
    *,
    preset_name: Any,
    detector_sampling: Any,
) -> np.ndarray | None:
    """
    Resolve optional angular weights for a detector preset.

    Supported preset fields are:

    - ``detector_angular_weights``: explicit complex-valued vector
    - ``detector_angular_weight_profile``: named ad hoc generator
    """
    if detector_preset_is_custom(preset_name):
        return None

    preset = loader.load_detector_configuration_preset(
        preset_name,
    )

    if not preset:
        return None

    sampling_size = int(detector_sampling)

    explicit_weights = preset.get("detector_angular_weights")

    if explicit_weights is not None:
        angular_weights = np.asarray(
            explicit_weights,
            dtype=np.complex128,
        ).reshape(-1)

        if angular_weights.size != sampling_size:
            raise ValueError(
                "Preset detector_angular_weights length must match detector_sampling. "
                f"Got {angular_weights.size} weights for sampling={sampling_size}."
            )

        return angular_weights

    profile_name = preset.get("detector_angular_weight_profile")

    if profile_name in (None, ""):
        return None

    normalized_profile_name = str(profile_name).strip().lower()

    if normalized_profile_name == "first-half-zero":
        angular_weights = np.ones(
            sampling_size,
            dtype=np.complex128,
        )
        angular_weights[: sampling_size // 2] = 0.0
        return angular_weights

    if normalized_profile_name == "zero-x-positive":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )

        angular_weights = np.ones(
            sampling_size,
            dtype=np.complex128,
        )
        angular_weights[coordinate_array[:, 0] > 0.0] = 0.0
        return angular_weights

    if normalized_profile_name in {
        "local-split-positive-side",
        "local-split-negative-side",
    }:
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        split_metric = _build_local_split_metric(coordinate_array)

        angular_weights = np.ones(
            sampling_size,
            dtype=np.complex128,
        )

        if normalized_profile_name == "local-split-positive-side":
            angular_weights[split_metric <= 0.0] = 0.0
        else:
            angular_weights[split_metric >= 0.0] = 0.0

        return angular_weights

    if normalized_profile_name in {
        "split-side-half",
        "split-forward-half",
    }:
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        split_metric = coordinate_array[:, 0] - coordinate_array[:, 2]

        angular_weights = np.ones(
            sampling_size,
            dtype=np.complex128,
        )

        if normalized_profile_name == "split-side-half":
            angular_weights[split_metric <= 0.0] = 0.0
        else:
            angular_weights[split_metric >= 0.0] = 0.0

        return angular_weights

    raise ValueError(
        f"Unsupported detector_angular_weight_profile: {profile_name!r}"
    )


def _build_profile_coordinate_array(
    *,
    preset: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    detector_numerical_aperture = float(
        preset.get(
            "detector_numerical_aperture",
            0.4,
        )
    )
    detector_phi_angle_degree = float(
        preset.get(
            "detector_phi_angle_degree",
            0.0,
        )
    )
    detector_gamma_angle_degree = float(
        preset.get(
            "detector_gamma_angle_degree",
            0.0,
        )
    )
    medium_refractive_index = float(
        preset.get(
            "medium_refractive_index",
            1.333,
        )
    )

    coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
        detector_numerical_aperture=detector_numerical_aperture,
        medium_refractive_index=medium_refractive_index,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
        detector_sampling=sampling_size,
    )

    if coordinate_array.shape[0] != sampling_size:
        raise ValueError(
            "PyMieSim detector mesh size does not match detector_sampling for angular weight generation. "
            f"Got {coordinate_array.shape[0]} mesh points for sampling={sampling_size}."
        )

    return coordinate_array


def _build_local_split_metric(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    axis_vector = np.asarray(
        coordinate_array.mean(axis=0),
        dtype=float,
    )
    axis_norm = np.linalg.norm(axis_vector)

    if axis_norm == 0.0:
        raise ValueError("Cannot build a local detector split from a zero-length axis vector.")

    axis_vector = axis_vector / axis_norm

    reference_vector = np.array([0.0, 0.0, 1.0], dtype=float)

    if abs(float(np.dot(axis_vector, reference_vector))) > 0.99:
        reference_vector = np.array([1.0, 0.0, 0.0], dtype=float)

    split_normal = np.cross(reference_vector, axis_vector)
    split_normal_norm = np.linalg.norm(split_normal)

    if split_normal_norm == 0.0:
        raise ValueError("Cannot build a local detector split normal for this detector orientation.")

    split_normal = split_normal / split_normal_norm

    return coordinate_array @ split_normal


def _resolve_preset_value(
    *,
    preset: dict[str, Any],
    key: str,
    fallback: Any,
) -> Any:
    """
    Resolve one detector preset field.
    """
    if key not in preset:
        logger.debug(
            "Detector preset key %r is missing. Using fallback=%r",
            key,
            fallback,
        )
        return fallback

    return preset[key]