
import json
import logging
import re
from .. import registry
from pathlib import Path
from RosettaX.utils.fcs_metadata import FCSMetadata
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig
from typing import Any

logger = logging.getLogger(__name__)
DETECTOR_AUTO_DETECT_RULES_PATH = Path(__file__).parents[2] / "detector" / (
    "detector_auto_detect_rules.json"
)
# Keep the shared channel catalog independent of test overrides for instrument rules.
CHANNEL_CATALOG_PATH = Path(__file__).parents[2] / "detector" / "detector_auto_detect_rules.json"


def load_channel_catalog() -> dict[str, Any]:
    """Load shared channel names and matching patterns from the detector catalog.

    Returns
    -------
    dict[str, Any]
        Catalog entries, or an empty dictionary if the resource is unavailable.
    """
    try:
        payload = json.loads(CHANNEL_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("Could not load channel catalog from %s", CHANNEL_CATALOG_PATH)
        return {}
    catalog = payload.get("channel_names", {}) if isinstance(payload, dict) else {}
    return catalog if isinstance(catalog, dict) else {}


SCATTERING_ROLE_NAMES = {"primary", "scattering", "forward"}
FLUORESCENCE_ROLE_NAMES = {"green_fluorescence"}


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
    runtime_config_data: Any = None,
    detector_selection_runtime_config_path: str | None = None,
    auto_select_rosetta_v1: bool = False,
    reset_rosetta_v1: bool = False,
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
            metadata = fcs_file.get_metadata()

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

    selection_mode = resolve_detector_selection_mode(
        runtime_config_data=runtime_config_data,
        detector_selection_runtime_config_path=detector_selection_runtime_config_path,
    )
    matched_rule = resolve_detector_auto_detect_rule(
        metadata=metadata,
    )

    resolved_options: list[list[dict[str, Any]]] = []
    resolved_values: list[Any] = []
    rosetta_scattering_index = next(
        (
            index
            for index, detector_dropdown_id in enumerate(detector_dropdown_ids or [])
            if isinstance(detector_dropdown_id, dict)
            and detector_dropdown_id.get("process") == "Rosetta Script V1"
            and detector_dropdown_id.get("channel") == "scattering"
        ),
        None,
    )
    selected_scattering_channel = None
    if rosetta_scattering_index is not None:
        current_scattering_channel = (current_detector_values or [])[rosetta_scattering_index]
        if auto_select_rosetta_v1 or current_scattering_channel in valid_values:
            selected_scattering_channel = (
                infer_rosetta_v1_channel(
                    column_names=column_names,
                    detector_role="scattering",
                    matched_rule=matched_rule,
                )
                if auto_select_rosetta_v1
                else current_scattering_channel
            )
    scattering_wavelength_nm = extract_channel_wavelength_nm(
        channel_name=selected_scattering_channel,
    )

    for detector_dropdown_id, current_value in zip(
        detector_dropdown_ids or [],
        current_detector_values or [],
        strict=False,
    ):
        resolved_options.append(
            options,
        )

        detector_role = None
        is_rosetta_v1 = (
            isinstance(detector_dropdown_id, dict)
            and detector_dropdown_id.get("process") == "Rosetta Script V1"
        )
        if isinstance(detector_dropdown_id, dict):
            detector_role = detector_dropdown_id.get("channel")

        if is_rosetta_v1 and reset_rosetta_v1:
            default_value = None
        elif is_rosetta_v1:
            selected = (
                infer_rosetta_v1_channel(
                    column_names=column_names,
                    detector_role=detector_role,
                    preferred_wavelength_nm=(
                        scattering_wavelength_nm
                        if detector_role == "green_fluorescence"
                        else None
                    ),
                    matched_rule=matched_rule,
                )
                if auto_select_rosetta_v1
                else None
            )
            default_value = selected or (current_value if current_value in valid_values else None)
        elif current_value in valid_values:
            default_value = current_value
        else:
            default_value = infer_default_detector_channel(
                column_names=column_names,
                metadata=metadata,
                detector_role=detector_role,
                selection_mode=selection_mode,
                matched_rule=matched_rule,
            )

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



def resolve_rosetta_v1_suggestion(
    *,
    column_names: list[str],
    detector_role: Any,
    preferred_wavelength_nm: int | None = None,
    matched_rule: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Suggest a channel and explain the match or ambiguity.

    Parameters
    ----------
    column_names : list[str]
        Available FCS channels.
    detector_role : Any
        Scattering or green fluorescence role.
    preferred_wavelength_nm : int or None
        Preferred excitation wavelength, in nanometers.
    matched_rule : dict or None
        Instrument-specific preferences from the detector catalog.

    Returns
    -------
    tuple[str or None, str]
        Suggested channel and explanation for the user.
    """
    catalog = load_channel_catalog()
    role_aliases = catalog.get("role_aliases", {}).get(detector_role, [detector_role])
    channel_rules = (matched_rule or {}).get("detector_channels", {})
    aliases = next((channel_rules.get(role) for role in role_aliases if channel_rules.get(role)), [])
    instrument_matches = [
        name for name in column_names
        if any(str(name).casefold() == str(alias).casefold() for alias in aliases)
    ]
    instrument_matches = _prefer_channel_measurement(
        channel_names=instrument_matches,
        suffix=catalog.get("preferred_pulse_measurement_suffix", "-H"),
    )
    if len(instrument_matches) == 1:
        name = instrument_matches[0]
        return name, f"Suggested {name} from instrument rule {matched_rule.get('name', '')}."

    keywords = catalog.get("rosetta_keywords", {}).get(detector_role, ())
    matches = [name for name in column_names if any(keyword in str(name).lower() for keyword in keywords)]
    if detector_role == "green_fluorescence":
        if not matches:
            filter_matches = []
            filter_rule = catalog.get("green_filter", {})
            for name in column_names:
                match = re.fullmatch(filter_rule.get("pattern", r"(?!)"), str(name), re.IGNORECASE)
                if match and filter_rule.get("minimum_wavelength_nm", 0) <= int(match.group(1)) <= filter_rule.get("maximum_wavelength_nm", 0):
                    filter_matches.append((name, str(name).rsplit("-", 1)[0].lower(), match.group(2).upper()))
            if len({base for _, base, _ in filter_matches}) == 1:
                preferred_matches = [name for name, _, measurement in filter_matches if measurement == filter_rule.get("preferred_measurement")]
                if len(preferred_matches) == 1:
                    return preferred_matches[0], f"Suggested {preferred_matches[0]} from its blue-laser green emission filter; height was preferred."
                if len(filter_matches) == 1:
                    name = filter_matches[0][0]
                    return name, f"Suggested {name} from its blue-laser green emission filter."
            matches = [name for name, _, _ in filter_matches]
            if matches:
                return None, f"Multiple green filter measurements match: {', '.join(matches)}. Select one manually."
        wavelength_matches = [name for name in matches if extract_channel_wavelength_nm(channel_name=name) == preferred_wavelength_nm]
        if preferred_wavelength_nm is not None and wavelength_matches:
            matches = wavelength_matches
        else:
            preferred_wavelength = str(catalog.get("preferred_green_wavelength_nm", ""))
            preferred = [name for name in matches if preferred_wavelength and preferred_wavelength in str(name).lower()]
            if preferred:
                matches = preferred

    measurement_token = catalog.get("preferred_measurement_token", "")
    peak_matches = [name for name in matches if measurement_token and measurement_token in str(name).lower()]
    if peak_matches:
        matches = peak_matches
    matches = _prefer_channel_measurement(
        channel_names=matches,
        suffix=catalog.get("preferred_pulse_measurement_suffix", "-H"),
    )
    if len(matches) == 1:
        return matches[0], f"Suggested {matches[0]} from its channel name and measurement."
    if matches:
        return None, f"Multiple channels match: {', '.join(matches)}. Select one manually."
    return None, "No matching channel name was found. Select one manually."


def _prefer_channel_measurement(*, channel_names: list[str], suffix: str) -> list[str]:
    """Prefer one pulse measurement suffix when matching channels include it."""
    if not suffix:
        return channel_names
    preferred = [name for name in channel_names if str(name).upper().endswith(str(suffix).upper())]
    return preferred or channel_names


def infer_rosetta_v1_channel(
    *,
    column_names: list[str],
    detector_role: Any,
    preferred_wavelength_nm: int | None = None,
    matched_rule: dict[str, Any] | None = None,
) -> str | None:
    """Return a Rosetta channel suggestion, leaving ambiguous matches unset.

    Parameters
    ----------
    column_names : list[str]
        Available FCS channels.
    detector_role : Any
        Scattering or green fluorescence role.
    preferred_wavelength_nm : int or None
        Preferred excitation wavelength, in nanometers.
    matched_rule : dict or None
        Optional instrument-specific preferences.

    Returns
    -------
    str or None
        Suggested channel when the catalog resolves a unique match.
    """
    return resolve_rosetta_v1_suggestion(
        column_names=column_names,
        detector_role=detector_role,
        preferred_wavelength_nm=preferred_wavelength_nm,
        matched_rule=matched_rule,
    )[0]


def extract_channel_wavelength_nm(*, channel_name: Any) -> int | None:
    """Extract a three-digit wavelength from an FCS channel name.

    Parameters
    ----------
    channel_name : Any
        Candidate FCS channel name.

    Returns
    -------
    int or None
        Wavelength in nanometers when encoded in the channel name.
    """
    match = re.search(r"(?<!\d)(\d{3})(?!\d)", str(channel_name or ""))
    return int(match.group(1)) if match is not None else None


def infer_default_detector_channel(
    *,
    column_names: list[str],
    metadata: FCSMetadata | None = None,
    detector_role: Any = None,
    selection_mode: str = "name-heuristic",
    matched_rule: dict[str, Any] | None = None,
) -> str | None:
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
    if selection_mode == "auto-detect":
        auto_detected_channel = resolve_rule_based_detector_channel(
            column_names=column_names,
            detector_role=detector_role,
            matched_rule=matched_rule or resolve_detector_auto_detect_rule(metadata=metadata),
        )

        if auto_detected_channel:
            return auto_detected_channel

    return infer_detector_channel_from_column_names(
        column_names=column_names,
        detector_role=detector_role,
    )


def infer_detector_channel_from_column_names(
    *,
    column_names: list[str],
    detector_role: Any = None,
) -> str | None:
    """
    Infer a reasonable default detector channel from the available column names.
    """
    role_name = clean_optional_string(detector_role)

    if role_name in FLUORESCENCE_ROLE_NAMES:
        fluorescence_channel = find_fluorescence_channel_from_column_names(
            column_names=column_names,
        )

        if fluorescence_channel:
            return fluorescence_channel

    if role_name in SCATTERING_ROLE_NAMES:
        scattering_channel = find_scattering_channel_from_column_names(
            column_names=column_names,
            detector_role=role_name,
        )

        if scattering_channel:
            return scattering_channel

    preferred_keywords = load_channel_catalog().get("fallback_keywords", [])

    for keyword in preferred_keywords:
        for column_name in column_names:
            if keyword in str(column_name).lower():
                return column_name

    if column_names:
        return column_names[0]

    return None


def find_fluorescence_channel_from_column_names(
    *,
    column_names: list[str],
) -> str | None:
    """
    Find a likely fluorescence detector channel from the available column names.
    """
    catalog = load_channel_catalog()
    preferred_keywords = catalog.get("fluorescence_keywords", [])

    for keyword in preferred_keywords:
        for column_name in column_names:
            normalized_column_name = str(column_name).lower()
            if keyword in normalized_column_name:
                return column_name

    for column_name in column_names:
        normalized_column_name = str(column_name).lower()
        if any(normalized_column_name.startswith(prefix) for prefix in catalog.get("fluorescence_prefixes", [])):
            return column_name

    return None


def find_scattering_channel_from_column_names(
    *,
    column_names: list[str],
    detector_role: str,
) -> str | None:
    """
    Find a likely scattering detector channel from the available column names.
    """
    role_specific_keywords = load_channel_catalog().get("scattering_keywords", {})

    for keyword in role_specific_keywords.get(detector_role, []):
        for column_name in column_names:
            normalized_column_name = str(column_name).lower()
            if keyword in normalized_column_name:
                return column_name

    return None


def resolve_detector_selection_mode(
    *,
    runtime_config_data: Any,
    detector_selection_runtime_config_path: str | None,
) -> str:
    """
    Resolve the detector dropdown defaulting mode for the current page.
    """
    if not detector_selection_runtime_config_path:
        return "name-heuristic"

    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    return str(
        runtime_config.get_str(
            detector_selection_runtime_config_path,
            default="auto-detect",
        )
        or "auto-detect"
    ).strip()


def resolve_detector_auto_detect_rule(
    *,
    metadata: FCSMetadata | None,
) -> dict[str, Any] | None:
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
                logger.debug(
                    "Matched detector auto-detect rule=%r for instrument_name=%r",
                    rule.get("name"),
                    instrument_name,
                )
                return rule

    logger.debug(
        "No detector auto-detect rule matched instrument_name=%r",
        instrument_name,
    )

    return None


def resolve_rule_based_detector_channel(
    *,
    column_names: list[str],
    detector_role: Any,
    matched_rule: dict[str, Any] | None,
) -> str | None:
    """
    Resolve one detector channel from a matched instrument rule.
    """
    if not matched_rule:
        return None

    detector_channels = matched_rule.get("detector_channels")

    if not isinstance(detector_channels, dict):
        return None

    role_name = clean_optional_string(
        detector_role,
    )

    candidate_aliases = None

    for role_alias in load_channel_catalog().get("role_aliases", {}).get(role_name, [role_name]):
        candidate_aliases = detector_channels.get(role_alias)
        if isinstance(candidate_aliases, list) and candidate_aliases:
            break

    if (
        not isinstance(candidate_aliases, list)
        and role_name in SCATTERING_ROLE_NAMES
    ):
        candidate_aliases = detector_channels.get("default")

    if not isinstance(candidate_aliases, list):
        return None

    for candidate_alias in candidate_aliases:
        matched_channel = find_matching_column_name(
            column_names=column_names,
            candidate_name=candidate_alias,
        )

        if matched_channel:
            logger.debug(
                "Resolved detector channel=%r for role=%r from rule=%r",
                matched_channel,
                role_name,
                matched_rule.get("name"),
            )
            return matched_channel

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

    if not isinstance(raw_payload, dict):
        return []

    raw_rules = raw_payload.get("rules")

    if not isinstance(raw_rules, list):
        return []

    normalized_rules: list[dict[str, Any]] = []

    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue

        instrument_aliases = raw_rule.get("instrument_aliases")
        detector_channels = raw_rule.get("detector_channels")

        if not isinstance(instrument_aliases, list) or not isinstance(detector_channels, dict):
            continue

        normalized_rules.append(
            {
                "name": clean_optional_string(raw_rule.get("name")) or "Unnamed detector rule",
                "instrument_aliases": [
                    clean_optional_string(instrument_alias)
                    for instrument_alias in instrument_aliases
                    if clean_optional_string(instrument_alias)
                ],
                "detector_channels": {
                    clean_optional_string(role_name): [
                        clean_optional_string(candidate_name)
                        for candidate_name in candidate_names
                        if clean_optional_string(candidate_name)
                    ]
                    for role_name, candidate_names in detector_channels.items()
                    if clean_optional_string(role_name) and isinstance(candidate_names, list)
                },
            }
        )

    return normalized_rules


def extract_instrument_name_from_metadata(
    *,
    metadata: FCSMetadata | None,
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


def find_matching_column_name(
    *,
    column_names: list[str],
    candidate_name: Any,
) -> str | None:
    """
    Find one FCS column name matching a rule candidate.
    """
    normalized_candidate = normalize_lookup_token(
        candidate_name,
    )

    if not normalized_candidate:
        return None

    for column_name in column_names:
        normalized_column_name = normalize_lookup_token(
            column_name,
        )

        if normalized_column_name == normalized_candidate:
            return column_name

    for column_name in column_names:
        normalized_column_name = normalize_lookup_token(
            column_name,
        )

        if (
            normalized_candidate in normalized_column_name
            or normalized_column_name in normalized_candidate
        ):
            return column_name

    return None


def normalize_lookup_token(value: Any) -> str:
    """
    Normalize one free-text token for case-insensitive lookup.
    """
    return "".join(
        character.lower()
        for character in clean_optional_string(value)
        if character.isalnum()
    )


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
