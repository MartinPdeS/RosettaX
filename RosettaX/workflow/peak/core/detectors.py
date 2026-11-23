
import logging
from .. import registry
from RosettaX.utils.fcs_metadata import FCSMetadata
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.detector.catalog import (
    INSTRUMENT_CATALOG_PATH,
    load_instrument_catalog,
    load_instrument_rules,
    match_instrument_rule,
)
from typing import Any

logger = logging.getLogger(__name__)
DETECTOR_AUTO_DETECT_RULES_PATH = INSTRUMENT_CATALOG_PATH


def load_channel_catalog() -> dict[str, Any]:
    """Load shared channel names and matching patterns from the detector catalog.

    Returns
    -------
    dict[str, Any]
        Catalog entries, or an empty dictionary if the resource is unavailable.
    """
    try:
        payload = load_instrument_catalog()
    except (OSError, ValueError):
        logger.exception("Could not load channel catalog from %s", INSTRUMENT_CATALOG_PATH)
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
    auto_select_process_name: str | None = None,
    instrument_catalog_key: str | None = None,
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

    if instrument_catalog_key is not None:
        matched_rule = load_instrument_catalog()["instruments"].get(instrument_catalog_key)

    resolved_options: list[list[dict[str, Any]]] = []
    resolved_values: list[Any] = []

    for detector_dropdown_id, current_value in zip(
        detector_dropdown_ids or [],
        current_detector_values or [],
        strict=False,
    ):
        resolved_options.append(
            options,
        )

        detector_role = None
        is_rosetta_script = (
            isinstance(detector_dropdown_id, dict)
            and str(detector_dropdown_id.get("process", "")).startswith("Rosetta Script")
        )
        auto_select_this_process = auto_select_rosetta_v1 and (
            auto_select_process_name is None
            or (
                isinstance(detector_dropdown_id, dict)
                and detector_dropdown_id.get("process") == auto_select_process_name
            )
        )
        if isinstance(detector_dropdown_id, dict):
            detector_role = detector_dropdown_id.get("channel")

        if is_rosetta_script and reset_rosetta_v1:
            default_value = None
        elif is_rosetta_script:
            selected = (
                infer_rosetta_v1_channel(
                    column_names=column_names,
                    detector_role=detector_role,
                    matched_rule=matched_rule,
                )
                if auto_select_this_process
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



def infer_rosetta_v1_channel(
    *,
    column_names: list[str],
    detector_role: Any,
    matched_rule: dict[str, Any] | None = None,
) -> str | None:
    """Resolve a catalog recommendation against the uploaded FCS columns.

    Parameters
    ----------
    column_names : list of str
        Available FCS columns.
    detector_role : str
        Scattering or green fluorescence role.
    matched_rule : dict or None
        Instrument rule resolved from the FCS metadata.

    Returns
    -------
    str or None
        First configured name with a unique case-insensitive match, or None
        when the role needs manual selection.
    """
    recommendations = (matched_rule or {}).get("rosetta_channels", {}).get(detector_role) or []
    for recommendation in recommendations:
        matches = [name for name in column_names if name.casefold() == recommendation.casefold()]
        if len(matches) == 1:
            return matches[0]
    return None


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
    return match_instrument_rule(
        instrument_name=extract_instrument_name_from_metadata(metadata=metadata),
        rules=load_detector_auto_detect_rules(),
    )


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
    """Load FCS instrument rules from the shared catalog."""
    return load_instrument_rules(path=DETECTOR_AUTO_DETECT_RULES_PATH)


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
