# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any, Optional
import json
import logging
import re

import numpy as np

from RosettaX.utils.fcs_metadata import FCSMetadata
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig

from .loader import get_default_detector_preset_loader


logger = logging.getLogger(__name__)
_DETECTOR_PRESET_LOADER = get_default_detector_preset_loader()
DETECTOR_AUTO_DETECT_RULES_PATH = Path(__file__).with_name(
    "detector_auto_detect_rules.json"
)


CUSTOM_DETECTOR_PRESET_NAME = "Generic detector"
CUSTOM_DETECTOR_DEFAULT_NUMERICAL_APERTURE = 0.2
CUSTOM_DETECTOR_DEFAULT_CACHE_NUMERICAL_APERTURE = 0.0
CUSTOM_DETECTOR_DEFAULT_BLOCKER_BAR_NUMERICAL_APERTURE = 0.0
CUSTOM_DETECTOR_DEFAULT_SAMPLING = 600
CUSTOM_DETECTOR_DEFAULT_PHI_ANGLE_DEGREE = 0.0
CUSTOM_DETECTOR_DEFAULT_GAMMA_ANGLE_DEGREE = 0.0

COMMON_LASER_WAVELENGTHS_NM: tuple[int, ...] = (
    355,
    375,
    405,
    407,
    440,
    445,
    457,
    473,
    488,
    505,
    514,
    532,
    561,
    594,
    633,
    635,
    637,
    638,
    640,
    655,
    660,
    685,
    730,
    780,
    808,
)

_LASER_WAVELENGTH_PATTERN = re.compile(
    r"(?<!\d)(%s)(?!\d)" % "|".join(str(value) for value in COMMON_LASER_WAVELENGTHS_NM)
)

SSC_FAMILY_ALIASES: tuple[str, ...] = (
    "vssc",
    "ssc",
    "sidescatter",
    "sidescattering",
    "sidescattered",
    "side",
    "lals",
    "lasl",
    "mals",
    "largeanglelightscatter",
    "mediumanglelightscatter",
    "anglelightscatter",
    "405ls",
    "488ls",
    "561ls",
    "638ls",
    "uvls",
    "vls",
    "bls",
)

FSC_FAMILY_ALIASES: tuple[str, ...] = (
    "fsc",
    "forwardscatter",
    "forwardscattering",
    "forward",
    "smallangle",
    "sals",
    "smallanglelightscatter",
)

FLUORESCENCE_FAMILY_ALIASES: tuple[str, ...] = (
    "fluorescence",
    "fluor",
    "fl",
)


def build_detector_preset_options() -> list[dict[str, str]]:
    """
    Build detector preset dropdown options from disk.

    JSON files are read every time this function is called, so preset edits are
    """
    preset_options = [
        option
        for option in _DETECTOR_PRESET_LOADER.load_preset_options()
        if option["value"] != CUSTOM_DETECTOR_PRESET_NAME
    ]

    return [
        {
            "label": CUSTOM_DETECTOR_PRESET_NAME,
            "value": CUSTOM_DETECTOR_PRESET_NAME,
        },
        *preset_options,
    ]


def resolve_runtime_detector_preset(
    preset_name: Any,
    *,
    runtime_config_data: Any = None,
    uploaded_fcs_path: Any = None,
    detector_selection_runtime_config_path: Optional[str] = None,
) -> Optional[str]:
    """
    Resolve one persisted detector preset name to a known preset.

    Empty values stay empty so the UI can initialize with no preset selected.
    """
    allowed_preset_names = {
        str(option.get("value"))
        for option in build_detector_preset_options()
        if isinstance(option, dict) and option.get("value") is not None
    }

    preset_name_string = clean_optional_string(
        preset_name,
    )

    if not preset_name_string:
        return None

    if preset_name_string in allowed_preset_names:
        return preset_name_string

    return None


def detect_detector_preset_from_uploaded_fcs(
    *,
    uploaded_fcs_path: Any,
    selected_detector_channel: Any,
) -> Optional[str]:
    """
    Detect one detector preset from uploaded FCS metadata and the selected peak detector.

    Detection requires the currently selected peak detector channel. Preset
    aliases from the detector catalog are scored first, then the remaining
    preset metadata heuristic runs.
    """
    uploaded_fcs_path_string = clean_optional_string(
        uploaded_fcs_path,
    )
    selected_detector_channel_string = clean_optional_string(
        selected_detector_channel,
    )

    if not uploaded_fcs_path_string or not selected_detector_channel_string:
        return None

    try:
        with FCSFile(uploaded_fcs_path_string) as fcs_file:
            metadata = fcs_file.get_metadata()
    except Exception:
        logger.exception(
            "Failed to detect detector preset from uploaded_fcs_path=%r",
            uploaded_fcs_path_string,
        )
        return None

    return infer_detector_preset_from_metadata(
        metadata=metadata,
        selected_detector_channel=selected_detector_channel_string,
    )


def detector_preset_is_empty(preset_name: Any) -> bool:
    """
    Return True when no detector preset is selected.
    """
    return not clean_optional_string(
        preset_name,
    )


def detector_preset_is_custom(preset_name: Any) -> bool:
    """
    Return True when the selected detector preset corresponds to editable custom values.
    """
    preset_name_string = clean_optional_string(
        preset_name,
    )

    return preset_name_string == CUSTOM_DETECTOR_PRESET_NAME


def clean_optional_string(value: Any) -> str:
    """
    Normalize one optional string.
    """
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def detect_wavelength_nm_from_detector_channel(
    detector_channel: Any,
) -> Optional[int]:
    """
    Infer one laser wavelength from a detector/channel name when it is explicit.

    Examples include names such as ``405SALS(Area)`` or ``488 FSC-A``.
    Ambiguous names like ``SSC-A`` or ``FL1-A`` return ``None``.
    """
    detector_channel_string = clean_optional_string(
        detector_channel,
    )

    if not detector_channel_string:
        return None

    match = _LASER_WAVELENGTH_PATTERN.search(
        detector_channel_string,
    )

    if match is None:
        return None

    return int(
        match.group(1),
    )


