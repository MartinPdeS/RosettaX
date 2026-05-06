# -*- coding: utf-8 -*-

import copy
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
DEFAULT_DETECTOR_PRESET_DIRECTORY = Path(__file__).with_name("presets")


class DetectorPresetLoader:
    """
    Load detector presets from a directory with per-file mtime caching.

    The class boundary keeps preset discovery and light preset normalization in
    one place so detector definitions can evolve without spreading path and
    schema details across the workflow.
    """

    def __init__(
        self,
        preset_directory: Path | str | None = None,
    ) -> None:
        self.preset_directory = Path(
            preset_directory or DEFAULT_DETECTOR_PRESET_DIRECTORY
        )
        self._detector_preset_cache: dict[Path, tuple[int, dict[str, Any]]] = {}

    def load_presets(self) -> dict[str, dict[str, Any]]:
        """
        Load detector configuration presets from JSON files.

        The directory is scanned on every call so added or changed preset files
        are visible without restarting the app.
        """
        detector_presets: dict[str, dict[str, Any]] = {}
        detector_directory = self.preset_directory.resolve()

        if not detector_directory.exists():
            logger.warning(
                "Detector preset directory does not exist: %s",
                detector_directory,
            )
            return detector_presets

        for detector_preset_path in sorted(detector_directory.glob("*.json")):
            try:
                detector_preset = self._load_detector_preset_from_file(
                    detector_preset_path,
                )
                normalized_detector_preset = self._normalize_detector_preset(
                    detector_preset=detector_preset,
                    detector_preset_path=detector_preset_path,
                )
            except TypeError:
                logger.warning(
                    "Ignoring detector preset because JSON root is not an object: %s",
                    detector_preset_path,
                )
                continue
            except ValueError:
                logger.warning(
                    "Ignoring detector preset because it is invalid: %s",
                    detector_preset_path,
                )
                continue
            except Exception:
                logger.exception(
                    "Failed to load detector preset JSON file: %s",
                    detector_preset_path,
                )
                continue

            detector_presets[normalized_detector_preset["name"]] = normalized_detector_preset

        logger.debug(
            "Loaded %d detector presets from %s",
            len(detector_presets),
            detector_directory,
        )

        return detector_presets

    def load_preset_options(self) -> list[dict[str, str]]:
        """
        Build dropdown options for all discovered detector presets.
        """
        detector_presets = self.load_presets()

        return [
            {
                "label": preset_name,
                "value": preset_name,
            }
            for preset_name in sorted(detector_presets)
        ]

    def load_preset(
        self,
        preset_name: Any,
    ) -> dict[str, Any]:
        """
        Load one detector preset by name from disk.

        Returns an empty dict if the preset does not exist.
        """
        if preset_name is None:
            return {}

        detector_presets = self.load_presets()

        return detector_presets.get(str(preset_name), {})

    def _load_detector_preset_from_file(
        self,
        detector_preset_path: Path,
    ) -> dict[str, Any]:
        resolved_detector_preset_path = Path(detector_preset_path).resolve()
        file_stat = resolved_detector_preset_path.stat()
        cached_entry = self._detector_preset_cache.get(resolved_detector_preset_path)

        if cached_entry is not None and cached_entry[0] == file_stat.st_mtime_ns:
            return copy.deepcopy(cached_entry[1])

        detector_preset = json.loads(
            resolved_detector_preset_path.read_text(encoding="utf-8")
        )

        if not isinstance(detector_preset, dict):
            raise TypeError("Detector preset JSON root must be an object.")

        self._detector_preset_cache[resolved_detector_preset_path] = (
            file_stat.st_mtime_ns,
            copy.deepcopy(detector_preset),
        )

        return copy.deepcopy(detector_preset)

    def _normalize_detector_preset(
        self,
        *,
        detector_preset: dict[str, Any],
        detector_preset_path: Path,
    ) -> dict[str, Any]:
        normalized_detector_preset = copy.deepcopy(detector_preset)
        detector_preset_name = str(
            normalized_detector_preset.get(
                "name",
                detector_preset_path.stem,
            )
        ).strip()

        if not detector_preset_name:
            raise ValueError("Detector preset name must not be empty.")

        normalized_detector_preset["name"] = detector_preset_name
        normalized_detector_preset["_path"] = str(detector_preset_path.resolve())

        normalized_angular_weighting = _normalize_angular_weighting_definition(
            normalized_detector_preset,
        )
        if normalized_angular_weighting is not None:
            normalized_detector_preset["detector_angular_weighting"] = normalized_angular_weighting

        return normalized_detector_preset


def _normalize_angular_weighting_definition(
    detector_preset: dict[str, Any],
) -> dict[str, Any] | None:
    angular_weighting = detector_preset.get("detector_angular_weighting")

    if isinstance(angular_weighting, dict):
        return copy.deepcopy(angular_weighting)

    legacy_profile_name = detector_preset.get("detector_angular_weight_profile")

    if legacy_profile_name in (None, ""):
        return None

    normalized_legacy_profile_name = str(legacy_profile_name).strip().lower()

    legacy_profile_mapping: dict[str, dict[str, Any]] = {
        "split-side-half": {
            "mode": "split",
            "metric": "x-minus-z",
            "keep": "positive",
        },
        "split-forward-half": {
            "mode": "split",
            "metric": "x-minus-z",
            "keep": "negative",
        },
        "zero-x-positive": {
            "mode": "split",
            "metric": "mesh-x",
            "keep": "nonpositive",
        },
        "local-split-positive-side": {
            "mode": "split",
            "metric": "local-plane",
            "keep": "positive",
        },
        "local-split-negative-side": {
            "mode": "split",
            "metric": "local-plane",
            "keep": "negative",
        },
        "first-half-zero": {
            "mode": "index-split",
            "keep": "second-half",
        },
    }

    return copy.deepcopy(legacy_profile_mapping.get(normalized_legacy_profile_name))


_DEFAULT_DETECTOR_PRESET_LOADER = DetectorPresetLoader()


def get_default_detector_preset_loader() -> DetectorPresetLoader:
    return _DEFAULT_DETECTOR_PRESET_LOADER


def load_detector_configuration_presets() -> dict[str, dict[str, Any]]:
    """
    Load detector configuration presets from JSON files.

    This function reads from disk every time it is called so changes to JSON
    files are visible without restarting the Dash server.
    """
    return get_default_detector_preset_loader().load_presets()


def load_detector_configuration_preset_options() -> list[dict[str, str]]:
    """
    Load detector preset dropdown options from JSON files.
    """
    return get_default_detector_preset_loader().load_preset_options()


def load_detector_configuration_preset(
    preset_name: Any,
) -> dict[str, Any]:
    """
    Load one detector preset by name from disk.

    Returns an empty dict if the preset does not exist.
    """
    return get_default_detector_preset_loader().load_preset(preset_name)
