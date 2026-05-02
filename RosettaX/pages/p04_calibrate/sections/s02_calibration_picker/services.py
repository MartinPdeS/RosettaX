# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from RosettaX.utils import directories
from RosettaX.utils.paths import resolve_selected_calibration_file_path
from RosettaX.workflow.plotting import scatter2d

logger = logging.getLogger(__name__)


def build_default_folder_definitions() -> list[tuple[str, str, Path]]:
    """
    Build calibration folder definitions.

    Returns
    -------
    list[tuple[str, str, Path]]
        Tuples of folder key, display label, and filesystem path.
    """
    return [
        (
            "fluorescence",
            "Fluorescence",
            directories.fluorescence_calibration,
        ),
        (
            "scattering",
            "Scattering",
            directories.scattering_calibration,
        ),
    ]


def build_dropdown_options(
    *,
    folder_definitions: list[tuple[str, str, Path]],
) -> list[dict[str, str]]:
    """
    Build calibration dropdown options from disk.
    """
    logger.debug("Building calibration dropdown options from disk.")

    dropdown_options: list[dict[str, str]] = []

    for folder_key, folder_label, folder_path in folder_definitions:
        try:
            folder_path.mkdir(
                parents=True,
                exist_ok=True,
            )

            calibration_file_paths = sorted(
                [path for path in folder_path.glob("*.json") if path.is_file()],
                key=lambda path: path.name.lower(),
            )

            logger.debug(
                "Found %d calibration files in folder_key=%r folder_path=%r",
                len(calibration_file_paths),
                folder_key,
                str(folder_path),
            )

            for calibration_file_path in calibration_file_paths:
                dropdown_options.append(
                    {
                        "label": f"{folder_label} | {calibration_file_path.name}",
                        "value": f"{folder_key}/{calibration_file_path.name}",
                    }
                )

        except Exception:
            logger.exception(
                "Failed while building dropdown options for folder_key=%r folder_path=%r",
                folder_key,
                str(folder_path),
            )

    logger.debug(
        "Returning %d total calibration dropdown options.",
        len(dropdown_options),
    )

    return dropdown_options


def resolve_calibration_file_path(
    *,
    selected_calibration: Any,
    folder_definitions: list[tuple[str, str, Path]],
) -> Path:
    """
    Resolve a selected dropdown value into a calibration file path.
    """
    del folder_definitions

    return resolve_selected_calibration_file_path(
        selected_calibration,
    )