def normalize_lookup_token(value: Any) -> str:
    """
    Normalize one free-text token for case-insensitive lookup.
    """
    return "".join(
        character.lower()
        for character in clean_optional_string(value)
        if character.isalnum()
    )


def tokenize_lookup_text(value: Any) -> set[str]:
    """
    Split free text into normalized alphanumeric tokens.
    """
    raw_value = clean_optional_string(value)

    if not raw_value:
        return set()

    token_characters: list[str] = []
    tokens: set[str] = set()

    for character in raw_value.lower():
        if character.isalnum():
            token_characters.append(character)
            continue

        if token_characters:
            tokens.add("".join(token_characters))
            token_characters = []

    if token_characters:
        tokens.add("".join(token_characters))

    return tokens


def infer_detector_preset_from_metadata(
    *,
    metadata: Optional[FCSMetadata],
    selected_detector_channel: Any,
) -> Optional[str]:
    """
    Heuristically infer one detector preset from the instrument name and selected channel.
    """
    instrument_name = extract_instrument_name_from_metadata(
        metadata=metadata,
    )
    selected_detector_channel_string = clean_optional_string(
        selected_detector_channel,
    )

    if not instrument_name or not selected_detector_channel_string:
        return None

    best_preset_name: Optional[str] = None
    best_score = 0

    for preset in _DETECTOR_PRESET_LOADER.load_presets().values():
        preset_score = score_detector_preset_match(
            instrument_name=instrument_name,
            preset=preset,
            selected_detector_channel=selected_detector_channel_string,
        )

        if preset_score <= best_score:
            continue

        best_score = preset_score
        best_preset_name = clean_optional_string(
            preset.get("name"),
        )

    logger.debug(
        "Heuristic detector preset inference instrument_name=%r best_preset_name=%r best_score=%r",
        instrument_name,
        best_preset_name,
        best_score,
    )

    return best_preset_name


def score_detector_preset_match(
    *,
    instrument_name: str,
    preset: dict[str, Any],
    selected_detector_channel: Any,
) -> int:
    """
    Score how strongly one detector preset matches the instrument name and selected channel.
    """
    normalized_instrument_name = normalize_lookup_token(
        instrument_name,
    )
    instrument_tokens = tokenize_lookup_text(
        instrument_name,
    )

    if not preset_matches_selected_detector_channel(
        preset=preset,
        selected_detector_channel=selected_detector_channel,
    ):
        return 0

    alias_score = _score_detector_preset_alias_match(
        instrument_name=instrument_name,
        preset=preset,
    )

    if alias_score > 0:
        score = alias_score
    else:
        score = 0

    field_weights = (
        ("instrument", 120),
        ("name", 100),
        ("manufacturer", 40),
    )

    for field_name, field_weight in field_weights:
        field_value = clean_optional_string(
            preset.get(field_name),
        )
        normalized_field_value = normalize_lookup_token(
            field_value,
        )

        if not normalized_field_value:
            continue

        if normalized_field_value == normalized_instrument_name:
            score = max(score, field_weight + 40)
            continue

        if (
            normalized_field_value in normalized_instrument_name
            or normalized_instrument_name in normalized_field_value
        ):
            score = max(score, field_weight + 20)
            continue

        shared_tokens = instrument_tokens & tokenize_lookup_text(field_value)

        if shared_tokens:
            score = max(score, field_weight + (10 * len(shared_tokens)))

    if score == 0:
        return 0

    channel_name = normalize_lookup_token(
        preset.get("channel"),
    )

    if any(token in channel_name for token in ("ssc", "scatter", "side")):
        score += 30
    elif any(token in channel_name for token in ("fsc", "forward")):
        score += 10

    if any(token in channel_name for token in ("fluorescence", "fl")):
        score -= 40

    selected_channel_family = classify_detector_channel_family(
        selected_detector_channel,
    )
    preset_channel_family = classify_detector_preset_family(
        preset,
    )

    if selected_channel_family and selected_channel_family == preset_channel_family:
        score += 80

    return score


def _score_detector_preset_alias_match(
    *,
    instrument_name: str,
    preset: dict[str, Any],
) -> int:
    normalized_instrument_name = normalize_lookup_token(
        instrument_name,
    )
    instrument_tokens = tokenize_lookup_text(
        instrument_name,
    )
    best_score = 0

    for alias_value in _iter_detector_preset_aliases(
        preset,
    ):
        normalized_alias = normalize_lookup_token(
            alias_value,
        )

        if not normalized_alias:
            continue

        if normalized_alias == normalized_instrument_name:
            best_score = max(best_score, 260)
            continue

        if (
            normalized_alias in normalized_instrument_name
            or normalized_instrument_name in normalized_alias
        ):
            best_score = max(best_score, 220)
            continue

        shared_tokens = instrument_tokens & tokenize_lookup_text(alias_value)

        if shared_tokens:
            best_score = max(best_score, 180 + (10 * len(shared_tokens)))

    return best_score


def _iter_detector_preset_aliases(
    preset: dict[str, Any],
) -> tuple[str, ...]:
    raw_aliases = preset.get("alias")

    if raw_aliases in (None, ""):
        return ()

    if isinstance(raw_aliases, str):
        alias_values = [raw_aliases]
    elif isinstance(raw_aliases, (list, tuple, set)):
        alias_values = list(raw_aliases)
    else:
        return ()

    normalized_aliases: list[str] = []

    for alias_value in alias_values:
        cleaned_alias = clean_optional_string(alias_value)

        if cleaned_alias and cleaned_alias not in normalized_aliases:
            normalized_aliases.append(cleaned_alias)

    return tuple(normalized_aliases)


