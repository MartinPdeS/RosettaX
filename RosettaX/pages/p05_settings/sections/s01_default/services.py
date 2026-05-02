# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any, Optional

import numpy as np

from RosettaX.utils import casting, directories
from RosettaX.utils.runtime_config import RuntimeConfig

from . import schema


def _json_safe_scalar(value: Any) -> Any:
    """
    Convert NumPy scalar values into JSON-safe Python scalars.
    """
    if isinstance(value, np.generic):
        return value.item()

    return value


def _json_safe_value(value: Any) -> Any:
    """
    Convert arrays, NumPy scalars, tuples, lists, and dictionaries into JSON-safe values.
    """
    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]

    if isinstance(value, tuple):
        return [_json_safe_value(item) for item in value]

    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}

    return value


def build_profile_options() -> list[dict[str, str]]:
    """
    Build profile dropdown options from saved profile files.
    """
    return [
        {
            "label": file_name,
            "value": file_name,
        }
        for file_name in directories.list_profiles()
    ]


def resolve_default_profile_value(
    profile_options: list[dict[str, str]],
) -> Optional[str]:
    """
    Resolve the initially selected profile.
    """
    if not profile_options:
        return None

    for option in profile_options:
        option_value = str(option.get("value") or "").strip()

        if option_value in {"default_profile", "default_profile.json"}:
            return option_value

    return str(profile_options[0].get("value") or "")


def normalize_profile_filename(profile_name: str) -> str:
    """
    Normalize a profile name into a JSON filename.
    """
    normalized_profile_name = str(profile_name or "").strip()

    if not normalized_profile_name:
        raise ValueError("Profile name cannot be empty.")

    if not normalized_profile_name.endswith(".json"):
        normalized_profile_name = f"{normalized_profile_name}.json"

    return normalized_profile_name


def get_saved_profile(profile_name: Optional[str]) -> Optional[dict[str, Any]]:
    """
    Load a saved profile as a dictionary.
    """
    if not profile_name:
        return None

    normalized_profile_name = normalize_profile_filename(
        profile_name,
    )

    profile_path = Path(directories.profiles) / normalized_profile_name

    if not profile_path.exists():
        return None

    return RuntimeConfig.from_json_path(
        profile_path,
    ).to_dict()


def build_form_field_ids(page) -> dict[str, str]:
    """
    Build the mapping from schema field names to Dash component IDs.

    Every schema field must have a matching attribute in page.ids.Default.
    """
    field_ids: dict[str, str] = {}
    missing_field_names: list[str] = []

    for field_name in schema.ordered_field_names():
        if not hasattr(page.ids.Default, field_name):
            missing_field_names.append(
                field_name,
            )
            continue

        field_ids[field_name] = getattr(
            page.ids.Default,
            field_name,
        )

    if missing_field_names:
        missing_field_names_text = ", ".join(
            missing_field_names,
        )

        raise AttributeError(
            "Missing settings ID(s) for schema field(s): " f"{missing_field_names_text}"
        )

    return field_ids


def _read_runtime_value(
    *,
    runtime_config: RuntimeConfig,
    field_definition: schema.FieldDefinition,
) -> Any:
    """
    Read one field value from a RuntimeConfig.
    """
    value_kind = field_definition.value_kind
    runtime_path = field_definition.runtime_path
    default_value = field_definition.default

    if value_kind == "float":
        return _json_safe_scalar(
            runtime_config.get_float(
                runtime_path,
                default=default_value,
            )
        )

    if value_kind == "int":
        return _json_safe_scalar(
            runtime_config.get_int(
                runtime_path,
                default=default_value,
            )
        )

    if value_kind == "float_list":
        raw_value = runtime_config.get_path(
            runtime_path,
            default=default_value,
        )

        raw_value = _json_safe_value(
            raw_value,
        )

        return casting.format_float_list_for_input(
            raw_value,
        )

    if value_kind == "string":
        raw_value = runtime_config.get_path(
            runtime_path,
            default=default_value,
        )

        raw_value = _json_safe_value(
            raw_value,
        )

        return (
            casting.coerce_optional_string(
                raw_value,
            )
            or ""
        )

    if value_kind == "yes_no_bool":
        resolved_bool = runtime_config.get_bool(
            runtime_path,
            default=bool(default_value),
        )

        return "yes" if resolved_bool else "no"

    if value_kind == "choice":
        raw_value = runtime_config.get_str(
            runtime_path,
            default=str(default_value),
        )

        return coerce_choice_value(
            field_definition=field_definition,
            raw_value=raw_value,
        )

    raise ValueError(f"Unsupported value_kind: {value_kind!r}")