def load_calibration_payload(
    *,
    calibration_file_path: Path,
) -> dict[str, Any]:
    """
    Load the top level payload from a calibration JSON file.
    """
    record = json.loads(
        calibration_file_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(record, dict):
        raise ValueError("Calibration file root record is invalid.")

    payload = record.get(
        "payload",
    )

    if not isinstance(payload, dict):
        raise ValueError('Calibration file is missing top level "payload".')

    return payload


def build_calibration_summary(
    *,
    selected_calibration: str,
    calibration_file_path: Path,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a lightweight calibration summary for UI decisions.
    """
    calibration_type = str(
        calibration_payload.get(
            "calibration_type",
            "",
        )
    ).strip()

    source_channel = str(
        calibration_payload.get(
            "source_channel",
            "",
        )
    ).strip()

    output_quantity = str(
        calibration_payload.get(
            "output_quantity",
            "",
        )
    ).strip()

    version = calibration_payload.get(
        "version",
        None,
    )

    instrument_response = calibration_payload.get(
        "instrument_response",
        {},
    )

    if isinstance(instrument_response, dict):
        measured_channel = str(
            instrument_response.get(
                "measured_channel",
                "",
            )
        ).strip()

    else:
        measured_channel = ""

    if not source_channel and measured_channel:
        source_channel = measured_channel

    return {
        "selected_calibration": selected_calibration,
        "file_name": calibration_file_path.name,
        "file_path": str(calibration_file_path),
        "calibration_type": calibration_type,
        "source_channel": source_channel,
        "output_quantity": output_quantity,
        "version": version,
        "is_scattering": calibration_type == "scattering",
        "is_fluorescence": calibration_type == "fluorescence",
        "requires_target_model": calibration_type == "scattering",
        "is_valid": bool(calibration_type),
        "error": "",
    }


def extract_selected_calibration_from_search(
    *,
    search: Optional[str],
) -> Optional[str]:
    """
    Extract selected calibration value from the URL query string.
    """
    logger.debug(
        "Extracting selected_calibration from search=%r",
        search,
    )

    if not search:
        return None

    parsed_query = parse_qs(
        search.lstrip("?"),
    )

    selected_calibration_values = parsed_query.get(
        "selected_calibration",
        [],
    )

    if not selected_calibration_values:
        return None

    selected_calibration = str(
        selected_calibration_values[0],
    ).strip()

    if not selected_calibration:
        return None

    logger.debug(
        "Extracted selected_calibration=%r from URL query string.",
        selected_calibration,
    )

    return selected_calibration


def resolve_target_mie_model(
    *,
    target_mie_model: Any,
) -> str:
    """
    Normalize the target Mie model value.
    """
    target_mie_model_string = str(
        target_mie_model or "Solid Sphere",
    ).strip()

    normalized_target_mie_model = target_mie_model_string.lower()

    if normalized_target_mie_model in {
        "core/shell sphere",
        "core shell sphere",
        "core-shell sphere",
        "coreshell sphere",
        "core_shell_sphere",
    }:
        return "Core/Shell Sphere"

    return "Solid Sphere"


def build_target_parameter_container_style(
    *,
    is_visible: bool,
    is_locked: bool = False,
) -> dict[str, str]:
    """
    Build the target parameter group visibility style.
    """
    return {
        "display": "block" if is_visible else "none",
        "opacity": "0.58" if is_locked else "1.0",
        "transition": "opacity 120ms ease-in-out",
    }


def build_scattering_target_model_container_style(
    *,
    is_visible: bool,
) -> dict[str, str]:
    """
    Build the target model container style.
    """
    return {
        "display": "block" if is_visible else "none",
        "overflow": "visible",
    }


def normalize_axis_scale(
    value: Any,
    *,
    default: str,
) -> str:
    """
    Normalize an axis scale value.
    """
    value_string = str(value or "").strip().lower()

    if value_string in (
        "linear",
        "log",
    ):
        return value_string

    return default


def build_axis_scale_toggle_values(
    *,
    xscale: Any,
    yscale: Any,
) -> list[str]:
    """
    Convert x and y axis scales to Scatter2DGraph checklist values.
    """
    axis_scale_toggle_values: list[str] = []

    if str(xscale).strip().lower() == "log":
        axis_scale_toggle_values.append(
            scatter2d.Scatter2DGraph.x_log_value,
        )

    if str(yscale).strip().lower() == "log":
        axis_scale_toggle_values.append(
            scatter2d.Scatter2DGraph.y_log_value,
        )

    return axis_scale_toggle_values


def build_empty_target_mie_relation_figure() -> Any:
    """
    Build an empty target Mie relation preview figure.
    """
    return scatter2d.Scatter2DGraph.build_empty_figure(
        message="Select a scattering calibration to compute the preview.",
    )


def build_target_mie_relation_figure(
    *,
    full_diameter_values_nm: Any,
    full_coupling_values: Any,
    selected_diameter_values_nm: Any,
    selected_coupling_values: Any,
    show_selected_branch: bool,
    axis_scale_toggle_values: Any,
    x_axis_title: str,
) -> Any:
    """
    Build the target Mie relation preview figure.

    The full Mie relation is always shown. If the full relation is not
    monotonic, the automatically selected largest monotonic branch is shown
    as a second curve.
    """
    traces = [
        scatter2d.Scatter2DTrace(
            x_values=full_diameter_values_nm,
            y_values=full_coupling_values,
            name="Full target Mie relation",
            mode="lines",
        )
    ]

    if show_selected_branch:
        traces.append(
            scatter2d.Scatter2DTrace(
                x_values=selected_diameter_values_nm,
                y_values=selected_coupling_values,
                name="Auto selected largest monotonic branch",
                mode="lines",
            )
        )

    return scatter2d.Scatter2DGraph.build_figure(
        traces=traces,
        title="Target Mie relation preview",
        x_axis_title=x_axis_title,
        y_axis_title="Theoretical optical coupling",
        axis_scale_toggle_values=axis_scale_toggle_values,
        show_grid=True,
        hovermode="closest",
        uirevision="target_mie_relation_preview",
    )
