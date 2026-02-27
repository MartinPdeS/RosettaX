
from typing import Any, Optional
from dataclasses import dataclass
import json
import os
import re
from datetime import datetime
from pathlib import Path


from RosettaX.utils.reader import FCSFile

@dataclass(frozen=True)
class ChannelOptions:
    scatter_options: list[dict[str, str]]
    fluorescence_options: list[dict[str, str]]
    scatter_value: Optional[str]
    fluorescence_value: Optional[str]


class FileStateRefresher:
    def __init__(self, *, scatter_keywords: list[str], non_valid_keywords: list[str]) -> None:
        self.scatter_keywords = [str(k).lower() for k in scatter_keywords]
        self.non_valid_keywords = [str(k).lower() for k in non_valid_keywords]

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
            lower = str(column).strip().lower()
            is_scatter = any(keyword in lower for keyword in self.scatter_keywords)
            is_invalid = any(keyword in lower for keyword in self.non_valid_keywords)

            if is_scatter:
                scatter_options.append({"label": str(column), "value": str(column)})
            elif not is_invalid:
                fluorescence_options.append({"label": str(column), "value": str(column)})

        scatter_value = None
        fluorescence_value = None

        preferred_scatter = str(preferred_scatter or "").strip()
        preferred_fluorescence = str(preferred_fluorescence or "").strip()

        if preferred_scatter and any(o["value"] == preferred_scatter for o in scatter_options):
            scatter_value = preferred_scatter
        elif scatter_options:
            scatter_value = scatter_options[0]["value"]

        if preferred_fluorescence and any(o["value"] == preferred_fluorescence for o in fluorescence_options):
            fluorescence_value = preferred_fluorescence
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

    Saves each calibration as a JSON file on disk and can list saved calibrations
    for populating the sidebar.

    Directory selection
    -------------------
    Uses environment variable ROSETTAX_CALIBRATION_DIR if defined,
    otherwise defaults to ~/.rosettax/calibrations
    """

    fluorescence_folder = "fluorescence"

    @staticmethod
    def _root_dir() -> Path:
        env = os.environ.get("ROSETTAX_CALIBRATION_DIR", "").strip()
        if env:
            root = Path(env).expanduser()
        else:
            root = Path.home() / ".rosettax" / "calibrations"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        s = str(name or "").strip()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^A-Za-z0-9 _().]", "", s)
        s = s.replace(" ", "_")
        if not s:
            s = "calibration"
        return s

    @classmethod
    def _folder_dir(cls, folder: str) -> Path:
        p = cls._root_dir() / str(folder)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def save_fluorescent_setup_to_file(cls, *, name: str, payload: dict[str, Any]) -> SavedCalibrationInfo:
        folder = cls.fluorescence_folder
        out_dir = cls._folder_dir(folder)

        safe = cls._sanitize_filename(name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"{safe}_{stamp}.json"
        filename = f"{safe}.json"
        path = out_dir / filename

        record = {
            "schema": "rosettax_calibration_v1",
            "kind": "fluorescence",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "name": str(name),
            "payload": payload,
        }

        path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        return SavedCalibrationInfo(folder=folder, filename=filename, path=path)

    @classmethod
    def list_saved_calibrations(cls) -> dict[str, list[str]]:
        """
        Returns a dict shaped like your Sidebar expects:
            { folder_name: [file1, file2, ...] }
        """
        root = cls._root_dir()

        result: dict[str, list[str]] = {}
        if not root.exists():
            return result

        for folder_path in sorted([p for p in root.iterdir() if p.is_dir()]):
            files = sorted([p.name for p in folder_path.glob("*.json") if p.is_file()])
            if files:
                result[folder_path.name] = files

        return result