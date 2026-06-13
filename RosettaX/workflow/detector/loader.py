# -*- coding: utf-8 -*-

import copy
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
DEFAULT_DETECTOR_PRESET_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "detector_definitions.json"
)
DEFAULT_DETECTOR_PRESET_DIRECTORY = DEFAULT_DETECTOR_PRESET_PATH
CUSTOM_DETECTOR_PRESET_NAME = "Generic detector"


class DetectorPresetLoader:
    """
    Load detector presets from a JSON catalog file.

    The class boundary keeps preset discovery and light preset normalization in
    one place so detector definitions can evolve without spreading schema and
    lookup details across the workflow.
    """

    def __init__(
        self,
        preset_directory: Path | str | None = None,
    ) -> None:
        self.preset_path = Path(
            preset_directory or DEFAULT_DETECTOR_PRESET_PATH
        )
        self._detector_preset_cache: dict[Path, tuple[int, Any]] = {}

    def load_presets(self) -> dict[str, dict[str, Any]]:
        """
        Load detector configuration presets from the catalog JSON file.
        """
        detector_presets: dict[str, dict[str, Any]] = {}
        detector_preset_path = self.preset_path.resolve()

        if not detector_preset_path.exists():
            logger.warning(
                "Detector preset catalog does not exist: %s",
                detector_preset_path,
            )
            return detector_presets

        if detector_preset_path.is_dir():
            return self._load_presets_from_directory(
                detector_preset_path,
            )

        detector_preset_document = self._load_detector_preset_document(
            detector_preset_path,
        )
        detector_preset_items = detector_preset_document.get("presets", [])

        if not isinstance(detector_preset_items, list):
            logger.warning(
                "Ignoring detector preset catalog because 'presets' is not a list: %s",
                detector_preset_path,
            )
            return detector_presets

        for detector_preset in detector_preset_items:
            try:
                normalized_detector_preset = self._normalize_detector_preset(
                    detector_preset=detector_preset,
                    detector_preset_path=detector_preset_path,
                )
            except TypeError:
                logger.warning(
                    "Ignoring detector preset because catalog entry is not an object: %s",
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
            "Loaded %d detector presets from catalog %s",
            len(detector_presets),
            detector_preset_path,
        )

        return detector_presets

    def _load_presets_from_directory(
        self,
        detector_directory: Path,
    ) -> dict[str, dict[str, Any]]:
        detector_presets: dict[str, dict[str, Any]] = {}

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
            "Loaded %d detector presets from directory %s",
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

    def load_preset_catalog(self) -> list[dict[str, str]]:
        """
        Build a normalized preset catalog with brand and model labels.
        """
        catalog: list[dict[str, str]] = []

        for preset in self.load_presets().values():
            preset_name = str(preset.get("name", "")).strip()

            if not preset_name:
                continue

            catalog.append(
                {
                    "brand": _resolve_detector_preset_brand_label(preset),
                    "model": _resolve_detector_preset_model_key(preset),
                    "detector_type": _resolve_detector_preset_type_label(preset),
                    "label": _resolve_detector_preset_model_label(preset),
                    "value": preset_name,
                }
            )

        return sorted(
            catalog,
            key=lambda item: (
                item["brand"].lower(),
                item["label"].lower(),
            ),
        )

    def load_brand_options(self) -> list[dict[str, str]]:
        """
        Build dropdown options for detector preset brands.
        """
        brand_labels = sorted(
            {
                item["brand"]
                for item in self.load_preset_catalog()
                if item.get("brand")
            },
            key=str.lower,
        )

        return [
            {
                "label": brand_label,
                "value": brand_label,
            }
            for brand_label in brand_labels
        ]

    def load_model_options(
        self,
        brand: Any,
    ) -> list[dict[str, str]]:
        """
        Build dropdown options for detector preset models under one brand.
        """
        resolved_brand = str(brand or "").strip()

        if not resolved_brand:
            return []

        model_labels = sorted(
            {
                item["model"]
                for item in self.load_preset_catalog()
                if item["brand"] == resolved_brand and item.get("model")
            },
            key=str.lower,
        )

        return [
            {
                "label": model_label,
                "value": model_label,
            }
            for model_label in model_labels
        ]

    def load_type_options(
        self,
        *,
        brand: Any,
        model: Any,
    ) -> list[dict[str, str]]:
        """
        Build detector type options for one brand/model pair.
        """
        resolved_brand = str(brand or "").strip()
        resolved_model = str(model or "").strip()

        if not resolved_brand or not resolved_model:
            return []

        return [
            {
                "label": item["detector_type"],
                "value": item["value"],
            }
            for item in self.load_preset_catalog()
            if item["brand"] == resolved_brand and item["model"] == resolved_model
        ]

    def resolve_preset_brand(
        self,
        preset_name: Any,
    ) -> str | None:
        """
        Resolve the brand label for one preset name.
        """
        preset = self.load_preset(
            preset_name,
        )

        if not preset:
            return None

        return _resolve_detector_preset_brand_label(
            preset,
        )

    def resolve_preset_model(
        self,
        preset_name: Any,
    ) -> str | None:
        """
        Resolve the model label for one preset name.
        """
        preset = self.load_preset(
            preset_name,
        )

        if not preset:
            return None

        return _resolve_detector_preset_model_key(
            preset,
        )

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

    def _load_detector_preset_document(
        self,
        detector_preset_path: Path,
    ) -> dict[str, Any]:
        resolved_detector_preset_path = Path(detector_preset_path).resolve()
        file_stat = resolved_detector_preset_path.stat()
        cached_entry = self._detector_preset_cache.get(resolved_detector_preset_path)

        if cached_entry is not None and cached_entry[0] == file_stat.st_mtime_ns:
            return copy.deepcopy(cached_entry[1])

        detector_preset_document = json.loads(
            resolved_detector_preset_path.read_text(encoding="utf-8")
        )

        if not isinstance(detector_preset_document, dict):
            raise TypeError("Detector preset catalog JSON root must be an object.")

        self._detector_preset_cache[resolved_detector_preset_path] = (
            file_stat.st_mtime_ns,
            copy.deepcopy(detector_preset_document),
        )

        return copy.deepcopy(detector_preset_document)

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
        normalized_detector_preset["alias"] = _normalize_detector_aliases(
            normalized_detector_preset.get("alias"),
        )
        normalized_detector_preset = _normalize_standard_scatter_angles(
            normalized_detector_preset,
        )

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