def classify_detector_channel_family(value: Any) -> str:
    """
    Classify one detector/channel string into a coarse family.
    """
    normalized_value = normalize_lookup_token(
        value,
    )

    if not normalized_value:
        return ""

    if any(token in normalized_value for token in SSC_FAMILY_ALIASES):
        return "ssc"

    if any(token in normalized_value for token in FSC_FAMILY_ALIASES):
        return "fsc"

    if any(token in normalized_value for token in FLUORESCENCE_FAMILY_ALIASES):
        return "fl"

    if normalized_value.endswith("als"):
        return "ssc"

    return ""


def classify_detector_preset_family(preset: dict[str, Any]) -> str:
    """
    Classify one detector preset into a coarse family.

    Some presets use a generic channel label like "Weighted" and keep the useful
    forward/side distinction only in the preset name.
    """
    if not isinstance(preset, dict):
        return ""

    for candidate_value in (
        preset.get("channel"),
        preset.get("name"),
        preset.get("description"),
    ):
        family = classify_detector_channel_family(
            candidate_value,
        )

        if family:
            return family

    return ""


def preset_matches_selected_detector_channel(
    *,
    preset: dict[str, Any],
    selected_detector_channel: Any,
) -> bool:
    """
    Return True when one preset family matches the selected peak detector channel.
    """
    selected_channel_family = classify_detector_channel_family(
        selected_detector_channel,
    )

    if not selected_channel_family:
        return False

    preset_channel_family = classify_detector_preset_family(
        preset,
    )

    return bool(preset_channel_family and preset_channel_family == selected_channel_family)


def resolve_detector_auto_detect_rule(
    *,
    metadata: Optional[FCSMetadata],
) -> Optional[dict[str, Any]]:
    """
    Resolve one detector auto-detect rule from FCS instrument metadata.
    """
    instrument_name = extract_instrument_name_from_metadata(
        metadata=metadata,
    )

    if not instrument_name:
        return None

    normalized_instrument_name = normalize_lookup_token(
        instrument_name,
    )

    for rule in load_detector_auto_detect_rules():
        for instrument_alias in rule.get("instrument_aliases", []):
            normalized_alias = normalize_lookup_token(
                instrument_alias,
            )

            if not normalized_alias:
                continue

            if (
                normalized_alias == normalized_instrument_name
                or normalized_alias in normalized_instrument_name
                or normalized_instrument_name in normalized_alias
            ):
                return rule

    return None


def resolve_rule_based_detector_preset(
    *,
    matched_rule: Optional[dict[str, Any]],
    selected_detector_channel: Any,
) -> Optional[str]:
    """
    Resolve one explicit detector preset from a matched instrument rule.
    """
    if not matched_rule:
        return None

    detector_preset_name = clean_optional_string(
        matched_rule.get("detector_preset"),
    )

    if not detector_preset_name:
        return None

    allowed_preset_names = {
        str(option.get("value"))
        for option in build_detector_preset_options()
        if isinstance(option, dict) and option.get("value") is not None
    }

    if detector_preset_name in allowed_preset_names:
        preset = _DETECTOR_PRESET_LOADER.load_preset(
            detector_preset_name,
        )

        if preset_matches_selected_detector_channel(
            preset=preset,
            selected_detector_channel=selected_detector_channel,
        ):
            return detector_preset_name

    return None


def load_detector_auto_detect_rules() -> list[dict[str, Any]]:
    """
    Load detector auto-detect rules from the shared JSON file.
    """
    if not DETECTOR_AUTO_DETECT_RULES_PATH.exists():
        return []

    try:
        raw_payload = json.loads(
            DETECTOR_AUTO_DETECT_RULES_PATH.read_text(encoding="utf-8")
        )
    except Exception:
        logger.exception(
            "Failed to load detector auto-detect rules from %s",
            DETECTOR_AUTO_DETECT_RULES_PATH,
        )
        return []

    raw_rules = raw_payload.get("rules") if isinstance(raw_payload, dict) else None

    if not isinstance(raw_rules, list):
        return []

    normalized_rules: list[dict[str, Any]] = []

    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue

        instrument_aliases = raw_rule.get("instrument_aliases")

        if not isinstance(instrument_aliases, list):
            continue

        detector_channels = raw_rule.get("detector_channels")

        normalized_rules.append(
            {
                "name": clean_optional_string(raw_rule.get("name")) or "Unnamed detector rule",
                "instrument_aliases": [
                    clean_optional_string(instrument_alias)
                    for instrument_alias in instrument_aliases
                    if clean_optional_string(instrument_alias)
                ],
                "detector_preset": clean_optional_string(raw_rule.get("detector_preset")),
                "detector_channels": detector_channels if isinstance(detector_channels, dict) else {},
            }
        )

    return normalized_rules


def extract_instrument_name_from_metadata(
    *,
    metadata: Optional[FCSMetadata],
) -> str:
    """
    Extract one instrument or system name from FCS metadata.
    """
    if metadata is None:
        return ""

    keyword_lookup = {
        str(key).strip().lower(): value
        for key, value in metadata.keywords.items()
    }

    preferred_keys = (
        "$cyt",
        "cyt",
        "$inst",
        "instrument",
        "instrument name",
        "system",
        "machine",
        "$src",
    )

    for preferred_key in preferred_keys:
        instrument_name = clean_optional_string(
            keyword_lookup.get(preferred_key),
        )

        if instrument_name:
            return instrument_name

    for keyword_name, keyword_value in keyword_lookup.items():
        if any(
            token in keyword_name
            for token in ("cyt", "instrument", "system", "machine")
        ):
            instrument_name = clean_optional_string(
                keyword_value,
            )

            if instrument_name:
                return instrument_name

    return ""


