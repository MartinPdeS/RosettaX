"""Resolve settings selected for a peak process."""

from .. import registry
from typing import Any


def build_process_settings(
    *,
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    process_name: str,
) -> dict[str, Any]:
    """
    Build a dictionary of process setting values for the selected process.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    process_settings: dict[str, Any] = {}

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

        if not isinstance(setting_name, str):
            continue

        process_settings[setting_name] = process_setting_value

    return process_settings


