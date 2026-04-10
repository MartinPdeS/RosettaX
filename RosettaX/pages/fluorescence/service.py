from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import logging
import re

from RosettaX.utils.reader import FCSFile
from RosettaX.utils.directories import fluorescence_calibration_directory



logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChannelOptions:
    """
    Detector options derived from an FCS file.

    Attributes
    ----------
    scatter_options : list[dict[str, str]]
        Dropdown options for scattering channels.
    fluorescence_options : list[dict[str, str]]
        Dropdown options for fluorescence channels.
    scatter_value : Optional[str]
        Default scattering selection.
    fluorescence_value : Optional[str]
        Default fluorescence selection.
    """

    scatter_options: list[dict[str, str]]
    fluorescence_options: list[dict[str, str]]
    scatter_value: Optional[str]
    fluorescence_value: Optional[str]


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


class FileStateRefresher:
    """
    Build detector dropdown options from an FCS file.
    """

    scatter_keywords = [
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

    non_valid_keywords = [
        "time",
        "width",
        "diameter",
        "cross section",
    ]

    def options_from_file(
        self,
        file_path: str,
        *,
        preferred_scatter: Optional[str] = None,
        preferred_fluorescence: Optional[str] = None,
    ) -> ChannelOptions:
        """
        Derive detector options from an FCS file.

        Parameters
        ----------
        file_path : str
            FCS file path.
        preferred_scatter : Optional[str]
            Preferred scattering detector if present.
        preferred_fluorescence : Optional[str]
            Preferred fluorescence detector if present.

        Returns
        -------
        ChannelOptions
            Dropdown options and default values.
        """
        with FCSFile(str(file_path), writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            parameter_count = int(fcs_file.text["Keywords"]["$PAR"])

            columns = [
                str(detectors[index].get("N", f"P{index}"))
                for index in range(1, parameter_count + 1)
            ]

        scatter_options: list[dict[str, str]] = []
        fluorescence_options: list[dict[str, str]] = []

        for column in columns:
            lower_column = str(column).strip().lower()
            is_scatter = any(keyword in lower_column for keyword in self.scatter_keywords)
            is_invalid = any(keyword in lower_column for keyword in self.non_valid_keywords)

            if is_scatter:
                scatter_options.append({"label": str(column), "value": str(column)})
            elif not is_invalid:
                fluorescence_options.append({"label": str(column), "value": str(column)})

        scatter_value = None
        fluorescence_value = None

        preferred_scatter_clean = str(preferred_scatter or "").strip()
        preferred_fluorescence_clean = str(preferred_fluorescence or "").strip()

        if preferred_scatter_clean and any(option["value"] == preferred_scatter_clean for option in scatter_options):
            scatter_value = preferred_scatter_clean
        elif scatter_options:
            scatter_value = scatter_options[0]["value"]

        if preferred_fluorescence_clean and any(
            option["value"] == preferred_fluorescence_clean for option in fluorescence_options
        ):
            fluorescence_value = preferred_fluorescence_clean
        elif fluorescence_options:
            fluorescence_value = fluorescence_options[0]["value"]

        return ChannelOptions(
            scatter_options=scatter_options,
            fluorescence_options=fluorescence_options,
            scatter_value=scatter_value,
            fluorescence_value=fluorescence_value,
        )


def _sanitize_filename(name: str) -> str:
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


def _fluorescence_calibration_output_directory() -> Path:
    """
    Return the fluorescence calibration output directory.

    Returns
    -------
    Path
        Existing output directory.
    """
    output_directory = Path(fluorescence_calibration_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory


def save_fluorescent_setup_to_file(*, name: str, payload: dict[str, Any]) -> SavedCalibrationInfo:
    """
    Save a fluorescence calibration payload as JSON.

    Parameters
    ----------
    name : str
        User visible calibration name.
    payload : dict[str, Any]
        Calibration payload.

    Returns
    -------
    SavedCalibrationInfo
        Saved file information.
    """
    output_directory = _fluorescence_calibration_output_directory()
    safe_name = _sanitize_filename(name)
    filename = f"{safe_name}.json"
    output_path = output_directory / filename

    record = {
        "schema": "rosettax_calibration_v1",
        "kind": "fluorescence",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "name": str(name),
        "payload": payload,
    }

    output_path.write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    logger.debug("Saved fluorescence calibration to output_path=%r", str(output_path))

    return SavedCalibrationInfo(
        folder="fluorescence",
        filename=filename,
        path=output_path,
    )


def list_saved_calibrations() -> dict[str, list[str]]:
    """
    List saved fluorescence calibrations in the format expected by the sidebar.

    Returns
    -------
    dict[str, list[str]]
        Mapping folder name to list of filenames.
    """
    output_directory = _fluorescence_calibration_output_directory()

    files = sorted(
        file_path.name
        for file_path in output_directory.glob("*.json")
        if file_path.is_file()
    )

    if not files:
        return {}

    return {"fluorescence": files}