def _normalize_detector_aliases(
    raw_aliases: Any,
) -> list[str]:
    if raw_aliases in (None, ""):
        return []

    if isinstance(raw_aliases, str):
        alias_values = [raw_aliases]
    elif isinstance(raw_aliases, (list, tuple, set)):
        alias_values = list(raw_aliases)
    else:
        raise ValueError("Detector preset alias must be a string or a list of strings.")

    normalized_aliases: list[str] = []

    for alias_value in alias_values:
        cleaned_alias = _clean_preset_text(alias_value)

        if cleaned_alias and cleaned_alias not in normalized_aliases:
            normalized_aliases.append(cleaned_alias)

    return normalized_aliases


def _normalize_standard_scatter_angles(
    detector_preset: dict[str, Any],
) -> dict[str, Any]:
    normalized_detector_preset = copy.deepcopy(detector_preset)
    channel_name = _clean_preset_text(
        normalized_detector_preset.get("channel"),
    ).upper()

    if channel_name == "FSC":
        normalized_detector_preset["detector_phi_angle_degree"] = 0.0
        normalized_detector_preset["detector_gamma_angle_degree"] = 0.0
        return normalized_detector_preset

    if channel_name == "SSC":
        normalized_detector_preset["detector_phi_angle_degree"] = 90.0
        normalized_detector_preset["detector_gamma_angle_degree"] = 0.0
        return normalized_detector_preset

    return normalized_detector_preset


_DEFAULT_DETECTOR_PRESET_LOADER = DetectorPresetLoader()


def _clean_preset_text(value: Any) -> str:
    return str(value or "").strip()


