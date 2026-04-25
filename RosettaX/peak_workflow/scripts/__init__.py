# -*- coding: utf-8 -*-

from typing import Any

from .registry import DEFAULT_PROCESS_NAME
from .registry import build_peak_process_options
from .registry import build_script_map
from .registry import clean_optional_string
from .registry import find_script_class_in_module
from .registry import get_default_script_name
from .registry import get_peak_process_instances
from .registry import get_process_instance
from .registry import load_peak_scripts
from .registry import resolve_process_name


def resolve_detector_channel_state(
    *,
    detector_dropdown_ids: list[dict[str, Any]] | None = None,
    detector_dropdown_values: list[Any] | None = None,
    process_name: Any = None,
    detector_options: Any = None,
    current_detector_value: Any = None,
    default_detector_value: Any = None,
    fallback_detector_value: Any = None,
    available_detector_options: Any = None,
    current_value: Any = None,
    default_value: Any = None,
    fallback_value: Any = None,
) -> dict[str, Any] | Any:
    """
    Resolve detector channel state for shared peak scripts.

    This function supports two call styles.

    Pattern matched dropdown style
    ------------------------------
    Used by scattering and fluorescence peak services:

    resolve_detector_channel_state(
        detector_dropdown_ids=[...],
        detector_dropdown_values=[...],
        process_name=...,
    )

    Returns a mapping such as:

    {
        "primary": "FSC-A",
        "x": "FSC-A",
        "y": "SSC-A",
    }

    Single dropdown style
    ---------------------
    Used by older code:

    resolve_detector_channel_state(
        detector_options=[...],
        current_detector_value=...,
        default_detector_value=...,
        fallback_detector_value=...,
    )

    Returns one resolved detector value.
    """
    if detector_dropdown_ids is not None or detector_dropdown_values is not None:
        return resolve_pattern_detector_channel_state(
            detector_dropdown_ids=detector_dropdown_ids or [],
            detector_dropdown_values=detector_dropdown_values or [],
            process_name=process_name,
        )

    return resolve_single_detector_channel_value(
        detector_options=detector_options,
        current_detector_value=current_detector_value,
        default_detector_value=default_detector_value,
        fallback_detector_value=fallback_detector_value,
        available_detector_options=available_detector_options,
        current_value=current_value,
        default_value=default_value,
        fallback_value=fallback_value,
    )


def resolve_pattern_detector_channel_state(
    *,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_name: Any,
) -> dict[str, Any]:
    """
    Resolve pattern matched detector dropdown values for one peak process.

    The first pass tries to match the selected process exactly. If this returns
    no channels, the second pass falls back to collecting all available detector
    channel values. This makes the function robust to small differences between
    process option values and process names stored in pattern matched ids.
    """
    resolved_process_name = resolve_process_name(
        process_name,
    )

    exact_channel_state = collect_detector_channel_state(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
        require_process_match=True,
    )

    if exact_channel_state:
        return exact_channel_state

    fallback_channel_state = collect_detector_channel_state(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
        require_process_match=False,
    )

    return fallback_channel_state


def collect_detector_channel_state(
    *,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_name: Any,
    require_process_match: bool,
) -> dict[str, Any]:
    """
    Collect detector channel values from pattern matched ids.

    Parameters
    ----------
    detector_dropdown_ids:
        Pattern matched detector dropdown ids.

    detector_dropdown_values:
        Pattern matched detector dropdown values.

    process_name:
        Selected process name.

    require_process_match:
        If True, only detector ids matching the selected process are accepted.
        If False, all detector ids with channel names are accepted.

    Returns
    -------
    dict[str, Any]
        Mapping from channel name to selected detector value.
    """
    resolved_process_name = "" if process_name is None else str(process_name)

    channel_state: dict[str, Any] = {}

    for detector_dropdown_id, detector_dropdown_value in zip(
        detector_dropdown_ids or [],
        detector_dropdown_values or [],
        strict=False,
    ):
        if not isinstance(detector_dropdown_id, dict):
            continue

        id_process_name = "" if detector_dropdown_id.get("process") is None else str(detector_dropdown_id.get("process"))

        if require_process_match and id_process_name != resolved_process_name:
            continue

        channel_name = detector_dropdown_id.get("channel")

        if channel_name is None:
            continue

        if detector_dropdown_value in ("", None):
            continue

        channel_state[str(channel_name)] = detector_dropdown_value

    return channel_state


def resolve_single_detector_channel_value(
    *,
    detector_options: Any = None,
    current_detector_value: Any = None,
    default_detector_value: Any = None,
    fallback_detector_value: Any = None,
    available_detector_options: Any = None,
    current_value: Any = None,
    default_value: Any = None,
    fallback_value: Any = None,
) -> Any:
    """
    Resolve a single detector dropdown value from available detector options.

    Resolution order
    ----------------
    1. Current value, if still present in options.
    2. Default value, if present in options.
    3. Fallback value, if present in options.
    4. First available option value.
    5. None.
    """
    resolved_options = detector_options

    if resolved_options is None:
        resolved_options = available_detector_options

    resolved_current_value = current_detector_value

    if resolved_current_value is None:
        resolved_current_value = current_value

    resolved_default_value = default_detector_value

    if resolved_default_value is None:
        resolved_default_value = default_value

    resolved_fallback_value = fallback_detector_value

    if resolved_fallback_value is None:
        resolved_fallback_value = fallback_value

    option_values = extract_option_values(
        resolved_options,
    )

    if resolved_current_value in option_values:
        return resolved_current_value

    if resolved_default_value in option_values:
        return resolved_default_value

    if resolved_fallback_value in option_values:
        return resolved_fallback_value

    if option_values:
        return option_values[0]

    return None


def extract_option_values(
    detector_options: Any,
) -> list[Any]:
    """
    Extract Dash dropdown option values from common option formats.
    """
    if detector_options is None:
        return []

    option_values: list[Any] = []

    for option in detector_options:
        if isinstance(option, dict):
            if "value" in option:
                option_values.append(
                    option["value"],
                )

            continue

        option_values.append(
            option,
        )

    return option_values


__all__ = [
    "DEFAULT_PROCESS_NAME",
    "build_peak_process_options",
    "build_script_map",
    "clean_optional_string",
    "collect_detector_channel_state",
    "extract_option_values",
    "find_script_class_in_module",
    "get_default_script_name",
    "get_peak_process_instances",
    "get_process_instance",
    "load_peak_scripts",
    "resolve_detector_channel_state",
    "resolve_pattern_detector_channel_state",
    "resolve_process_name",
    "resolve_single_detector_channel_value",
]