def resolve_detector_configuration_visibility_style(
    *,
    preset_name: Any,
) -> dict[str, str]:
    """
    Resolve the visibility style for the manual detector configuration block.
    """
    if detector_preset_is_custom(preset_name):
        return {"display": "block"}

    return {"display": "none"}


def resolve_detector_configuration_values(
    *,
    preset_name: Any,
    current_detector_numerical_aperture: Any,
    current_detector_cache_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
    current_detector_sampling: Any,
    current_detector_phi_angle_degree: Any,
    current_detector_gamma_angle_degree: Any,
) -> tuple[Any, Any, Any, Any, Any, Any]:
    """
    Resolve detector values from either editable fields or a JSON backed preset.

    detector_cache_numerical_aperture and blocker_bar_numerical_aperture are
    separate physical/configuration parameters and must not be aliased.
    """
    current_values = (
        current_detector_numerical_aperture,
        current_detector_cache_numerical_aperture,
        current_blocker_bar_numerical_aperture,
        current_detector_sampling,
        current_detector_phi_angle_degree,
        current_detector_gamma_angle_degree,
    )

    if detector_preset_is_empty(preset_name):
        logger.debug(
            "Resolved empty detector preset values for preset_name=%r values=%r",
            preset_name,
            (None, None, None, None, None, None),
        )

        return (None, None, None, None, None, None)

    if detector_preset_is_custom(preset_name):
        resolved_custom_values = (
            _coalesce_custom_detector_value(
                current_detector_numerical_aperture,
                CUSTOM_DETECTOR_DEFAULT_NUMERICAL_APERTURE,
            ),
            _coalesce_custom_detector_value(
                current_detector_cache_numerical_aperture,
                CUSTOM_DETECTOR_DEFAULT_CACHE_NUMERICAL_APERTURE,
            ),
            _coalesce_custom_detector_value(
                current_blocker_bar_numerical_aperture,
                CUSTOM_DETECTOR_DEFAULT_BLOCKER_BAR_NUMERICAL_APERTURE,
            ),
            _coalesce_custom_detector_value(
                current_detector_sampling,
                CUSTOM_DETECTOR_DEFAULT_SAMPLING,
            ),
            _coalesce_custom_detector_value(
                current_detector_phi_angle_degree,
                CUSTOM_DETECTOR_DEFAULT_PHI_ANGLE_DEGREE,
            ),
            _coalesce_custom_detector_value(
                current_detector_gamma_angle_degree,
                CUSTOM_DETECTOR_DEFAULT_GAMMA_ANGLE_DEGREE,
            ),
        )

        logger.debug(
            "Resolved custom detector preset values for preset_name=%r values=%r",
            preset_name,
            resolved_custom_values,
        )

        return resolved_custom_values

    preset = _DETECTOR_PRESET_LOADER.load_preset(
        preset_name,
    )

    resolved_values = (
        _resolve_preset_value(
            preset=preset,
            key="detector_numerical_aperture",
            fallback=current_detector_numerical_aperture,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_cache_numerical_aperture",
            fallback=current_detector_cache_numerical_aperture,
        ),
        _resolve_preset_value(
            preset=preset,
            key="blocker_bar_numerical_aperture",
            fallback=current_blocker_bar_numerical_aperture,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_sampling",
            fallback=current_detector_sampling,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_phi_angle_degree",
            fallback=current_detector_phi_angle_degree,
        ),
        _resolve_preset_value(
            preset=preset,
            key="detector_gamma_angle_degree",
            fallback=current_detector_gamma_angle_degree,
        ),
    )

    logger.debug(
        "Resolved detector preset values for preset_name=%r values=%r preset=%r",
        preset_name,
        resolved_values,
        preset,
    )

    return resolved_values


def resolve_detector_preset_wavelength_nm(
    *,
    preset_name: Any,
    current_wavelength_nm: Any = None,
    fallback_wavelength_nm: Any = None,
) -> Any:
    """
    Resolve the wavelength owned by one detector preset.

    Empty or custom presets keep the current wavelength so the user can edit it
    manually when no fixed preset wavelength should apply.
    """
    resolved_current_wavelength_nm = current_wavelength_nm

    if resolved_current_wavelength_nm is None:
        resolved_current_wavelength_nm = fallback_wavelength_nm

    if detector_preset_is_empty(preset_name) or detector_preset_is_custom(preset_name):
        return resolved_current_wavelength_nm

    preset = _DETECTOR_PRESET_LOADER.load_preset(
        preset_name,
    )

    return _resolve_preset_value(
        preset=preset,
        key="wavelength_nm",
        fallback=resolved_current_wavelength_nm,
    )


def resolve_detector_modeling_geometry_values(
    *,
    preset_name: Any,
    current_detector_cache_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
) -> tuple[Any, Any]:
    """
    Resolve the geometry values that should be passed into modeling calls.

    Preset-driven detector weights can encode detector cache and blocker-bar
    geometry directly. When that happens, the scalar geometry values passed to
    PyMieSim and the preview are neutralized to avoid double-applying the mask.
    """
    if detector_preset_is_custom(preset_name):
        resolved_detector_cache_numerical_aperture = (
            _coerce_optional_float(
                current_detector_cache_numerical_aperture,
            )
            or 0.0
        )
        resolved_blocker_bar_numerical_aperture = (
            _coerce_optional_float(
                current_blocker_bar_numerical_aperture,
            )
            or 0.0
        )

        if (
            resolved_detector_cache_numerical_aperture > 0.0
            or resolved_blocker_bar_numerical_aperture > 0.0
        ):
            return 0.0, 0.0

        return (
            resolved_detector_cache_numerical_aperture,
            resolved_blocker_bar_numerical_aperture,
        )

    preset = _DETECTOR_PRESET_LOADER.load_preset(
        preset_name,
    )

    if not preset or not _preset_uses_weighted_detector_geometry(preset):
        return (
            current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture,
        )

    return 0.0, 0.0


