# -*- coding: utf-8 -*-

from typing import Any, Optional


def build_saved_payload_section_specs(
    *,
    payload: Any,
) -> list[dict[str, Any]]:
    """
    Build report sections for extra saved calibration payload fields.
    """
    if not isinstance(payload, dict):
        return []

    overview_items: list[tuple[str, str]] = []
    section_specs: list[dict[str, Any]] = []
    top_level_excluded_keys = {
        "calibration_type",
        "fit_metrics",
        "fit_model",
        "gating_channel",
        "gating_threshold",
        "instrument_response",
        "output_quantity",
        "parameters",
        "reference_points",
        "reference_table",
        "source_channel",
        "source_file",
    }

    for key, value in payload.items():
        if key in top_level_excluded_keys or is_empty_payload_value(value):
            continue

        if isinstance(value, dict):
            group_items = _build_saved_payload_group_items(
                group_name=key,
                group_payload=value,
            )
            if group_items:
                section_specs.append(
                    {
                        "title": f"Additional calibration fields: {prettify_label(key)}",
                        "items": group_items,
                    }
                )
            continue

        if isinstance(value, list):
            if is_scalar_sequence(value):
                overview_items.append((prettify_label(key), format_display_value(value)))
            continue

        overview_items.append((prettify_label(key), format_display_value(value)))

    if overview_items:
        section_specs.insert(
            0,
            {
                "title": "Additional saved calibration fields",
                "items": overview_items,
            },
        )

    return section_specs


def is_scalar_sequence(value: Any) -> bool:
    return isinstance(value, list) and all(not isinstance(item, (dict, list)) for item in value)


def is_empty_payload_value(value: Any) -> bool:
    if value in (None, "", [], {}):
        return True

    if isinstance(value, dict):
        return all(is_empty_payload_value(item) for item in value.values())

    if isinstance(value, list):
        return all(is_empty_payload_value(item) for item in value)

    return False


def format_display_value(value: Any) -> str:
    if value in (None, ""):
        return "n/a"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if value == 0.0:
            return "0"
        if abs(value) >= 1000.0 or abs(value) < 0.01:
            return f"{value:.4e}"
        return f"{value:.6g}"

    if isinstance(value, list):
        return ", ".join(format_display_value(item) for item in value) or "n/a"

    return str(value)


def format_payload_path_label(path: str) -> str:
    parts = [part for part in str(path).split(".") if part]
    return " / ".join(prettify_label(part) for part in parts) or "Value"


def prettify_label(value: str) -> str:
    label = str(value).replace("_", " ").strip()

    if not label:
        return "Value"

    return label.capitalize()


def _build_saved_payload_group_items(
    *,
    group_name: str,
    group_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    excluded_paths: set[str] = set()

    if group_name == "payload":
        excluded_paths = {
            "slope",
            "intercept",
            "prefactor",
            "R_squared",
            "r_squared",
        }

    return _collect_scalar_payload_items(
        payload=group_payload,
        excluded_paths=excluded_paths,
    )


def _collect_scalar_payload_items(
    *,
    payload: dict[str, Any],
    parent_path: str = "",
    excluded_paths: Optional[set[str]] = None,
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    active_excluded_paths = excluded_paths or set()

    for key, value in payload.items():
        path = f"{parent_path}.{key}" if parent_path else str(key)

        if path in active_excluded_paths or is_empty_payload_value(value):
            continue

        if isinstance(value, dict):
            items.extend(
                _collect_scalar_payload_items(
                    payload=value,
                    parent_path=path,
                    excluded_paths=active_excluded_paths,
                )
            )
            continue

        if isinstance(value, list):
            if is_scalar_sequence(value):
                items.append(
                    (format_payload_path_label(path), format_display_value(value))
                )
            continue

        items.append((format_payload_path_label(path), format_display_value(value)))

    return items
