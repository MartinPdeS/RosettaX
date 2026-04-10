from typing import Any, Optional
from dataclasses import dataclass
import json
import re
from datetime import datetime
from pathlib import Path

from RosettaX.utils.reader import FCSFile
from RosettaX.utils.directories import fluorescence_calibration_directory, scattering_calibration_directory


@dataclass(frozen=True)
class ChannelOptions:
    scatter_options: list[dict[str, str]]
    fluorescence_options: list[dict[str, str]]
    scatter_value: Optional[str]
    fluorescence_value: Optional[str]


class FileStateRefresher:
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
        with FCSFile(str(file_path), writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            num_parameters = int(fcs_file.text["Keywords"]["$PAR"])

            columns = [
                str(detectors[index].get("N", f"P{index}"))
                for index in range(1, num_parameters + 1)
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


@dataclass(frozen=True)
class SavedCalibrationInfo:
    folder: str
    filename: str
    path: Path


class CalibrationFileStore:
    """
    File based calibration storage.

    Saves each calibration as a JSON file directly inside the calibration
    directories defined in RosettaX.directories.
    """

    fluorescence_folder = "fluorescence"
    scattering_folder = "scattering"

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        sanitized_name = str(name or "").strip()
        sanitized_name = re.sub(r"\s+", " ", sanitized_name)
        sanitized_name = re.sub(r"[^A-Za-z0-9 _().]", "", sanitized_name)
        sanitized_name = sanitized_name.replace(" ", "_")

        if not sanitized_name:
            sanitized_name = "calibration"

        return sanitized_name

    @staticmethod
    def _fluorescence_directory() -> Path:
        directory = Path(fluorescence_calibration_directory).expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _scattering_directory() -> Path:
        directory = Path(scattering_calibration_directory).expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def save_fluorescent_setup_to_file(
        cls,
        *,
        name: str,
        payload: dict[str, Any],
    ) -> SavedCalibrationInfo:
        output_directory = cls._fluorescence_directory()
        sanitized_name = cls._sanitize_filename(name)

        filename = f"{sanitized_name}.json"
        path = output_directory / filename

        record = {
            "schema": "rosettax_calibration_v1",
            "kind": "fluorescence",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "name": str(name),
            "payload": payload,
        }

        path.write_text(
            json.dumps(record, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return SavedCalibrationInfo(
            folder=cls.fluorescence_folder,
            filename=filename,
            path=path,
        )

    @classmethod
    def save_scattering_setup_to_file(
        cls,
        *,
        name: str,
        payload: dict[str, Any],
    ) -> SavedCalibrationInfo:
        output_directory = cls._scattering_directory()
        sanitized_name = cls._sanitize_filename(name)

        filename = f"{sanitized_name}.json"
        path = output_directory / filename

        record = {
            "schema": "rosettax_calibration_v1",
            "kind": "scattering",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "name": str(name),
            "payload": payload,
        }

        path.write_text(
            json.dumps(record, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return SavedCalibrationInfo(
            folder=cls.scattering_folder,
            filename=filename,
            path=path,
        )

    @classmethod
    def list_saved_calibrations(cls) -> dict[str, list[str]]:
        """
        Returns a dict shaped like the Sidebar expects:
            {
                "fluorescence": [file1, file2, ...],
                "scattering": [file1, file2, ...],
            }
        """
        fluorescence_directory = cls._fluorescence_directory()
        scattering_directory = cls._scattering_directory()

        fluorescence_files = sorted(
            file_path.name
            for file_path in fluorescence_directory.glob("*.json")
            if file_path.is_file()
        )
        scattering_files = sorted(
            file_path.name
            for file_path in scattering_directory.glob("*.json")
            if file_path.is_file()
        )

        result: dict[str, list[str]] = {}

        if fluorescence_files:
            result[cls.fluorescence_folder] = fluorescence_files

        if scattering_files:
            result[cls.scattering_folder] = scattering_files

        return result