def _coalesce_custom_detector_value(
    current_value: Any,
    default_value: Any,
) -> Any:
    """
    Fill missing custom detector fields with the standard generic defaults.
    """
    if current_value in (None, ""):
        return default_value

    return current_value


def _coerce_optional_float(
    value: Any,
) -> float | None:
    """
    Convert a candidate detector geometry value to float when possible.
    """
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def resolve_detector_angular_weights(
    *,
    preset_name: Any,
    detector_sampling: Any,
    current_detector_numerical_aperture: Any = None,
    current_detector_cache_numerical_aperture: Any = None,
    current_blocker_bar_numerical_aperture: Any = None,
    current_detector_phi_angle_degree: Any = None,
    current_detector_gamma_angle_degree: Any = None,
    current_medium_refractive_index: Any = None,
    current_detector_angular_weighting: Any = None,
) -> np.ndarray | None:
    """
    Resolve optional angular weights for a detector preset.

        Supported preset fields are:

        - ``detector_angular_weights``: explicit complex-valued vector
        - ``detector_cache_numerical_aperture`` and
            ``blocker_bar_numerical_aperture``: radial geometry masks
        - ``detector_angular_weight_profile``: named ad hoc generator
    """
    def resolve_sampling_size(preset: Optional[dict[str, Any]] = None) -> int | None:
        for candidate_value in (
            detector_sampling,
            None if preset is None else preset.get("detector_sampling"),
        ):
            try:
                resolved_sampling_size = int(candidate_value)
            except (TypeError, ValueError):
                continue

            if resolved_sampling_size > 0:
                return resolved_sampling_size

        return None

    if detector_preset_is_custom(preset_name):
        preset = _build_custom_geometry_preset(
            current_detector_numerical_aperture=current_detector_numerical_aperture,
            current_detector_cache_numerical_aperture=current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
            current_detector_phi_angle_degree=current_detector_phi_angle_degree,
            current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
            current_medium_refractive_index=current_medium_refractive_index,
            current_detector_angular_weighting=current_detector_angular_weighting,
        )

        if preset is None:
            return None
    else:
        preset = _DETECTOR_PRESET_LOADER.load_preset(
            preset_name,
        )

        if not preset:
            return None

    sampling_size = resolve_sampling_size(
        preset,
    )

    if sampling_size is None:
        logger.debug(
            "Resolved no detector angular weights because detector_sampling is missing for preset_name=%r",
            preset_name,
        )
        return None

    geometry_angular_weights = _build_geometry_angular_weights(
        preset=preset,
        sampling_size=sampling_size,
    )
    explicit_weights = preset.get("detector_angular_weights")

    if explicit_weights is not None:
        angular_weights = np.asarray(
            explicit_weights,
            dtype=np.complex128,
        ).reshape(-1)

        if angular_weights.size != sampling_size:
            raise ValueError(
                "Preset detector_angular_weights length must match detector_sampling. "
                f"Got {angular_weights.size} weights for sampling={sampling_size}."
            )

        return _combine_detector_angular_weights(
            geometry_angular_weights,
            angular_weights,
        )

    angular_weighting = preset.get("detector_angular_weighting")

    if isinstance(angular_weighting, dict):
        return _combine_detector_angular_weights(
            geometry_angular_weights,
            _resolve_detector_angular_weighting(
                preset=preset,
                angular_weighting=angular_weighting,
                sampling_size=sampling_size,
            ),
        )

    profile_name = preset.get("detector_angular_weight_profile")

    if profile_name in (None, ""):
        return geometry_angular_weights

    raise ValueError(
        f"Unsupported detector_angular_weight_profile: {profile_name!r}"
    )


def _combine_detector_angular_weights(
    geometry_angular_weights: np.ndarray | None,
    configured_angular_weights: np.ndarray | None,
) -> np.ndarray | None:
    if geometry_angular_weights is None:
        return configured_angular_weights

    if configured_angular_weights is None:
        return geometry_angular_weights

    return np.asarray(
        geometry_angular_weights,
        dtype=np.complex128,
    ) * np.asarray(
        configured_angular_weights,
        dtype=np.complex128,
    )


def _build_custom_geometry_preset(
    *,
    current_detector_numerical_aperture: Any,
    current_detector_cache_numerical_aperture: Any,
    current_blocker_bar_numerical_aperture: Any,
    current_detector_phi_angle_degree: Any,
    current_detector_gamma_angle_degree: Any,
    current_medium_refractive_index: Any,
    current_detector_angular_weighting: Any = None,
) -> dict[str, Any] | None:
    detector_angular_weighting = _parse_custom_detector_angular_weighting(
        current_detector_angular_weighting,
    )
    detector_cache_numerical_aperture = float(
        current_detector_cache_numerical_aperture or 0.0,
    )
    blocker_bar_numerical_aperture = float(
        current_blocker_bar_numerical_aperture or 0.0,
    )

    if (
        detector_cache_numerical_aperture <= 0.0
        and blocker_bar_numerical_aperture <= 0.0
        and detector_angular_weighting is None
    ):
        return None

    custom_preset = {
        "name": CUSTOM_DETECTOR_PRESET_NAME,
        "detector_numerical_aperture": float(
            current_detector_numerical_aperture or 0.0,
        ),
        "detector_cache_numerical_aperture": detector_cache_numerical_aperture,
        "blocker_bar_numerical_aperture": blocker_bar_numerical_aperture,
        "detector_phi_angle_degree": float(
            current_detector_phi_angle_degree or 0.0,
        ),
        "detector_gamma_angle_degree": float(
            current_detector_gamma_angle_degree or 0.0,
        ),
        "medium_refractive_index": float(
            current_medium_refractive_index or 1.333,
        ),
    }

    if detector_angular_weighting is not None:
        custom_preset["detector_angular_weighting"] = detector_angular_weighting

    return custom_preset


