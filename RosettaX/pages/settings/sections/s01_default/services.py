# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any, Optional

import numpy as np

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import casting, directories
from . import schema

def _json_safe_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def _json_safe_value(value: Any) -> Any:
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
    return [{"label": file_name, "value": file_name} for file_name in directories.list_profiles()]


def resolve_default_profile_value(profile_options: list[dict[str, str]]) -> Optional[str]:
    if not profile_options:
        return None

    for option in profile_options:
        option_value = str(option.get("value") or "").strip()
        if option_value in {"default_profile", "default_profile.json"}:
            return option_value

    return str(profile_options[0].get("value") or "")


def normalize_profile_filename(profile_name: str) -> str:
    normalized_profile_name = str(profile_name or "").strip()

    if not normalized_profile_name:
        raise ValueError("Profile name cannot be empty.")

    if not normalized_profile_name.endswith(".json"):
        normalized_profile_name = f"{normalized_profile_name}.json"

    return normalized_profile_name


def get_saved_profile(profile_name: Optional[str]) -> Optional[dict[str, Any]]:
    if not profile_name:
        return None

    normalized_profile_name = normalize_profile_filename(profile_name)
    profile_path = Path(directories.profiles) / normalized_profile_name

    if not profile_path.exists():
        return None

    return RuntimeConfig.from_json_path(profile_path).to_dict()


def build_form_field_ids(page) -> dict[str, str]:
    return {
        field_name: getattr(page.ids.Default, field_name)
        for field_name in schema.ordered_field_names()
    }


def _read_runtime_value(
    *,
    runtime_config: RuntimeConfig,
    field_definition: schema.FieldDefinition,
) -> Any:
    value_kind = field_definition.value_kind
    runtime_path = field_definition.runtime_path
    default_value = field_definition.default

    if value_kind == "float":
        return _json_safe_scalar(runtime_config.get_float(runtime_path, default=default_value))

    if value_kind == "int":
        return _json_safe_scalar(runtime_config.get_int(runtime_path, default=default_value))

    if value_kind == "float_list":
        raw_value = runtime_config.get_path(runtime_path, default=default_value)
        raw_value = _json_safe_value(raw_value)
        return casting.format_float_list_for_input(raw_value)

    if value_kind == "string":
        raw_value = runtime_config.get_path(runtime_path, default=default_value)
        raw_value = _json_safe_value(raw_value)
        return casting.coerce_optional_string(raw_value) or ""

    if value_kind == "yes_no_bool":
        resolved_bool = runtime_config.get_bool(runtime_path, default=bool(default_value))
        return "yes" if resolved_bool else "no"

    if value_kind == "choice":
        return str(runtime_config.get_str(runtime_path, default=str(default_value)))

    raise ValueError(f"Unsupported value_kind: {value_kind!r}")


def build_form_store_from_runtime_config(runtime_config: RuntimeConfig) -> dict[str, Any]:
    return {
        field_definition.name: _read_runtime_value(
            runtime_config=runtime_config,
            field_definition=field_definition,
        )
        for field_definition in schema.FIELD_DEFINITIONS
    }


def build_form_store_from_form_values(form_values: tuple[Any, ...]) -> dict[str, Any]:
    ordered_field_names = schema.ordered_field_names()

    if len(form_values) != len(ordered_field_names):
        raise ValueError(
            f"Expected {len(ordered_field_names)} form values, got {len(form_values)}."
        )

    return {
        field_name: _json_safe_value(value)
        for field_name, value in zip(ordered_field_names, form_values, strict=True)
    }


def build_output_values_from_form_store(form_store: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        _json_safe_value(form_store.get(field_name))
        for field_name in schema.ordered_field_names()
    )


def coerce_form_store_to_flat_runtime_payload(form_store_data: Any) -> dict[str, Any]:
    if not isinstance(form_store_data, dict):
        raise TypeError("form_store data must be a dictionary.")

    return {
        field_name: _json_safe_value(form_store_data.get(field_name))
        for field_name in schema.ordered_field_names()
    }


def _set_nested_value(
    nested_payload: dict[str, Any],
    dotted_path: str,
    value: Any,
) -> None:
    path_parts = [part for part in str(dotted_path).split(".") if part]
    current_level = nested_payload

    for path_part in path_parts[:-1]:
        next_level = current_level.get(path_part)
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
    value_kind = field_definition.value_kind

    if value_kind == "float":
        return casting.as_optional_float(raw_value)

    if value_kind == "int":
        return casting.as_optional_int(raw_value)

    if value_kind == "float_list":
        return casting.as_float_list(raw_value)

    if value_kind == "string":
        return casting.coerce_optional_string(raw_value)

    if value_kind == "yes_no_bool":
        return str(raw_value or "no").strip().lower() == "yes"

    if value_kind == "choice":
        return str(raw_value or field_definition.default).strip()

    raise ValueError(f"Unsupported value_kind: {value_kind!r}")


def build_nested_profile_payload(flat_runtime_payload: dict[str, Any]) -> dict[str, Any]:
    nested_profile_payload: dict[str, Any] = {}

    for field_definition in schema.FIELD_DEFINITIONS:
        raw_value = flat_runtime_payload.get(field_definition.name)
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


def save_profile(profile_name: str, nested_profile_payload: dict[str, Any]) -> None:
    normalized_profile_name = normalize_profile_filename(profile_name)
    profile_path = Path(directories.profiles) / normalized_profile_name
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    RuntimeConfig.from_dict(nested_profile_payload).to_json_path(profile_path)