def coerce_choice_value(
    *,
    field_definition: schema.FieldDefinition,
    raw_value: Any,
) -> str:
    """
    Coerce a choice field value and fall back to the schema default if invalid.
    """
    raw_value_string = str(
        raw_value if raw_value is not None else field_definition.default
    ).strip()

    valid_values = {
        str(option.get("value")) for option in (field_definition.options or [])
    }

    if not valid_values:
        return raw_value_string

    if raw_value_string in valid_values:
        return raw_value_string

    default_value_string = str(
        field_definition.default,
    )

    if default_value_string in valid_values:
        return default_value_string

    return sorted(valid_values)[0]


def build_form_store_from_runtime_config(
    runtime_config: RuntimeConfig,
) -> dict[str, Any]:
    """
    Build editable form data from a RuntimeConfig.
    """
    return {
        field_definition.name: _read_runtime_value(
            runtime_config=runtime_config,
            field_definition=field_definition,
        )
        for field_definition in schema.FIELD_DEFINITIONS
    }


def build_form_store_from_form_values(
    form_values: tuple[Any, ...],
) -> dict[str, Any]:
    """
    Build editable form data from Dash callback input values.
    """
    ordered_field_names = schema.ordered_field_names()

    if len(form_values) != len(ordered_field_names):
        raise ValueError(
            f"Expected {len(ordered_field_names)} form values, got {len(form_values)}."
        )

    return {
        field_name: _json_safe_value(value)
        for field_name, value in zip(
            ordered_field_names,
            form_values,
            strict=True,
        )
    }


def build_output_values_from_form_store(
    form_store: dict[str, Any],
) -> tuple[Any, ...]:
    """
    Build ordered Dash output values from form data.
    """
    return tuple(
        _json_safe_value(
            form_store.get(field_name),
        )
        for field_name in schema.ordered_field_names()
    )


def coerce_form_store_to_flat_runtime_payload(
    form_store_data: Any,
) -> dict[str, Any]:
    """
    Coerce form data into a flat runtime payload keyed by schema field name.
    """
    if not isinstance(form_store_data, dict):
        raise TypeError("form_store data must be a dictionary.")

    return {
        field_name: _json_safe_value(
            form_store_data.get(field_name),
        )
        for field_name in schema.ordered_field_names()
    }


def _set_nested_value(
    nested_payload: dict[str, Any],
    dotted_path: str,
    value: Any,
) -> None:
    """
    Set a value in a nested dictionary using a dotted path.
    """
    path_parts = [part for part in str(dotted_path).split(".") if part]

    if not path_parts:
        raise ValueError("dotted_path cannot be empty.")

    current_level = nested_payload

    for path_part in path_parts[:-1]:
        next_level = current_level.get(
            path_part,
        )

        if not isinstance(next_level, dict):
            next_level = {}
            current_level[path_part] = next_level

        current_level = next_level

    current_level[path_parts[-1]] = value


def _coerce_field_value_for_save(
    *,
    field_definition: schema.FieldDefinition,
    raw_value: Any,
) -> Any:
    """
    Coerce one form value into the type expected by the profile payload.
    """
    value_kind = field_definition.value_kind

    if value_kind == "float":
        coerced_value = casting.as_optional_float(
            raw_value,
        )
        return field_definition.default if coerced_value is None else coerced_value

    if value_kind == "int":
        coerced_value = casting.as_optional_int(
            raw_value,
        )
        return field_definition.default if coerced_value is None else coerced_value

    if value_kind == "float_list":
        return casting.as_float_list(
            raw_value,
        ).tolist()

    if value_kind == "string":
        coerced_value = casting.coerce_optional_string(
            raw_value,
        )
        return coerced_value or str(field_definition.default or "")

    if value_kind == "yes_no_bool":
        return (
            str(
                raw_value or "no",
            )
            .strip()
            .lower()
            == "yes"
        )

    if value_kind == "choice":
        return coerce_choice_value(
            field_definition=field_definition,
            raw_value=raw_value,
        )

    raise ValueError(f"Unsupported value_kind: {value_kind!r}")


def build_nested_profile_payload(
    flat_runtime_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a nested profile payload from flat form values.
    """
    nested_profile_payload: dict[str, Any] = {}

    for field_definition in schema.FIELD_DEFINITIONS:
        raw_value = flat_runtime_payload.get(
            field_definition.name,
        )

        coerced_value = _coerce_field_value_for_save(
            field_definition=field_definition,
            raw_value=raw_value,
        )

        _set_nested_value(
            nested_payload=nested_profile_payload,
            dotted_path=field_definition.runtime_path,
            value=coerced_value,
        )

    return nested_profile_payload


def save_profile(
    profile_name: str,
    nested_profile_payload: dict[str, Any],
) -> None:
    """
    Save a nested profile payload to disk.
    """
    normalized_profile_name = normalize_profile_filename(
        profile_name,
    )

    profile_path = Path(directories.profiles) / normalized_profile_name
    profile_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RuntimeConfig.from_dict(
        nested_profile_payload,
    ).to_json_path(
        profile_path,
    )