def _parse_custom_detector_angular_weighting(
    current_detector_angular_weighting: Any,
) -> dict[str, Any] | None:
    if current_detector_angular_weighting in (None, ""):
        return None

    if isinstance(current_detector_angular_weighting, dict):
        return dict(current_detector_angular_weighting)

    try:
        parsed_payload = json.loads(str(current_detector_angular_weighting))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Custom detector angular weighting must be valid JSON."
        ) from exc

    if parsed_payload in (None, ""):
        return None

    if not isinstance(parsed_payload, dict):
        raise ValueError(
            "Custom detector angular weighting JSON must define an object."
        )

    return dict(parsed_payload)


def _build_geometry_angular_weights(
    *,
    preset: dict[str, Any],
    sampling_size: int,
) -> np.ndarray | None:
    detector_cache_numerical_aperture = float(
        preset.get(
            "detector_cache_numerical_aperture",
            0.0,
        )
    )
    blocker_bar_numerical_aperture = float(
        preset.get(
            "blocker_bar_numerical_aperture",
            0.0,
        )
    )

    if detector_cache_numerical_aperture <= 0.0 and blocker_bar_numerical_aperture <= 0.0:
        return None

    coordinate_array = _build_profile_coordinate_array(
        preset=preset,
        sampling_size=sampling_size,
    )
    local_numerical_aperture = _build_local_numerical_aperture(
        preset=preset,
        coordinate_array=coordinate_array,
    )
    visible_mask = np.ones(
        sampling_size,
        dtype=bool,
    )

    if detector_cache_numerical_aperture > 0.0:
        visible_mask &= (
            _build_detector_cache_numerical_aperture(
                preset=preset,
                coordinate_array=coordinate_array,
            ) >= detector_cache_numerical_aperture
        )

    if blocker_bar_numerical_aperture > 0.0:
        visible_mask &= (
            _build_blocker_bar_numerical_aperture(
                preset=preset,
                coordinate_array=coordinate_array,
            ) >= blocker_bar_numerical_aperture
        )

    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )
    angular_weights[visible_mask] = 1.0
    return angular_weights


def _build_local_numerical_aperture(
    *,
    preset: dict[str, Any],
    coordinate_array: np.ndarray,
) -> np.ndarray:
    return _build_detector_cache_numerical_aperture(
        preset=preset,
        coordinate_array=coordinate_array,
    )


def _build_detector_cache_numerical_aperture(
    *,
    preset: dict[str, Any],
    coordinate_array: np.ndarray,
) -> np.ndarray:
    medium_refractive_index = float(
        preset.get(
            "medium_refractive_index",
            1.333,
        )
    )
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, first_transverse_projection, second_transverse_projection = _project_coordinates_to_local_detector_frame(
        normalized_coordinate_array,
    )
    radial_coordinate = np.sqrt(
        first_transverse_projection ** 2
        + second_transverse_projection ** 2
    )
    return medium_refractive_index * radial_coordinate


def _build_blocker_bar_numerical_aperture(
    *,
    preset: dict[str, Any],
    coordinate_array: np.ndarray,
) -> np.ndarray:
    medium_refractive_index = float(
        preset.get(
            "medium_refractive_index",
            1.333,
        )
    )
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, blocker_axis_projection, _ = _project_coordinates_to_local_detector_frame(
        normalized_coordinate_array,
    )
    return medium_refractive_index * np.abs(blocker_axis_projection)


