# -*- coding: utf-8 -*-

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
import plotly.graph_objects as go

from RosettaX.utils import plottings
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.upload_limits import format_upload_size, get_max_upload_bytes

from .models import CrossCalibrationPoint, CrossCalibrationResult


SUPPORTED_SCHEMA = "rosettax_calibration_v1"
EXPORT_SCHEMA = "rosettax_cross_calibration_v1"
DEFAULT_EXPORT_FILE_NAME = "cross_calibration"
SUPPORTED_CALIBRATION_TYPES = {"fluorescence", "scattering"}


def resolve_runtime_config(
    runtime_config_data: Any = None,
) -> RuntimeConfig:
    """
    Resolve the active runtime configuration for the cross-calibration page.
    """
    if isinstance(runtime_config_data, dict):
        return RuntimeConfig.from_dict(runtime_config_data)

    return RuntimeConfig.from_default_profile()


def resolve_graph_style(
    runtime_config_data: Any = None,
) -> dict[str, Any]:
    """
    Resolve the graph container style from the active runtime profile.
    """
    runtime_config = resolve_runtime_config(runtime_config_data)
    return {
        "height": runtime_config.get_graph_height(default="850px"),
        "width": "100%",
    }


def _resolve_figure_height_px(
    runtime_config_data: Any = None,
    *,
    default: int = 850,
) -> int:
    runtime_config = resolve_runtime_config(runtime_config_data)
    graph_height = str(runtime_config.get_graph_height(default=f"{default}px")).strip().lower()

    if graph_height.endswith("px"):
        graph_height = graph_height[:-2].strip()

    try:
        resolved_height = int(float(graph_height))
    except Exception:
        return int(default)

    return max(250, resolved_height)


def build_upload_prompt_text(
    role_label: str,
) -> str:
    """
    Build the upload prompt text for one calibration role.
    """
    resolved_role = str(role_label).strip() or "calibration"
    return (
        f"Select {resolved_role} calibration JSON. "
        f"Maximum file size: {format_upload_size()}."
    )


def parse_uploaded_calibration(
    *,
    contents: Any,
    filename: Any,
    expected_calibration_type: Optional[str] = None,
) -> tuple[str, dict[str, Any]]:
    """
    Parse one uploaded RosettaX calibration JSON and optionally validate its type.
    """
    resolved_filename = str(filename or "").strip()

    if not resolved_filename:
        raise ValueError("Uploaded calibration file name is missing.")

    if Path(resolved_filename).suffix.lower() != ".json":
        raise ValueError("Calibration upload must be a .json file.")

    if not isinstance(contents, str) or "," not in contents:
        raise ValueError("Uploaded calibration file has a malformed Dash contents payload.")

    _, encoded_payload = contents.split(",", 1)
    raw_bytes = base64.b64decode(encoded_payload, validate=True)

    if len(raw_bytes) > get_max_upload_bytes():
        raise ValueError(
            "Calibration upload exceeds the maximum supported size of "
            f"{format_upload_size()}."
        )

    record = json.loads(raw_bytes.decode("utf-8"))

    if not isinstance(record, dict):
        raise ValueError("Calibration file root record is invalid.")

    schema = str(record.get("schema", "")).strip()

    if schema != SUPPORTED_SCHEMA:
        raise ValueError(
            f"Calibration file schema is unsupported: {schema or '<missing>'}."
        )

    payload = record.get("payload")

    if not isinstance(payload, dict):
        raise ValueError('Calibration file is missing top level "payload".')

    calibration_type = str(payload.get("calibration_type", "")).strip().lower()

    if calibration_type not in SUPPORTED_CALIBRATION_TYPES:
        raise ValueError(
            f'Calibration type "{calibration_type or "unknown"}" is not supported for cross calibration.'
        )

    expected_type = str(expected_calibration_type or "").strip().lower()

    if expected_type and calibration_type != expected_type:
        raise ValueError(
            f'Expected a {expected_type} calibration, received "{calibration_type or "unknown"}".'
        )

    return resolved_filename, payload


