# -*- coding: utf-8 -*-

from typing import Any
import logging

from . import loader

logger = logging.getLogger(__name__)


CUSTOM_DETECTOR_PRESET_NAME = "Custom detector"

DETECTOR_PRESET_STYLE_VISIBLE = {"display": "block"}
DETECTOR_PRESET_STYLE_HIDDEN = {"display": "none"}


def build_detector_preset_options() -> list[dict[str, str]]:
    """
    Build detector preset dropdown options.

    JSON backed detector presets are loaded from disk every time this function
    is called. This makes JSON edits visible while the Dash server is running.
    """
    logger.debug("Building detector preset options from disk.")

    json_preset_options = loader.load_detector_configuration_preset_options()

    options = [
        {
            "label": CUSTOM_DETECTOR_PRESET_NAME,
            "value": CUSTOM_DETECTOR_PRESET_NAME,
        },
        *json_preset_options,
    ]

    logger.debug(
        "Built detector preset options with option_count=%d options=%r",
        len(options),
        options,
    )

    return options


def detector_preset_is_custom(
    preset_name: Any,
) -> bool:
    """
    Return True when the selected detector preset corresponds to editable custom values.
    """
    resolved_preset_name = normalize_detector_preset_name(preset_name)
    return resolved_preset_name == CUSTOM_DETECTOR_PRESET_NAME


def normalize_detector_preset_name(
    preset_name: Any,
) -> str:
    """
    Convert a detector preset name to a normalized string.
    """
    if preset_name is None:
        return ""

    return str(preset_name).strip()


def resolve_detector_configuration_visibility_style(
    *,
    preset_name: Any,
) -> dict[str, str]:
    """
    Resolve the visibility style for the manual detector configuration block.

    Manual detector inputs are visible only for Custom detector mode.
    """
    if detector_preset_is_custom(preset_name):
        logger.debug(
            "Detector preset %r is custom. Showing detector configuration fields.",
            preset_name,
        )
        return dict(DETECTOR_PRESET_STYLE_VISIBLE)

    logger.debug(
        "Detector preset %r is JSON backed. Hiding detector configuration fields.",
        preset_name,
    )
    return dict(DETECTOR_PRESET_STYLE_HIDDEN)


def resolve_detector_configuration_values(
    *,
    preset_name: Any,
    current_detector_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
    current_detector_sampling: Any,
    current_detector_phi_angle_degree: Any,
    current_detector_gamma_angle_degree: Any,
) -> tuple[Any, Any, Any, Any, Any]:
    """
    Resolve detector values from either editable fields or a JSON backed preset.

    JSON backed presets are loaded from disk each time, so changes to the JSON
    file are applied without restarting the Dash server.

    Returns
    -------
    tuple
        Values ordered as:
        - detector_numerical_aperture
        - blocker_bar_numerical_aperture
        - detector_sampling
        - detector_phi_angle_degree
        - detector_gamma_angle_degree
    """
    current_values = build_current_detector_configuration_values(
        current_detector_numerical_aperture=current_detector_numerical_aperture,
        current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
        current_detector_sampling=current_detector_sampling,
        current_detector_phi_angle_degree=current_detector_phi_angle_degree,
        current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
    )

    if detector_preset_is_custom(preset_name):
        logger.debug(
            "Selected detector preset is custom. Preserving current detector values=%r",
            current_values,
        )
        return current_values

    resolved_preset_name = normalize_detector_preset_name(preset_name)

    logger.debug(
        "Loading detector preset values from disk for preset_name=%r",
        resolved_preset_name,
    )

    preset = loader.load_detector_configuration_preset(
        resolved_preset_name,
    )

    if not preset:
        logger.warning(
            "Detector preset %r could not be loaded. Preserving current detector values=%r",
            resolved_preset_name,
            current_values,
        )
        return current_values

    resolved_values = (
        get_detector_preset_value(
            preset=preset,
            key="detector_numerical_aperture",
            fallback=current_detector_numerical_aperture,
        ),
        get_detector_preset_value(
            preset=preset,
            key="blocker_bar_numerical_aperture",
            fallback=get_detector_preset_value(
                preset=preset,
                key="detector_cache_numerical_aperture",
                fallback=current_blocker_bar_numerical_aperture,
            ),
        ),
        get_detector_preset_value(
            preset=preset,
            key="detector_sampling",
            fallback=current_detector_sampling,
        ),
        get_detector_preset_value(
            preset=preset,
            key="detector_phi_angle_degree",
            fallback=current_detector_phi_angle_degree,
        ),
        get_detector_preset_value(
            preset=preset,
            key="detector_gamma_angle_degree",
            fallback=current_detector_gamma_angle_degree,
        ),
    )

    logger.debug(
        "Resolved detector preset values for preset_name=%r values=%r preset=%r",
        resolved_preset_name,
        resolved_values,
        preset,
    )

    return resolved_values


def build_current_detector_configuration_values(
    *,
    current_detector_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
    current_detector_sampling: Any,
    current_detector_phi_angle_degree: Any,
    current_detector_gamma_angle_degree: Any,
) -> tuple[Any, Any, Any, Any, Any]:
    """
    Build the detector value tuple from current UI values.
    """
    return (
        current_detector_numerical_aperture,
        current_blocker_bar_numerical_aperture,
        current_detector_sampling,
        current_detector_phi_angle_degree,
        current_detector_gamma_angle_degree,
    )


def get_detector_preset_value(
    *,
    preset: dict[str, Any],
    key: str,
    fallback: Any,
) -> Any:
    """
    Return a detector preset value, preserving the fallback when the key is absent
    or the JSON value is None.
    """
    if key not in preset:
        logger.debug(
            "Detector preset key %r is missing. Using fallback=%r",
            key,
            fallback,
        )
        return fallback

    value = preset.get(key)

    if value is None:
        logger.debug(
            "Detector preset key %r is None. Using fallback=%r",
            key,
            fallback,
        )
        return fallback

    return value