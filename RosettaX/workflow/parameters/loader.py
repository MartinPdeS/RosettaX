# -*- coding: utf-8 -*-
import json
import logging
from pathlib import Path
from typing import Any

from RosettaX.utils import directories


logger = logging.getLogger(__name__)


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
            detector_preset = json.loads(
                detector_preset_path.read_text(encoding="utf-8")
            )
        except Exception:
            logger.exception(
                "Failed to load detector preset JSON file: %s",
                detector_preset_path,
            )
            continue

        if not isinstance(detector_preset, dict):
            logger.warning(
                "Ignoring detector preset because JSON root is not an object: %s",
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