def _resolve_detector_preset_brand_label(
    detector_preset: dict[str, Any],
) -> str:
    manufacturer = _clean_preset_text(
        detector_preset.get("manufacturer"),
    )

    if manufacturer:
        return manufacturer

    preset_name = _clean_preset_text(
        detector_preset.get("name"),
    )

    if preset_name == CUSTOM_DETECTOR_PRESET_NAME:
        return "Custom"

    return "Other"


def _resolve_detector_preset_model_label(
    detector_preset: dict[str, Any],
) -> str:
    preset_name = _clean_preset_text(
        detector_preset.get("name"),
    )
    manufacturer = _clean_preset_text(
        detector_preset.get("manufacturer"),
    )
    instrument = _clean_preset_text(
        detector_preset.get("instrument"),
    )
    channel = _clean_preset_text(
        detector_preset.get("channel"),
    )

    if preset_name == CUSTOM_DETECTOR_PRESET_NAME:
        return CUSTOM_DETECTOR_PRESET_NAME

    if instrument and instrument.lower() != "ad hoc" and channel:
        return f"{instrument} - {channel}"

    if instrument and instrument.lower() != "ad hoc":
        return instrument

    manufacturer_prefix = f"{manufacturer} - "

    if manufacturer and preset_name.startswith(manufacturer_prefix):
        return preset_name[len(manufacturer_prefix):]

    return preset_name


def _resolve_detector_preset_model_key(
    detector_preset: dict[str, Any],
) -> str:
    preset_name = _clean_preset_text(
        detector_preset.get("name"),
    )

    if preset_name == CUSTOM_DETECTOR_PRESET_NAME:
        return CUSTOM_DETECTOR_PRESET_NAME

    instrument = _clean_preset_text(
        detector_preset.get("instrument"),
    )

    if instrument and instrument.lower() != "ad hoc":
        return instrument

    manufacturer = _clean_preset_text(
        detector_preset.get("manufacturer"),
    )

    if manufacturer:
        return manufacturer

    return _resolve_detector_preset_model_label(
        detector_preset,
    )


def _resolve_detector_preset_type_label(
    detector_preset: dict[str, Any],
) -> str:
    channel = _clean_preset_text(
        detector_preset.get("channel"),
    )

    if channel and channel.lower() != "weighted":
        return channel

    preset_name = _clean_preset_text(
        detector_preset.get("name"),
    ).lower()

    if "side" in preset_name:
        return "Side"

    if "forward" in preset_name:
        return "Forward"

    if channel:
        return channel

    return "Detector"


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


def load_detector_configuration_preset_catalog() -> list[dict[str, str]]:
    """
    Load the normalized detector preset catalog.
    """
    return get_default_detector_preset_loader().load_preset_catalog()


def load_detector_configuration_brand_options() -> list[dict[str, str]]:
    """
    Load detector preset brand options from JSON files.
    """
    return get_default_detector_preset_loader().load_brand_options()


def load_detector_configuration_model_options(
    brand: Any,
) -> list[dict[str, str]]:
    """
    Load detector preset model options for one brand.
    """
    return get_default_detector_preset_loader().load_model_options(
        brand,
    )


def load_detector_configuration_type_options(
    *,
    brand: Any,
    model: Any,
) -> list[dict[str, str]]:
    """
    Load detector type options for one brand/model pair.
    """
    return get_default_detector_preset_loader().load_type_options(
        brand=brand,
        model=model,
    )


def resolve_detector_configuration_preset_brand(
    preset_name: Any,
) -> str | None:
    """
    Resolve the brand label for one detector preset name.
    """
    return get_default_detector_preset_loader().resolve_preset_brand(
        preset_name,
    )


def resolve_detector_configuration_preset_model(
    preset_name: Any,
) -> str | None:
    """
    Resolve the model label for one detector preset name.
    """
    return get_default_detector_preset_loader().resolve_preset_model(
        preset_name,
    )


def load_detector_configuration_preset(
    preset_name: Any,
) -> dict[str, Any]:
    """
    Load one detector preset by name from disk.

    Returns an empty dict if the preset does not exist.
    """
    return get_default_detector_preset_loader().load_preset(preset_name)
