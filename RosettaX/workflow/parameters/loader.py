# -*- coding: utf-8 -*-
import copy
import json
import logging
from pathlib import Path
from typing import Any

from RosettaX.utils import directories


logger = logging.getLogger(__name__)
_DETECTOR_PRESET_CACHE: dict[Path, tuple[int, dict[str, Any]]] = {}


def _load_detector_preset_from_file(
    detector_preset_path: Path,
) -> dict[str, Any]:
    """
    Load one detector preset JSON file with mtime-based caching.
    """
    resolved_detector_preset_path = Path(detector_preset_path).resolve()
    file_stat = resolved_detector_preset_path.stat()
    cached_entry = _DETECTOR_PRESET_CACHE.get(resolved_detector_preset_path)

    if cached_entry is not None and cached_entry[0] == file_stat.st_mtime_ns:
        return copy.deepcopy(cached_entry[1])

    detector_preset = json.loads(
        resolved_detector_preset_path.read_text(encoding="utf-8")
    )

    if not isinstance(detector_preset, dict):
        raise TypeError("Detector preset JSON root must be an object.")

    _DETECTOR_PRESET_CACHE[resolved_detector_preset_path] = (
        file_stat.st_mtime_ns,
        copy.deepcopy(detector_preset),
    )

    return copy.deepcopy(detector_preset)


def load_detector_configuration_presets() -> dict[str, dict[str, Any]]:
    """
    Load detector configuration presets from JSON files.

    This function reads from disk every time it is called so changes to JSON
    files are visible without restarting the Dash server.
    """
    detector_presets: dict[str, dict[str, Any]] = {}

    detector_directory = Path(directories.detectors)

    if not detector_directory.exists():
        logger.warning(
            "Detector preset directory does not exist: %s",
            detector_directory,
        )
        return detector_presets

    for detector_preset_path in sorted(detector_directory.glob("*.json")):
        try:
            detector_preset = _load_detector_preset_from_file(detector_preset_path)
        except TypeError:
            logger.warning(
                "Ignoring detector preset because JSON root is not an object: %s",
                detector_preset_path,
            )
            continue
        except Exception:
            logger.exception(
                "Failed to load detector preset JSON file: %s",
                detector_preset_path,
            )
            continue

        detector_preset_name = str(
            detector_preset.get(
                "name",
                detector_preset_path.stem,
            )
        ).strip()

        if not detector_preset_name:
            logger.warning(
                "Ignoring detector preset with empty name: %s",
                detector_preset_path,
            )
            continue

        detector_preset["name"] = detector_preset_name
        detector_preset["_path"] = str(detector_preset_path)

        detector_presets[detector_preset_name] = detector_preset

    logger.debug(
        "Loaded %d detector presets from %s",
        len(detector_presets),
        detector_directory,
    )

    return detector_presets


def load_detector_configuration_preset_options() -> list[dict[str, str]]:
    """
    Load detector preset dropdown options from JSON files.
    """
    detector_presets = load_detector_configuration_presets()

    return [
        {
            "label": preset_name,
            "value": preset_name,
        }
        for preset_name in sorted(detector_presets)
    ]


def load_detector_configuration_preset(
    preset_name: Any,
) -> dict[str, Any]:
    """
    Load one detector preset by name from disk.

    Returns an empty dict if the preset does not exist.
    """
    if preset_name is None:
        return {}

    detector_presets = load_detector_configuration_presets()

    return detector_presets.get(str(preset_name), {})
