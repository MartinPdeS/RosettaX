# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

from RosettaX.peak_script.registry import resolve_process_name
from RosettaX.peak_script import resolve_detector_channel_state
from RosettaX.utils.reader import FCSFile

from .services_common import clean_optional_string


logger = logging.getLogger(__name__)


def populate_peak_script_detector_dropdowns(
    *,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    current_detector_values: list[Any],
    logger: logging.Logger,
) -> tuple[list[list[dict[str, Any]]], list[Any]]:
    """
    Populate every detector dropdown owned by peak scripts.

    Each dropdown receives the same available FCS column options, but the default
    value is resolved per channel name. This avoids assigning the same default
    channel to x and y in 2D workflows whenever better channel-specific defaults
    are available.
    """
    uploaded_fcs_path_clean = clean_optional_string(uploaded_fcs_path)
    dropdown_count = len(detector_dropdown_ids or [])

    logger.debug(
        "Populating peak script detector dropdowns uploaded_fcs_path=%r "
        "dropdown_count=%d detector_dropdown_ids=%r current_detector_values=%r",
        uploaded_fcs_path_clean,
        dropdown_count,
        detector_dropdown_ids,
        current_detector_values,
    )

    if not uploaded_fcs_path_clean:
        return (
            [
                []
                for _ in range(dropdown_count)
            ],
            [
                None
                for _ in range(dropdown_count)
            ],
        )

    try:
        with FCSFile(uploaded_fcs_path_clean) as fcs_file:
            column_names = fcs_file.get_column_names()

    except Exception:
        logger.exception(
            "Failed to read FCS column names from uploaded_fcs_path=%r",
            uploaded_fcs_path_clean,
        )

        return (
            [
                []
                for _ in range(dropdown_count)
            ],
            [
                None
                for _ in range(dropdown_count)
            ],
        )

    options = build_detector_options(
        column_names=column_names,
    )

    valid_values = {
        option["value"]
        for option in options
    }

    resolved_options: list[list[dict[str, Any]]] = []
    resolved_values: list[Any] = []

    for detector_dropdown_id, current_value in zip(
        detector_dropdown_ids or [],
        current_detector_values or [],
        strict=False,
    ):
        resolved_options.append(
            options,
        )

        if current_value in valid_values:
            resolved_values.append(
                current_value,
            )

            continue

        channel_name = extract_detector_channel_name(
            detector_dropdown_id,
        )

        default_value = infer_default_detector_channel(
            column_names=column_names,
            channel_name=channel_name,
        )

        resolved_values.append(
            default_value,
        )

        logger.debug(
            "Detector dropdown id=%r had invalid current_value=%r. "
            "Using default_value=%r for channel_name=%r.",
            detector_dropdown_id,
            current_value,
            default_value,
            channel_name,
        )

    return resolved_options, resolved_values


def build_detector_options(
    *,
    column_names: list[str],
) -> list[dict[str, str]]:
    """
    Build Dash dropdown options from FCS column names.

    Parameters
    ----------
    column_names:
        FCS channel names.

    Returns
    -------
    list[dict[str, str]]
        Dash dropdown options.
    """
    return [
        {
            "label": str(column_name),
            "value": str(column_name),
        }
        for column_name in column_names
    ]


def extract_detector_channel_name(
    detector_dropdown_id: Any,
) -> str:
    """
    Extract the logical process channel name from a detector dropdown id.

    Parameters
    ----------
    detector_dropdown_id:
        Pattern-matched detector dropdown id.

    Returns
    -------
    str
        Channel name, such as primary, x, or y.
    """
    if not isinstance(detector_dropdown_id, dict):
        return ""

    channel_name = detector_dropdown_id.get("channel")

    if channel_name is None:
        return ""

    return str(channel_name)


def infer_default_detector_channel(
    *,
    column_names: list[str],
    channel_name: str,
) -> Optional[str]:
    """
    Infer a default detector channel from FCS column names.

    Parameters
    ----------
    column_names:
        FCS column names.

    channel_name:
        Logical channel name requested by the selected process.

    Returns
    -------
    Optional[str]
        Best matching FCS column name, or None.
    """
    resolved_channel_name = clean_optional_string(
        channel_name,
    ).lower()

    if resolved_channel_name == "x":
        return infer_default_channel_from_keywords(
            column_names=column_names,
            preferred_keywords=[
                "fsc",
                "fs",
                "scatter",
                "ssc",
                "ss",
            ],
        )

    if resolved_channel_name == "y":
        return infer_default_channel_from_keywords(
            column_names=column_names,
            preferred_keywords=[
                "ssc",
                "ss",
                "scatter",
                "fsc",
                "fs",
            ],
        )

    return infer_default_scattering_channel(
        column_names=column_names,
    )


def infer_default_scattering_channel(
    *,
    column_names: list[str],
) -> Optional[str]:
    """
    Infer a default scattering channel from FCS column names.

    Parameters
    ----------
    column_names:
        FCS column names.

    Returns
    -------
    Optional[str]
        Best matching scattering column name, or None.
    """
    return infer_default_channel_from_keywords(
        column_names=column_names,
        preferred_keywords=[
            "ssc",
            "fsc",
            "scatter",
            "fs",
            "ss",
        ],
    )


def infer_default_channel_from_keywords(
    *,
    column_names: list[str],
    preferred_keywords: list[str],
) -> Optional[str]:
    """
    Infer a default channel by matching preferred keywords.

    Parameters
    ----------
    column_names:
        FCS column names.

    preferred_keywords:
        Keywords in priority order.

    Returns
    -------
    Optional[str]
        Best matching column name, or None.
    """
    for keyword in preferred_keywords:
        for column_name in column_names:
            if keyword in str(column_name).lower():
                return column_name

    if column_names:
        return column_names[0]

    return None


def resolve_detector_channels_for_process(
    *,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_name: Any,
) -> dict[str, Any]:
    """
    Resolve detector channels for the selected process.

    Parameters
    ----------
    detector_dropdown_ids:
        Pattern-matched detector dropdown ids.

    detector_dropdown_values:
        Pattern-matched detector dropdown values.

    process_name:
        Selected process name.

    Returns
    -------
    dict[str, Any]
        Mapping from logical channel name to selected detector column.
    """
    channel_state = resolve_detector_channel_state(
        detector_dropdown_ids=detector_dropdown_ids or [],
        detector_dropdown_values=detector_dropdown_values or [],
        process_name=process_name,
    )

    logger.debug(
        "Resolved detector channel state for process_name=%r channel_state=%r",
        process_name,
        channel_state,
    )

    return channel_state


def resolve_process_setting_state(
    *,
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    process_name: Any,
) -> dict[str, Any]:
    """
    Resolve setting component values for the selected process.

    Parameters
    ----------
    process_setting_ids:
        Pattern-matched setting ids.

    process_setting_values:
        Pattern-matched setting values.

    process_name:
        Selected process name.

    Returns
    -------
    dict[str, Any]
        Mapping from setting name to value.
    """
    resolved_process_name = resolve_process_name(
        process_name,
    )

    setting_state: dict[str, Any] = {}

    for process_setting_id, process_setting_value in zip(
        process_setting_ids or [],
        process_setting_values or [],
        strict=False,
    ):
        if not isinstance(process_setting_id, dict):
            continue

        if process_setting_id.get("process") != resolved_process_name:
            continue

        setting_name = process_setting_id.get("setting")

        if not setting_name:
            continue

        setting_state[str(setting_name)] = process_setting_value

    logger.debug(
        "Resolved process setting state for process_name=%r setting_state=%r",
        resolved_process_name,
        setting_state,
    )

    return setting_state