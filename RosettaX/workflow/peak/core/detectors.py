# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

from .. import registry
from RosettaX.utils.reader import FCSFile


logger = logging.getLogger(__name__)


def clean_optional_string(value: Any) -> str:
    """
    Normalize an optional string value.

    Parameters
    ----------
    value:
        Raw value.

    Returns
    -------
    str
        Clean string.
    """
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def populate_peak_script_detector_dropdowns(
    *,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    current_detector_values: list[Any],
    logger: logging.Logger,
) -> tuple[list[list[dict[str, Any]]], list[Any]]:
    """
    Populate every detector dropdown owned by peak scripts.

    Parameters
    ----------
    uploaded_fcs_path:
        Uploaded FCS file path.

    detector_dropdown_ids:
        Pattern matched detector dropdown IDs.

    current_detector_values:
        Current dropdown values.

    logger:
        Logger.

    Returns
    -------
    tuple[list[list[dict[str, Any]]], list[Any]]
        Dropdown options and resolved values.
    """
    uploaded_fcs_path_clean = clean_optional_string(
        uploaded_fcs_path,
    )

    dropdown_count = len(
        detector_dropdown_ids or [],
    )

    logger.debug(
        "Populating peak detector dropdowns uploaded_fcs_path=%r dropdown_count=%d "
        "detector_dropdown_ids=%r current_detector_values=%r",
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

    options = [
        {
            "label": column_name,
            "value": column_name,
        }
        for column_name in column_names
    ]

    valid_values = {
        option["value"]
        for option in options
    }

    default_value = infer_default_detector_channel(
        column_names=column_names,
    )

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

        resolved_values.append(
            default_value,
        )

        logger.debug(
            "Detector dropdown id=%r had invalid current_value=%r. Using default_value=%r.",
            detector_dropdown_id,
            current_value,
            default_value,
        )

    return resolved_options, resolved_values


def infer_default_detector_channel(
    *,
    column_names: list[str],
) -> Optional[str]:
    """
    Infer a reasonable default detector channel.

    Parameters
    ----------
    column_names:
        FCS column names.

    Returns
    -------
    Optional[str]
        Default channel name.
    """
    preferred_keywords = [
        "ssc",
        "fsc",
        "scatter",
        "fl",
        "height",
        "area",
    ]

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
        Pattern matched dropdown IDs.

    detector_dropdown_values:
        Pattern matched dropdown values.

    process_name:
        Selected process name.

    Returns
    -------
    dict[str, Any]
        Mapping from logical channel name to selected FCS column.
    """
    channel_state = registry.resolve_detector_channel_state(
        detector_dropdown_ids=detector_dropdown_ids or [],
        detector_dropdown_values=detector_dropdown_values or [],
        process_name=process_name,
    )

    logger.debug(
        "Resolved detector channel state process_name=%r channel_state=%r",
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
    Resolve process setting values for the selected process.

    Parameters
    ----------
    process_setting_ids:
        Pattern matched setting IDs.

    process_setting_values:
        Pattern matched setting values.

    process_name:
        Selected process name.

    Returns
    -------
    dict[str, Any]
        Mapping from setting name to value.
    """
    resolved_process_name = registry.resolve_process_name(
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
        "Resolved process setting state process_name=%r setting_state=%r",
        resolved_process_name,
        setting_state,
    )

    return setting_state