def _project_coordinates_to_local_detector_frame(
    normalized_coordinate_array: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    detector_axis_vector, first_transverse_axis, second_transverse_axis = _build_local_detector_basis(
        normalized_coordinate_array,
    )

    return (
        normalized_coordinate_array @ detector_axis_vector,
        normalized_coordinate_array @ first_transverse_axis,
        normalized_coordinate_array @ second_transverse_axis,
    )


def _build_local_detector_basis(
    normalized_coordinate_array: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    detector_axis_vector = np.asarray(
        normalized_coordinate_array.mean(axis=0),
        dtype=float,
    )
    detector_axis_norm = np.linalg.norm(detector_axis_vector)

    if detector_axis_norm == 0.0:
        raise ValueError("Cannot build a detector-local basis from a zero-length axis vector.")

    detector_axis_vector = detector_axis_vector / detector_axis_norm

    reference_vector = np.array([0.0, 0.0, 1.0], dtype=float)

    if abs(float(np.dot(detector_axis_vector, reference_vector))) > 0.99:
        reference_vector = np.array([1.0, 0.0, 0.0], dtype=float)

    first_transverse_axis = np.cross(reference_vector, detector_axis_vector)
    first_transverse_axis_norm = np.linalg.norm(first_transverse_axis)

    if first_transverse_axis_norm == 0.0:
        raise ValueError("Cannot build the first detector transverse axis for this detector orientation.")

    first_transverse_axis = first_transverse_axis / first_transverse_axis_norm
    second_transverse_axis = np.cross(detector_axis_vector, first_transverse_axis)
    second_transverse_axis_norm = np.linalg.norm(second_transverse_axis)

    if second_transverse_axis_norm == 0.0:
        raise ValueError("Cannot build the second detector transverse axis for this detector orientation.")

    second_transverse_axis = second_transverse_axis / second_transverse_axis_norm

    return detector_axis_vector, first_transverse_axis, second_transverse_axis


def _normalize_coordinate_array(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    coordinate_array = np.asarray(
        coordinate_array,
        dtype=float,
    )
    coordinate_norms = np.linalg.norm(
        coordinate_array,
        axis=1,
    )

    if np.any(coordinate_norms <= 0.0):
        raise ValueError("Detector mesh coordinates contain a zero-length vector.")

    return coordinate_array / coordinate_norms[:, None]


def _preset_uses_weighted_detector_geometry(
    preset: dict[str, Any],
) -> bool:
    if float(preset.get("detector_cache_numerical_aperture", 0.0)) > 0.0:
        return True

    if float(preset.get("blocker_bar_numerical_aperture", 0.0)) > 0.0:
        return True

    if preset.get("detector_angular_weights") is not None:
        return True

    if isinstance(preset.get("detector_angular_weighting"), dict):
        return True

    return preset.get("detector_angular_weight_profile") not in (None, "")


def _resolve_detector_angular_weighting(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray | None:
    weighting_mode = str(angular_weighting.get("mode", "")).strip().lower()

    if not weighting_mode:
        return None

    if weighting_mode == "split":
        return _resolve_split_angular_weighting(
            preset=preset,
            angular_weighting=angular_weighting,
            sampling_size=sampling_size,
        )

    if weighting_mode == "split-fraction":
        return _resolve_split_fraction_angular_weighting(
            preset=preset,
            angular_weighting=angular_weighting,
            sampling_size=sampling_size,
        )

    if weighting_mode in {
        "split-separation-angle",
        "split-fraction-angle",
    }:
        return _resolve_split_separation_angle_angular_weighting(
            preset=preset,
            angular_weighting=angular_weighting,
            sampling_size=sampling_size,
        )

    if weighting_mode == "index-split":
        return _resolve_index_split_angular_weighting(
            angular_weighting=angular_weighting,
            sampling_size=sampling_size,
        )

    if weighting_mode == "explicit":
        explicit_weights = angular_weighting.get("weights")
        angular_weights = np.asarray(
            explicit_weights,
            dtype=np.complex128,
        ).reshape(-1)

        if angular_weights.size != sampling_size:
            raise ValueError(
                "detector_angular_weighting weights length must match detector_sampling. "
                f"Got {angular_weights.size} weights for sampling={sampling_size}."
            )

        return angular_weights

    raise ValueError(
        f"Unsupported detector_angular_weighting mode: {angular_weighting.get('mode')!r}"
    )


def _resolve_split_angular_weighting(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    split_metric = _build_split_metric(
        preset=preset,
        angular_weighting=angular_weighting,
        sampling_size=sampling_size,
    )
    keep_side = str(angular_weighting.get("keep", "positive")).strip().lower()
    keep_mask_builders = {
        "positive": split_metric > 0.0,
        "negative": split_metric < 0.0,
        "nonpositive": split_metric <= 0.0,
        "nonnegative": split_metric >= 0.0,
    }

    if keep_side not in keep_mask_builders:
        raise ValueError(
            f"Unsupported detector split keep side: {angular_weighting.get('keep')!r}"
        )

    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )
    angular_weights[keep_mask_builders[keep_side]] = 1.0
    return angular_weights


def _resolve_index_split_angular_weighting(
    *,
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    keep_side = str(angular_weighting.get("keep", "second-half")).strip().lower()
    split_index = int(angular_weighting.get("split_index", sampling_size // 2))

    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )

    if keep_side == "second-half":
        angular_weights[split_index:] = 1.0
        return angular_weights

    if keep_side == "first-half":
        angular_weights[:split_index] = 1.0
        return angular_weights

    raise ValueError(
        f"Unsupported detector index split keep side: {angular_weighting.get('keep')!r}"
    )


def _resolve_split_fraction_angular_weighting(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    split_metric = _build_split_metric(
        preset=preset,
        angular_weighting=angular_weighting,
        sampling_size=sampling_size,
    )
    keep_side = str(angular_weighting.get("keep", "positive")).strip().lower()

    if keep_side not in {
        "positive",
        "negative",
        "nonpositive",
        "nonnegative",
    }:
        raise ValueError(
            f"Unsupported detector split-fraction keep side: {angular_weighting.get('keep')!r}"
        )

    try:
        keep_fraction = float(
            angular_weighting.get("fraction", 0.5),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "detector split-fraction fraction must be numeric."
        ) from exc

    if not 0.0 <= keep_fraction <= 1.0:
        raise ValueError(
            f"detector split-fraction fraction must be between 0 and 1. Got {keep_fraction!r}."
        )

    geometry_angular_weights = _build_geometry_angular_weights(
        preset=preset,
        sampling_size=sampling_size,
    )
    if geometry_angular_weights is None:
        eligible_mask = np.ones(
            sampling_size,
            dtype=bool,
        )
    else:
        eligible_mask = np.asarray(
            geometry_angular_weights,
            dtype=np.complex128,
        ) != 0.0

    eligible_indices = np.flatnonzero(
        eligible_mask,
    )
    angular_weights = np.zeros(
        sampling_size,
        dtype=np.complex128,
    )

    if eligible_indices.size == 0 or keep_fraction <= 0.0:
        return angular_weights

    keep_count = int(
        round(keep_fraction * eligible_indices.size),
    )
    keep_count = max(
        0,
        min(keep_count, int(eligible_indices.size)),
    )

    if keep_count == 0:
        return angular_weights

    ordered_indices = eligible_indices[
        np.argsort(
            split_metric[eligible_indices],
            kind="stable",
        )
    ]

    if keep_side in {"positive", "nonnegative"}:
        kept_indices = ordered_indices[-keep_count:]
    else:
        kept_indices = ordered_indices[:keep_count]

    angular_weights[kept_indices] = 1.0
    return angular_weights


def _resolve_split_separation_angle_angular_weighting(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    weighting_with_fraction = dict(angular_weighting)
    weighting_with_fraction["fraction"] = _resolve_split_separation_fraction(
        preset=preset,
        angular_weighting=angular_weighting,
    )

    return _resolve_split_fraction_angular_weighting(
        preset=preset,
        angular_weighting=weighting_with_fraction,
        sampling_size=sampling_size,
    )


def _resolve_split_separation_fraction(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
) -> float:
    separation_angle_value = angular_weighting.get("separation_angle_degree")

    if separation_angle_value in (None, ""):
        legacy_fraction_value = angular_weighting.get("fraction")

        if legacy_fraction_value in (None, ""):
            raise ValueError(
                "detector split-separation-angle requires separation_angle_degree or legacy fraction."
            )

        try:
            legacy_fraction = float(legacy_fraction_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "detector split-separation-angle legacy fraction must be numeric."
            ) from exc

        if not np.isfinite(legacy_fraction):
            raise ValueError(
                "detector split-separation-angle legacy fraction must be finite."
            )

        return float(
            np.clip(legacy_fraction, 0.0, 1.0),
        )

    try:
        detector_numerical_aperture = float(
            preset.get("detector_numerical_aperture", 0.0),
        )
        medium_refractive_index = float(
            preset.get("medium_refractive_index", 1.333),
        )
        detector_phi_angle_degree = float(
            preset.get("detector_phi_angle_degree", 0.0),
        )
        separation_angle_degree = float(
            separation_angle_value,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "detector split-separation-angle requires numeric detector_numerical_aperture, "
            "detector_phi_angle_degree, medium_refractive_index, and separation_angle_degree."
        ) from exc

    if medium_refractive_index <= 0.0:
        raise ValueError("detector split-separation-angle requires medium_refractive_index > 0.")

    normalized_aperture_ratio = detector_numerical_aperture / medium_refractive_index
    clamped_aperture_ratio = float(np.clip(normalized_aperture_ratio, -1.0, 1.0))
    detector_half_angle_degree = float(
        np.degrees(np.arcsin(clamped_aperture_ratio)),
    )

    minimum_detector_angle_degree = detector_phi_angle_degree - detector_half_angle_degree
    maximum_detector_angle_degree = detector_phi_angle_degree + detector_half_angle_degree
    detector_span_degree = maximum_detector_angle_degree - minimum_detector_angle_degree

    if detector_span_degree <= 0.0:
        raise ValueError(
            "detector split-separation-angle requires a positive detector angular span."
        )

    keep_side = str(angular_weighting.get("keep", "positive")).strip().lower()

    if keep_side in {"negative", "nonpositive"}:
        keep_fraction = (
            separation_angle_degree - minimum_detector_angle_degree
        ) / detector_span_degree
    elif keep_side in {"positive", "nonnegative"}:
        keep_fraction = (
            maximum_detector_angle_degree - separation_angle_degree
        ) / detector_span_degree
    else:
        raise ValueError(
            f"Unsupported detector split-separation-angle keep side: {angular_weighting.get('keep')!r}"
        )

    return float(
        np.clip(keep_fraction, 0.0, 1.0),
    )


def _build_split_metric(
    *,
    preset: dict[str, Any],
    angular_weighting: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    metric_name = str(angular_weighting.get("metric", "")).strip().lower()

    if metric_name == "mesh-x":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return coordinate_array[:, 0]

    if metric_name == "x-minus-z":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return coordinate_array[:, 0] - coordinate_array[:, 2]

    if metric_name == "local-plane":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return _build_local_split_metric(coordinate_array)

    if metric_name == "local-top-bottom":
        coordinate_array = _build_profile_coordinate_array(
            preset=preset,
            sampling_size=sampling_size,
        )
        return _build_local_top_bottom_split_metric(coordinate_array)

    raise ValueError(
        f"Unsupported detector split metric: {angular_weighting.get('metric')!r}"
    )


def _build_profile_coordinate_array(
    *,
    preset: dict[str, Any],
    sampling_size: int,
) -> np.ndarray:
    from ...pages.p03_scattering.sections.s03_model.optical_preview import (
        build_pymiesim_photodiode_mesh_coordinates,
    )

    detector_numerical_aperture = float(
        preset.get(
            "detector_numerical_aperture",
            0.4,
        )
    )
    detector_phi_angle_degree = float(
        preset.get(
            "detector_phi_angle_degree",
            0.0,
        )
    )
    detector_gamma_angle_degree = float(
        preset.get(
            "detector_gamma_angle_degree",
            0.0,
        )
    )
    medium_refractive_index = float(
        preset.get(
            "medium_refractive_index",
            1.333,
        )
    )

    coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
        detector_numerical_aperture=detector_numerical_aperture,
        medium_refractive_index=medium_refractive_index,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
        detector_sampling=sampling_size,
    )

    if coordinate_array.shape[0] != sampling_size:
        raise ValueError(
            "PyMieSim detector mesh size does not match detector_sampling for angular weight generation. "
            f"Got {coordinate_array.shape[0]} mesh points for sampling={sampling_size}."
        )

    return coordinate_array


def _build_local_split_metric(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, split_normal, _ = _build_local_detector_basis(
        normalized_coordinate_array,
    )
    return normalized_coordinate_array @ split_normal


def _build_local_top_bottom_split_metric(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    normalized_coordinate_array = _normalize_coordinate_array(
        coordinate_array,
    )
    _, _, split_normal = _build_local_detector_basis(
        normalized_coordinate_array,
    )
    return normalized_coordinate_array @ split_normal


def _resolve_preset_value(
    *,
    preset: dict[str, Any],
    key: str,
    fallback: Any,
) -> Any:
    """
    Resolve one detector preset field.
    """
    if key not in preset:
        logger.debug(
            "Detector preset key %r is missing. Using fallback=%r",
            key,
            fallback,
        )
        return fallback

    return preset[key]
