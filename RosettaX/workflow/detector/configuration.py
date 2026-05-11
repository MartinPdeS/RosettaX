# -*- coding: utf-8 -*-

from typing import Any
import logging

import numpy as np

from .loader import get_default_detector_preset_loader
from ...pages.p03_scattering.sections.s03_model.optical_preview import build_pymiesim_photodiode_mesh_coordinates


logger = logging.getLogger(__name__)
_DETECTOR_PRESET_LOADER = get_default_detector_preset_loader()


CUSTOM_DETECTOR_PRESET_NAME = "Generic detector"


def build_detector_preset_options() -> list[dict[str, str]]:
    """
    Build detector preset dropdown options from disk.

    JSON files are read every time this function is called, so preset edits are
    visible without restarting the app after clicking Reload detector presets.
    """
    preset_options = [
        option
        for option in _DETECTOR_PRESET_LOADER.load_preset_options()
        if option["value"] != CUSTOM_DETECTOR_PRESET_NAME
    ]

    return [
        {
            "label": CUSTOM_DETECTOR_PRESET_NAME,
            "value": CUSTOM_DETECTOR_PRESET_NAME,
        },
        *preset_options,
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

    preset = _DETECTOR_PRESET_LOADER.load_preset(
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


def resolve_detector_modeling_geometry_values(
    *,
    preset_name: Any,
    current_detector_cache_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
) -> tuple[Any, Any]:
    """
    Resolve the geometry values that should be passed into modeling calls.

    Preset-driven detector weights can encode detector cache and blocker-bar
    geometry directly. When that happens, the scalar geometry values passed to
    PyMieSim and the preview are neutralized to avoid double-applying the mask.
    """
    if detector_preset_is_custom(preset_name):
        if (
            float(current_detector_cache_numerical_aperture) > 0.0
            or float(current_blocker_bar_numerical_aperture) > 0.0
        ):
            return 0.0, 0.0

        return (
            current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture,
        )

    preset = _DETECTOR_PRESET_LOADER.load_preset(
        preset_name,
    )

    if not preset or not _preset_uses_weighted_detector_geometry(preset):
        return (
            current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture,
        )

    return 0.0, 0.0


def resolve_detector_angular_weights(
    *,
    preset_name: Any,
    detector_sampling: Any,
    current_detector_numerical_aperture: Any = None,
    current_detector_cache_numerical_aperture: Any = None,
    current_blocker_bar_numerical_aperture: Any = None,
    current_detector_phi_angle_degree: Any = None,
    current_detector_gamma_angle_degree: Any = None,
    current_medium_refractive_index: Any = None,
) -> np.ndarray | None:
    """
    Resolve optional angular weights for a detector preset.

        Supported preset fields are:

        - ``detector_angular_weights``: explicit complex-valued vector
        - ``detector_cache_numerical_aperture`` and
            ``blocker_bar_numerical_aperture``: radial geometry masks
        - ``detector_angular_weight_profile``: named ad hoc generator
    """
    if detector_preset_is_custom(preset_name):
        custom_geometry_preset = _build_custom_geometry_preset(
            current_detector_numerical_aperture=current_detector_numerical_aperture,
            current_detector_cache_numerical_aperture=current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
            current_detector_phi_angle_degree=current_detector_phi_angle_degree,
            current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
            current_medium_refractive_index=current_medium_refractive_index,
        )

        if custom_geometry_preset is None:
            return None

        return _build_geometry_angular_weights(
            preset=custom_geometry_preset,
            sampling_size=int(detector_sampling),
        )

    preset = _DETECTOR_PRESET_LOADER.load_preset(
        preset_name,
    )

    if not preset:
        return None

    sampling_size = int(detector_sampling)

    geometry_angular_weights = _build_geometry_angular_weights(
        preset=preset,
        sampling_size=sampling_size,
    )
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

        return _combine_detector_angular_weights(
            geometry_angular_weights,
            angular_weights,
        )

    angular_weighting = preset.get("detector_angular_weighting")

    if isinstance(angular_weighting, dict):
        return _combine_detector_angular_weights(
            geometry_angular_weights,
            _resolve_detector_angular_weighting(
                preset=preset,
                angular_weighting=angular_weighting,
                sampling_size=sampling_size,
            ),
        )

    profile_name = preset.get("detector_angular_weight_profile")

    if profile_name in (None, ""):
        return geometry_angular_weights

    raise ValueError(
        f"Unsupported detector_angular_weight_profile: {profile_name!r}"
    )


def _combine_detector_angular_weights(
    geometry_angular_weights: np.ndarray | None,
    configured_angular_weights: np.ndarray | None,
) -> np.ndarray | None:
    if geometry_angular_weights is None:
        return configured_angular_weights

    if configured_angular_weights is None:
        return geometry_angular_weights

    return np.asarray(
        geometry_angular_weights,
        dtype=np.complex128,
    ) * np.asarray(
        configured_angular_weights,
        dtype=np.complex128,
    )


def _build_custom_geometry_preset(
    *,
    current_detector_numerical_aperture: Any,
    current_detector_cache_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
    current_detector_phi_angle_degree: Any,
    current_detector_gamma_angle_degree: Any,
    current_medium_refractive_index: Any,
) -> dict[str, Any] | None:
    detector_cache_numerical_aperture = float(
        current_detector_cache_numerical_aperture or 0.0,
    )
    blocker_bar_numerical_aperture = float(
        current_blocker_bar_numerical_aperture or 0.0,
    )

    if detector_cache_numerical_aperture <= 0.0 and blocker_bar_numerical_aperture <= 0.0:
        return None

    return {
        "name": CUSTOM_DETECTOR_PRESET_NAME,
        "detector_numerical_aperture": float(
            current_detector_numerical_aperture or 0.0,
        ),
        "detector_cache_numerical_aperture": detector_cache_numerical_aperture,
        "blocker_bar_numerical_aperture": blocker_bar_numerical_aperture,
        "detector_phi_angle_degree": float(
            current_detector_phi_angle_degree or 0.0,
        ),
        "detector_gamma_angle_degree": float(
            current_detector_gamma_angle_degree or 0.0,
        ),
        "medium_refractive_index": float(
            current_medium_refractive_index or 1.333,
        ),
    }


def _build_geometry_angular_weights(
    *,
    preset: dict[str, Any],
    sampling_size: int,
) -> np.ndarray | None:
    detector_cache_numerical_aperture = float(
        preset.get(
            "detector_cache_numerical_aperture",
            0.0,
        )
    )
    blocker_bar_numerical_aperture = float(
        preset.get(
            "blocker_bar_numerical_aperture",
            0.0,
        )
    )

    if detector_cache_numerical_aperture <= 0.0 and blocker_bar_numerical_aperture <= 0.0:
        return None

    coordinate_array = _build_profile_coordinate_array(
        preset=preset,
        sampling_size=sampling_size,
    )
    local_numerical_aperture = _build_local_numerical_aperture(
        preset=preset,
        coordinate_array=coordinate_array,
    )
    visible_mask = np.ones(
        sampling_size,
        dtype=bool,
    )

    if detector_cache_numerical_aperture > 0.0:
        visible_mask &= (
            _build_detector_cache_numerical_aperture(
                preset=preset,
                coordinate_array=coordinate_array,
            ) >= detector_cache_numerical_aperture
        )

    if blocker_bar_numerical_aperture > 0.0:
        visible_mask &= (
            _build_blocker_bar_numerical_aperture(
                preset=preset,
                coordinate_array=coordinate_array,
            ) >= blocker_bar_numerical_aperture
        )

    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )
    angular_weights[visible_mask] = 1.0
    return angular_weights


def _build_local_numerical_aperture(
    *,
    preset: dict[str, Any],
    coordinate_array: np.ndarray,
) -> np.ndarray:
    return _build_detector_cache_numerical_aperture(
        preset=preset,
        coordinate_array=coordinate_array,
    )


def _build_detector_cache_numerical_aperture(
    *,
    preset: dict[str, Any],
    coordinate_array: np.ndarray,
) -> np.ndarray:
    medium_refractive_index = float(
        preset.get(
            "medium_refractive_index",
            1.333,
        )
    )
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, first_transverse_projection, second_transverse_projection = _project_coordinates_to_local_detector_frame(
        normalized_coordinate_array,
    )
    radial_coordinate = np.sqrt(
        first_transverse_projection ** 2
        + second_transverse_projection ** 2
    )
    return medium_refractive_index * radial_coordinate


def _build_blocker_bar_numerical_aperture(
    *,
    preset: dict[str, Any],
    coordinate_array: np.ndarray,
) -> np.ndarray:
    medium_refractive_index = float(
        preset.get(
            "medium_refractive_index",
            1.333,
        )
    )
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, blocker_axis_projection, _ = _project_coordinates_to_local_detector_frame(
        normalized_coordinate_array,
    )
    return medium_refractive_index * np.abs(blocker_axis_projection)


def _project_coordinates_to_local_detector_frame(
    normalized_coordinate_array: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    detector_axis_vector, first_transverse_axis, second_transverse_axis = _build_local_detector_basis(
        normalized_coordinate_array,
    )

    return (
        normalized_coordinate_array @ detector_axis_vector,
        normalized_coordinate_array @ first_transverse_axis,
        normalized_coordinate_array @ second_transverse_axis,
    )


def _build_local_detector_basis(
    normalized_coordinate_array: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    detector_axis_vector = np.asarray(
        normalized_coordinate_array.mean(axis=0),
        dtype=float,
    )
    detector_axis_norm = np.linalg.norm(detector_axis_vector)

    if detector_axis_norm == 0.0:
        raise ValueError("Cannot build a detector-local basis from a zero-length axis vector.")

    detector_axis_vector = detector_axis_vector / detector_axis_norm

    reference_vector = np.array([0.0, 0.0, 1.0], dtype=float)

    if abs(float(np.dot(detector_axis_vector, reference_vector))) > 0.99:
        reference_vector = np.array([1.0, 0.0, 0.0], dtype=float)

    first_transverse_axis = np.cross(reference_vector, detector_axis_vector)
    first_transverse_axis_norm = np.linalg.norm(first_transverse_axis)

    if first_transverse_axis_norm == 0.0:
        raise ValueError("Cannot build the first detector transverse axis for this detector orientation.")

    first_transverse_axis = first_transverse_axis / first_transverse_axis_norm
    second_transverse_axis = np.cross(detector_axis_vector, first_transverse_axis)
    second_transverse_axis_norm = np.linalg.norm(second_transverse_axis)

    if second_transverse_axis_norm == 0.0:
        raise ValueError("Cannot build the second detector transverse axis for this detector orientation.")

    second_transverse_axis = second_transverse_axis / second_transverse_axis_norm

    return detector_axis_vector, first_transverse_axis, second_transverse_axis


def _normalize_coordinate_array(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    coordinate_array = np.asarray(
        coordinate_array,
        dtype=float,
    )
    coordinate_norms = np.linalg.norm(
        coordinate_array,
        axis=1,
    )

    if np.any(coordinate_norms <= 0.0):
        raise ValueError("Detector mesh coordinates contain a zero-length vector.")

    return coordinate_array / coordinate_norms[:, None]


def _preset_uses_weighted_detector_geometry(
    preset: dict[str, Any],
) -> bool:
    if float(preset.get("detector_cache_numerical_aperture", 0.0)) > 0.0:
        return True

    if float(preset.get("blocker_bar_numerical_aperture", 0.0)) > 0.0:
        return True

    if preset.get("detector_angular_weights") is not None:
        return True

    if isinstance(preset.get("detector_angular_weighting"), dict):
        return True

    return preset.get("detector_angular_weight_profile") not in (None, "")


def _resolve_detector_angular_weighting(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray | None:
    weighting_mode = str(angular_weighting.get("mode", "")).strip().lower()

    if not weighting_mode:
        return None

    if weighting_mode == "split":
        return _resolve_split_angular_weighting(
            preset=preset,
            angular_weighting=angular_weighting,
            sampling_size=sampling_size,
        )

    if weighting_mode == "index-split":
        return _resolve_index_split_angular_weighting(
            angular_weighting=angular_weighting,
            sampling_size=sampling_size,
        )

    if weighting_mode == "explicit":
        explicit_weights = angular_weighting.get("weights")
        angular_weights = np.asarray(
            explicit_weights,
            dtype=np.complex128,
        ).reshape(-1)

        if angular_weights.size != sampling_size:
            raise ValueError(
                "detector_angular_weighting weights length must match detector_sampling. "
                f"Got {angular_weights.size} weights for sampling={sampling_size}."
            )

        return angular_weights

    raise ValueError(
        f"Unsupported detector_angular_weighting mode: {angular_weighting.get('mode')!r}"
    )


def _resolve_split_angular_weighting(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    split_metric = _build_split_metric(
        preset=preset,
        angular_weighting=angular_weighting,
        sampling_size=sampling_size,
    )
    keep_side = str(angular_weighting.get("keep", "positive")).strip().lower()
    keep_mask_builders = {
        "positive": split_metric > 0.0,
        "negative": split_metric < 0.0,
        "nonpositive": split_metric <= 0.0,
        "nonnegative": split_metric >= 0.0,
    }

    if keep_side not in keep_mask_builders:
        raise ValueError(
            f"Unsupported detector split keep side: {angular_weighting.get('keep')!r}"
        )

    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )
    angular_weights[keep_mask_builders[keep_side]] = 1.0
    return angular_weights


def _resolve_index_split_angular_weighting(
    *,
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    keep_side = str(angular_weighting.get("keep", "second-half")).strip().lower()
    split_index = int(angular_weighting.get("split_index", sampling_size // 2))

    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )

    if keep_side == "second-half":
        angular_weights[split_index:] = 1.0
        return angular_weights

    if keep_side == "first-half":
        angular_weights[:split_index] = 1.0
        return angular_weights

    raise ValueError(
        f"Unsupported detector index split keep side: {angular_weighting.get('keep')!r}"
    )


def _build_split_metric(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    metric_name = str(angular_weighting.get("metric", "")).strip().lower()

    if metric_name == "mesh-x":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return coordinate_array[:, 0]

    if metric_name == "x-minus-z":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return coordinate_array[:, 0] - coordinate_array[:, 2]

    if metric_name == "local-plane":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return _build_local_split_metric(coordinate_array)

    raise ValueError(
        f"Unsupported detector split metric: {angular_weighting.get('metric')!r}"
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
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, split_normal, _ = _build_local_detector_basis(
        normalized_coordinate_array,
    )
    return normalized_coordinate_array @ split_normal


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
