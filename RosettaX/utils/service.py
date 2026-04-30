from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import logging
import re

from RosettaX.utils.reader import FCSFile


logger = logging.getLogger(__name__)


SCATTER_KEYWORDS = [
    "scatter",
    "fsc",
    "ssc",
    "sals",
    "lals",
    "mals",
    "405ls",
    "488ls",
    "638ls",
    "fs-a",
    "fs-h",
    "ss-a",
    "ss-h",
]

NON_VALID_KEYWORDS = [
    "time",
    "width",
    "diameter",
    "cross section",
]


@dataclass(frozen=True)
class ChannelOptions:
    """
    Detector options derived from an FCS file.

    Attributes
    ----------
    scatter_options : list[dict[str, str]]
        Dropdown options for scattering channels.
    secondary_options : list[dict[str, str]]
        Dropdown options for the secondary detector family.
    scatter_value : Optional[str]
        Default scattering selection.
    secondary_value : Optional[str]
        Default secondary detector selection.
    """

    scatter_options: list[dict[str, str]]
    secondary_options: list[dict[str, str]]
    scatter_value: Optional[str]
    secondary_value: Optional[str]


@dataclass(frozen=True)
class SavedCalibrationInfo:
    """
    Information about a saved calibration file.

    Attributes
    ----------
    folder : str
        Logical folder name used by the UI.
    filename : str
        Saved file name.
    path : Path
        Full output path.
    """

    folder: str
    filename: str
    path: Path


def sanitize_filename(name: str) -> str:
    """
    Sanitize a user provided calibration name into a safe filename stem.

    Parameters
    ----------
    name : str
        Raw calibration name.

    Returns
    -------
    str
        Sanitized filename stem.
    """
    sanitized_name = str(name or "").strip()
    sanitized_name = re.sub(r"\s+", " ", sanitized_name)
    sanitized_name = re.sub(r"[^A-Za-z0-9 _().]", "", sanitized_name)
    sanitized_name = sanitized_name.replace(" ", "_")

    if not sanitized_name:
        sanitized_name = "calibration"

    return sanitized_name


def get_detector_column_names_from_file(file_path: str) -> list[str]:
    """
    Extract detector column names from an FCS file.

    Parameters
    ----------
    file_path : str
        FCS file path.

    Returns
    -------
    list[str]
        Detector column names in file order.
    """
    with FCSFile(str(file_path), writable=False) as fcs_file:
        detectors = fcs_file.text["Detectors"]
        parameter_count = int(fcs_file.text["Keywords"]["$PAR"])

        return [
            str(detectors[index].get("N", f"P{index}"))
            for index in range(1, parameter_count + 1)
        ]


def is_scatter_channel(column_name: str) -> bool:
    """
    Determine whether a detector name should be treated as a scattering channel.

    Parameters
    ----------
    column_name : str
        Detector column name.

    Returns
    -------
    bool
        True if the column matches known scatter keywords.
    """
    lowered_column_name = str(column_name).strip().lower()
    return any(keyword in lowered_column_name for keyword in SCATTER_KEYWORDS)


def is_invalid_detector_channel(column_name: str) -> bool:
    """
    Determine whether a detector name should be excluded from selectable channels.

    Parameters
    ----------
    column_name : str
        Detector column name.

    Returns
    -------
    bool
        True if the column matches invalid keywords.
    """
    lowered_column_name = str(column_name).strip().lower()
    return any(keyword in lowered_column_name for keyword in NON_VALID_KEYWORDS)


def resolve_default_dropdown_value(
    *,
    options: list[dict[str, str]],
    preferred_value: Optional[str],
) -> Optional[str]:
    """
    Resolve the default dropdown value from a preferred value and an option list.

    Parameters
    ----------
    options : list[dict[str, str]]
        Dropdown options.
    preferred_value : Optional[str]
        Preferred selected value.

    Returns
    -------
    Optional[str]
        Resolved dropdown value.
    """
    cleaned_preferred_value = str(preferred_value or "").strip()

    if cleaned_preferred_value and any(
        option["value"] == cleaned_preferred_value
        for option in options
    ):
        return cleaned_preferred_value

    if options:
        return options[0]["value"]

    return None