def build_calibration_summary(
    *,
    filename: str,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a lightweight calibration summary for the cross-calibration page.
    """
    calibration_type = str(calibration_payload.get("calibration_type", "")).strip().lower()
    source_channel = str(calibration_payload.get("source_channel", "")).strip()
    applied_output_channel_name = str(
        calibration_payload.get("applied_output_channel_name", "")
    ).strip()

    metadata = calibration_payload.get("metadata")
    instrument_name = ""

    if isinstance(metadata, dict):
        instrument_name = str(
            metadata.get("instrument") or metadata.get("measured_channel") or ""
        ).strip()

    return {
        "file_name": str(filename),
        "calibration_type": calibration_type,
        "source_channel": source_channel,
        "applied_output_channel_name": applied_output_channel_name,
        "output_quantity_label": _resolve_output_quantity_label(calibration_payload),
        "instrument_name": instrument_name,
        "calibration_payload": dict(calibration_payload),
    }


def build_calibration_summary_children(
    summary: Optional[dict[str, Any]],
    *,
    empty_message: str,
) -> list[Any]:
    """
    Build simple summary lines for one uploaded calibration.
    """
    if not isinstance(summary, dict):
        return [empty_message]

    return [
        {
            "label": "File",
            "value": summary.get("file_name") or "n/a",
        },
        {
            "label": "Type",
            "value": summary.get("calibration_type") or "n/a",
        },
        {
            "label": "Source channel",
            "value": summary.get("source_channel") or "n/a",
        },
        {
            "label": "Output scale",
            "value": summary.get("output_quantity_label") or "n/a",
        },
        {
            "label": "Instrument",
            "value": summary.get("instrument_name") or "n/a",
        },
    ]


def build_empty_result_figure(
    *,
    message: str,
    runtime_config_data: Any = None,
) -> go.Figure:
    """
    Build an empty placeholder figure.
    """
    figure = go.Figure()
    figure.update_layout(
        template="plotly_white",
        height=_resolve_figure_height_px(runtime_config_data),
        margin={"l": 70, "r": 20, "t": 30, "b": 70},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": str(message),
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
    )
    return figure


def _resolve_output_quantity_label(
    calibration_payload: dict[str, Any],
) -> str:
    applied_output_channel_name = str(
        calibration_payload.get("applied_output_channel_name", "")
    ).strip()

    if applied_output_channel_name:
        return applied_output_channel_name

    calibration_type = str(calibration_payload.get("calibration_type", "")).strip().lower()

    if calibration_type == "fluorescence":
        nested_payload = calibration_payload.get("payload")
        if isinstance(nested_payload, dict):
            y_definition = str(nested_payload.get("y_definition", "")).strip()
            if y_definition:
                return y_definition
        return "Calibrated fluorescence value"

    output_quantity = str(calibration_payload.get("output_quantity", "")).strip()
    if output_quantity:
        return output_quantity

    return "Calibrated value"


def _as_positive_float(
    value: Any,
) -> Optional[float]:
    try:
        resolved_value = float(value)
    except Exception:
        return None

    if not np.isfinite(resolved_value) or resolved_value <= 0.0:
        return None

    return float(resolved_value)


def _extract_fluorescence_reference_points(
    calibration_payload: dict[str, Any],
) -> tuple[list[dict[str, float]], str]:
    points = calibration_payload.get("reference_points")

    if not isinstance(points, list):
        raise ValueError("Fluorescence calibration is missing reference_points.")

    extracted_points: list[dict[str, float]] = []

    for point in points:
        if not isinstance(point, dict):
            continue

        measured_value = _as_positive_float(point.get("measured_value"))
        reference_value = _as_positive_float(point.get("reference_value"))

        if measured_value is None or reference_value is None:
            continue

        extracted_points.append(
            {
                "measured_value": measured_value,
                "reference_value": reference_value,
            }
        )

    if len(extracted_points) < 2:
        raise ValueError("Fluorescence calibration needs at least two valid reference points.")

    return extracted_points, "Calibrated fluorescence value"


def _extract_scattering_reference_points(
    calibration_payload: dict[str, Any],
) -> tuple[list[dict[str, float]], str]:
    reference_table = calibration_payload.get("reference_table")

    if not isinstance(reference_table, list):
        raise ValueError("Scattering calibration is missing reference_table.")

    coupling_points: list[dict[str, float]] = []
    diameter_points: list[dict[str, float]] = []

    for row in reference_table:
        if not isinstance(row, dict):
            continue

        measured_value = _as_positive_float(row.get("measured_peak_position"))
        expected_coupling = _as_positive_float(row.get("expected_coupling"))
        particle_diameter_nm = _as_positive_float(row.get("particle_diameter_nm"))

        if measured_value is None:
            continue

        if expected_coupling is not None:
            coupling_points.append(
                {
                    "measured_value": measured_value,
                    "reference_value": expected_coupling,
                }
            )

        if particle_diameter_nm is not None:
            diameter_points.append(
                {
                    "measured_value": measured_value,
                    "reference_value": particle_diameter_nm,
                }
            )

    if len(coupling_points) >= 2:
        return coupling_points, "Expected coupling [W]"

    if len(diameter_points) >= 2:
        return diameter_points, "Particle diameter [nm]"

    raise ValueError("Scattering calibration needs at least two valid reference rows.")


def extract_reference_points(
    calibration_payload: dict[str, Any],
) -> tuple[list[dict[str, float]], str]:
    """
    Extract generic measured-to-reference bead points from one saved calibration.
    """
    calibration_type = str(calibration_payload.get("calibration_type", "")).strip().lower()

    if calibration_type == "fluorescence":
        return _extract_fluorescence_reference_points(calibration_payload)

    if calibration_type == "scattering":
        return _extract_scattering_reference_points(calibration_payload)

    raise ValueError(
        f'Calibration type "{calibration_type or "unknown"}" is not supported for cross calibration.'
    )


def _compute_log_log_fit(
    *,
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> tuple[float, float, float]:
    log_x = np.log10(x_values)
    log_y = np.log10(y_values)
    slope, intercept = np.polyfit(log_x, log_y, deg=1)
    fitted_log_y = (slope * log_x) + intercept

    residual_sum_of_squares = float(np.sum((log_y - fitted_log_y) ** 2))
    total_sum_of_squares = float(np.sum((log_y - np.mean(log_y)) ** 2))

    if total_sum_of_squares <= 0.0:
        r_squared = 1.0
    else:
        r_squared = 1.0 - (residual_sum_of_squares / total_sum_of_squares)

    return float(slope), float(intercept), float(r_squared)


def _build_secondary_axis_label(
    *,
    calibration_type: str,
    source_channel: str,
) -> str:
    channel_label = source_channel or "selected detector"

    if calibration_type == "fluorescence":
        return f"Secondary routine-bead peak on {channel_label} [a.u.]"

    return f"Secondary routine-bead peak on {channel_label}"


def build_cross_calibration_result(
    *,
    primary_summary: dict[str, Any],
    secondary_summary: dict[str, Any],
) -> CrossCalibrationResult:
    """
    Build one transfer calibration from a primary to a secondary bead set.
    """
    primary_type = str(primary_summary.get("calibration_type") or "").strip().lower()
    secondary_type = str(secondary_summary.get("calibration_type") or "").strip().lower()

    if primary_type not in SUPPORTED_CALIBRATION_TYPES:
        raise ValueError("The primary calibration type is not supported for cross calibration.")

    if secondary_type not in SUPPORTED_CALIBRATION_TYPES:
        raise ValueError("The secondary calibration type is not supported for cross calibration.")

    if primary_type != secondary_type:
        raise ValueError("Primary and secondary calibrations must be of the same type.")

    primary_source_channel = str(primary_summary.get("source_channel") or "").strip()
    secondary_source_channel = str(secondary_summary.get("source_channel") or "").strip()

    if (
        primary_source_channel
        and secondary_source_channel
        and primary_source_channel != secondary_source_channel
    ):
        raise ValueError("Primary and secondary calibrations must target the same source channel.")

    source_channel = primary_source_channel or secondary_source_channel
    primary_payload = dict(primary_summary.get("calibration_payload") or {})
    secondary_payload = dict(secondary_summary.get("calibration_payload") or {})

    primary_points, primary_reference_label = extract_reference_points(primary_payload)
    secondary_points, _ = extract_reference_points(secondary_payload)

    pair_count = min(len(primary_points), len(secondary_points))

    if pair_count < 2:
        raise ValueError("At least two shared bead points are required to fit a transfer calibration.")

    warnings: list[str] = []

    if len(primary_points) != len(secondary_points):
        warnings.append(
            "Primary and secondary calibrations have different reference counts; paired the first shared points in order."
        )

    used_primary_points = primary_points[:pair_count]
    used_secondary_points = secondary_points[:pair_count]

    x_values = [point["measured_value"] for point in used_secondary_points]
    y_values = [point["reference_value"] for point in used_primary_points]

    x_array = np.asarray(x_values, dtype=float)
    y_array = np.asarray(y_values, dtype=float)

    slope, intercept, r_squared = _compute_log_log_fit(
        x_values=x_array,
        y_values=y_array,
    )

    y_quantity = str(
        primary_summary.get("output_quantity_label")
        or primary_reference_label
        or "Primary calibrated value"
    ).strip()

    points: list[CrossCalibrationPoint] = []

    for index, (primary_point, secondary_point) in enumerate(
        zip(
            used_primary_points,
            used_secondary_points,
        ),
        start=1,
    ):
        points.append(
            CrossCalibrationPoint(
                bead_index=index,
                x_value=float(secondary_point["measured_value"]),
                y_value=float(primary_point["reference_value"]),
                primary_reference_value=float(primary_point["reference_value"]),
                primary_measured_value=float(primary_point["measured_value"]),
                secondary_measured_value=float(secondary_point["measured_value"]),
            )
        )

    return CrossCalibrationResult(
        primary_file_name=str(primary_summary.get("file_name") or "primary.json"),
        secondary_file_name=str(secondary_summary.get("file_name") or "secondary.json"),
        calibration_type=primary_type,
        source_channel=source_channel,
        x_quantity="secondary_measured_value",
        x_axis_label=_build_secondary_axis_label(
            calibration_type=primary_type,
            source_channel=source_channel,
        ),
        y_quantity=y_quantity,
        y_axis_label=f"Primary calibrated scale: {y_quantity}",
        fit_model="log10(y)=slope*log10(x)+intercept",
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        point_count=pair_count,
        warnings=warnings,
        points=points,
    )


def build_result_figure(
    result: Optional[dict[str, Any]],
    runtime_config_data: Any = None,
) -> go.Figure:
    """
    Build the cross-calibration review figure.
    """
    if not isinstance(result, dict):
        return build_empty_result_figure(
            message="Upload a primary and a secondary calibration to build a transfer relation.",
            runtime_config_data=runtime_config_data,
        )

    point_dicts = result.get("points") or []

    if not isinstance(point_dicts, list) or not point_dicts:
        return build_empty_result_figure(
            message="No cross-calibration points are available to plot.",
            runtime_config_data=runtime_config_data,
        )

    x_values = np.asarray([point.get("x_value") for point in point_dicts], dtype=float)
    y_values = np.asarray([point.get("y_value") for point in point_dicts], dtype=float)

    slope = float(result.get("slope"))
    intercept = float(result.get("intercept"))

    fit_x_values = np.geomspace(np.min(x_values), np.max(x_values), 200)
    fit_y_values = (10 ** intercept) * (fit_x_values ** slope)

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="markers",
            name="Paired beads",
            marker={
                "size": 10,
                "color": "#2a9d8f",
                "line": {"color": "#1d3557", "width": 1},
            },
            customdata=np.asarray(
                [point.get("bead_index") for point in point_dicts],
                dtype=int,
            ),
            hovertemplate=(
                "Bead %{customdata}<br>"
                f"{result.get('x_axis_label')}=%{{x:.6g}}<br>"
                f"{result.get('y_axis_label')}=%{{y:.6g}}"
                "<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=fit_x_values,
            y=fit_y_values,
            mode="lines",
            name="Transfer fit",
            line={"color": "#e76f51", "width": 3},
            hovertemplate="Fit<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_white",
        height=_resolve_figure_height_px(runtime_config_data),
        margin={"l": 70, "r": 20, "t": 30, "b": 70},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
    )
    figure.update_xaxes(
        title_text=str(result.get("x_axis_label") or "Secondary routine-bead peak"),
        type="log",
        showgrid=True,
        zeroline=False,
    )
    figure.update_yaxes(
        title_text=str(result.get("y_axis_label") or "Primary calibrated scale"),
        type="log",
        showgrid=True,
        zeroline=False,
    )
    runtime_config = resolve_runtime_config(runtime_config_data)
    visualization_settings = plottings.resolve_runtime_visualization_settings(
        runtime_config,
    )

    return plottings.apply_calibration_chart_style(
        figure,
        marker_size=float(visualization_settings["default_marker_size"]),
        marker_opacity=float(visualization_settings["default_marker_opacity"]),
        line_width=float(visualization_settings["default_line_width"]),
        font_size=float(visualization_settings["default_font_size"]),
        tick_size=float(visualization_settings["default_tick_size"]),
        show_grid=bool(visualization_settings["show_grid"]),
        legend_vertical_anchor=str(visualization_settings["legend_vertical_anchor"]),
        annotation_text_position=str(visualization_settings["annotation_text_position"]),
        margin={
            "l": 70,
            "r": 24,
            "t": 30,
            "b": 70,
        },
        clear_title_text=False,
    )


def build_result_table_data(
    result: Optional[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build table rows for the paired bead points.
    """
    if not isinstance(result, dict):
        return []

    rows: list[dict[str, Any]] = []

    for point in result.get("points") or []:
        if not isinstance(point, dict):
            continue

        rows.append(
            {
                "Bead": point.get("bead_index"),
                "Secondary peak": point.get("secondary_measured_value"),
                "Primary calibrated value": point.get("primary_reference_value"),
                "Primary peak": point.get("primary_measured_value"),
            }
        )

    return rows


def build_result_status_text(
    result: Optional[dict[str, Any]],
) -> str:
    """
    Build one concise status summary.
    """
    if not isinstance(result, dict):
        return "No transfer calibration generated yet."

    summary = (
        f"Built a transfer calibration from {int(result.get('point_count') or 0)} paired bead point(s). "
        f"Fit R²={float(result.get('r_squared') or 0.0):.4f}."
    )

    warnings = result.get("warnings") or []

    if warnings:
        return summary + " " + " ".join(str(item) for item in warnings)

    return summary


def build_export_payload(
    *,
    result: dict[str, Any],
    export_name: str,
) -> dict[str, Any]:
    """
    Build the downloadable cross-calibration payload.
    """
    clean_export_name = str(export_name or DEFAULT_EXPORT_FILE_NAME).strip() or DEFAULT_EXPORT_FILE_NAME
    payload = dict(result)
    payload["calibration_type"] = "cross"
    payload["transfer_role"] = "primary_to_secondary"
    payload["name"] = clean_export_name
    payload["created_at"] = datetime.now().isoformat(timespec="seconds")
    return {
        "schema": EXPORT_SCHEMA,
        "name": clean_export_name,
        "payload": payload,
    }


def build_export_filename(
    export_name: Any,
) -> str:
    """
    Build one stable cross-calibration download filename.
    """
    stem = Path(str(export_name or DEFAULT_EXPORT_FILE_NAME)).stem or DEFAULT_EXPORT_FILE_NAME
    return f"{stem}.json"