# def build_channel_options_from_file(
#     file_path: str,
#     *,
#     preferred_scatter: Optional[str] = None,
#     preferred_secondary: Optional[str] = None,
# ) -> ChannelOptions:
#     """
#     Derive detector options from an FCS file.

#     Parameters
#     ----------
#     file_path : str
#         FCS file path.
#     preferred_scatter : Optional[str]
#         Preferred scattering detector if present.
#     preferred_secondary : Optional[str]
#         Preferred secondary detector if present.

#     Returns
#     -------
#     ChannelOptions
#         Dropdown options and default values.
#     """
#     detector_column_names = get_detector_column_names_from_file(file_path)

#     scatter_options: list[dict[str, str]] = []
#     secondary_options: list[dict[str, str]] = []

#     for detector_column_name in detector_column_names:
#         if is_invalid_detector_channel(detector_column_name):
#             continue

#         detector_option = {
#             "label": str(detector_column_name),
#             "value": str(detector_column_name),
#         }

#         if is_scatter_channel(detector_column_name):
#             scatter_options.append(detector_option)
#         else:
#             secondary_options.append(detector_option)

#     scatter_value = resolve_default_dropdown_value(
#         options=scatter_options,
#         preferred_value=preferred_scatter,
#     )
#     secondary_value = resolve_default_dropdown_value(
#         options=secondary_options,
#         preferred_value=preferred_secondary,
#     )

#     return ChannelOptions(
#         scatter_options=scatter_options,
#         secondary_options=secondary_options,
#         scatter_value=scatter_value,
#         secondary_value=secondary_value,
#     )


def save_calibration_to_file(
    *,
    name: str,
    payload: dict[str, Any],
    calibration_kind: str,
    output_directory: Path,
) -> SavedCalibrationInfo:
    """
    Save a calibration payload as JSON.

    Parameters
    ----------
    name : str
        User visible calibration name.
    payload : dict[str, Any]
        Calibration payload.
    calibration_kind : str
        Calibration kind stored in the file, for example "fluorescence" or "scattering".
    output_directory : Path
        Output directory for saved calibration files.

    Returns
    -------
    SavedCalibrationInfo
        Saved file information.
    """
    safe_name = sanitize_filename(name)
    filename = f"{safe_name}.json"
    output_path = Path(output_directory) / filename

    record = {
        "schema": "rosettax_calibration_v1",
        "kind": str(calibration_kind),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "name": str(name),
        "payload": payload,
    }

    output_path.write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    logger.debug(
        "Saved calibration to output_path=%r calibration_kind=%r",
        str(output_path),
        calibration_kind,
    )

    return SavedCalibrationInfo(
        folder=str(calibration_kind),
        filename=filename,
        path=output_path,
    )


def list_saved_calibrations_from_directory(
    *,
    directory: Path,
) -> dict[str, list[str]]:
    """
    List saved calibration files in the format expected by the sidebar.

    Parameters
    ----------
    folder_name : str
        Logical folder name used by the UI.
    directory : Path
        Directory containing saved calibration files.

    Returns
    -------
    dict[str, list[str]]
        Mapping folder name to list of filenames.
    """
    files = sorted(
        file_path.name
        for file_path in Path(directory).glob("*.json")
        if file_path.is_file()
    )

    if not files:
        return []

    return files

def resolve_first_fcs_path(uploaded_fcs_path_data: Any) -> Optional[str]:
    """
    Extract the first non-empty FCS file path from an uploaded path payload.

    Dash upload components may wrap the path in nested lists.  This helper
    unwraps any level of list nesting, returning the first scalar string value
    it finds.

    Parameters
    ----------
    uploaded_fcs_path_data : Any
        Raw upload payload – may be ``None``, a plain string, or a (nested)
        list of strings.

    Returns
    -------
    Optional[str]
        The first non-empty path string, or ``None`` if nothing valid is found.
    """
    if uploaded_fcs_path_data is None:
        return None

    current_value = uploaded_fcs_path_data

    while isinstance(current_value, list):
        if not current_value:
            return None
        current_value = current_value[0]

    if current_value is None:
        return None

    resolved_path = str(current_value).strip()
    return resolved_path or None
