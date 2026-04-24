# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import casting, service
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import add_vertical_lines, _make_info_figure


logger = logging.getLogger(__name__)


def is_enabled(value: Any) -> bool:
    return isinstance(value, list) and ("enabled" in value)


def clean_optional_string(value: Any) -> str:
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def clear_peak_lines_payload() -> dict[str, list[Any]]:
    return {
        "positions": [],
        "labels": [],
        "points": [],
        "x_positions": [],
        "y_positions": [],
    }


def get_script_process_name(script: Any) -> str:
    return clean_optional_string(
        getattr(script, "process_name", ""),
    )


def get_script_required_detector_channels(script: Any) -> list[str]:
    try:
        channels = script.get_required_detector_channels()
    except Exception:
        logger.exception(
            "Failed to call get_required_detector_channels on script=%r",
            script,
        )
        return ["primary"]

    if not isinstance(channels, list) or not channels:
        return ["primary"]

    return [
        str(channel)
        for channel in channels
    ]


def script_uses_two_dimensional_graph(script: Any) -> bool:
    channels = get_script_required_detector_channels(
        script,
    )

    return "x" in channels and "y" in channels


def script_should_force_graph_visible(script: Any) -> bool:
    method = getattr(
        script,
        "should_force_histogram_visible",
        None,
    )

    if callable(method):
        try:
            return bool(
                method(
                    selected_process_name=getattr(script, "process_name", None),
                )
            )
        except TypeError:
            try:
                return bool(method())
            except Exception:
                return False
        except Exception:
            return False

    method = getattr(
        script,
        "should_force_graph_visible",
        None,
    )

    if callable(method):
        try:
            return bool(method())
        except Exception:
            return False

    process_name = get_script_process_name(script).lower()

    return "manual" in process_name and "click" in process_name


def script_uses_manual_click(script: Any) -> bool:
    method = getattr(
        script,
        "uses_manual_click",
        None,
    )

    if callable(method):
        try:
            return bool(method())
        except Exception:
            return False

    process_name = get_script_process_name(script).lower()

    return "manual" in process_name and "click" in process_name


def script_is_automatic_peak_finding(script: Any) -> bool:
    process_name = get_script_process_name(script).lower()

    return "automatic" in process_name or "auto" in process_name


def build_controls_for_script(
    *,
    script: Any,
    ids: Any,
) -> Any:
    """
    Build controls for the shared peak scripts.

    The shared scattering scripts are the source of truth. This adapter supports
    both newer class based scripts and older module style scripts.
    """
    try:
        return script.build_controls(
            ids=ids,
        )
    except TypeError:
        return script.build_controls(
            ids=ids,
            detector_dropdown_id_builder=ids.process_detector_dropdown,
        )


def build_visibility_style_for_script(
    *,
    script: Any,
    selected_process_name: Any,
) -> dict[str, Any]:
    method = getattr(
        script,
        "build_visibility_style",
        None,
    )

    if callable(method):
        return method(
            selected_process_name=selected_process_name,
        )

    if clean_optional_string(selected_process_name) == get_script_process_name(script):
        from RosettaX.utils import styling

        return styling.CARD

    return {
        "display": "none",
    }


def build_fluorescence_detector_options(
    *,
    uploaded_fcs_path: Any,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    fcs_path_clean = clean_optional_string(
        uploaded_fcs_path,
    )

    if not fcs_path_clean:
        logger.debug(
            "No FCS path available. Returning empty fluorescence detector options."
        )
        return []

    try:
        channels = service.build_channel_options_from_file(
            fcs_path_clean,
        )
    except Exception:
        logger.exception(
            "Failed to build fluorescence detector options from fcs_path=%r",
            fcs_path_clean,
        )
        return []

    if channels.secondary_options:
        return list(
            channels.secondary_options,
        )

    if channels.scatter_options:
        return list(
            channels.scatter_options,
        )

    return []


def resolve_detector_dropdown_values(
    *,
    detector_dropdown_ids: list[dict[str, Any]],
    current_detector_values: list[Any],
    options: list[dict[str, Any]],
    logger: logging.Logger,
) -> list[Any]:
    allowed_values = {
        str(option.get("value"))
        for option in options
        if "value" in option
    }

    fallback_value = options[0].get("value") if options else None
    resolved_values: list[Any] = []

    for current_value in current_detector_values or []:
        current_value_clean = clean_optional_string(
            current_value,
        )

        if current_value_clean and current_value_clean in allowed_values:
            resolved_values.append(
                current_value_clean,
            )
            continue

        resolved_values.append(
            fallback_value,
        )

    while len(resolved_values) < len(detector_dropdown_ids or []):
        resolved_values.append(
            fallback_value,
        )

    logger.debug(
        "Resolved detector dropdown values=%r for dropdown_ids=%r",
        resolved_values,
        detector_dropdown_ids,
    )

    return resolved_values


def resolve_detector_channel_values(
    *,
    selected_process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
) -> dict[str, str]:
    selected_process_name_clean = clean_optional_string(
        selected_process_name,
    )

    channel_values: dict[str, str] = {}

    for dropdown_id, dropdown_value in zip(
        detector_dropdown_ids or [],
        detector_dropdown_values or [],
        strict=False,
    ):
        if not isinstance(dropdown_id, dict):
            continue

        if dropdown_id.get("process") != selected_process_name_clean:
            continue

        channel_name = clean_optional_string(
            dropdown_id.get("channel"),
        )
        channel_value = clean_optional_string(
            dropdown_value,
        )

        if not channel_name or not channel_value:
            continue

        channel_values[channel_name] = channel_value

    return channel_values


def resolve_primary_channel(
    *,
    selected_process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
) -> Optional[str]:
    channel_values = resolve_detector_channel_values(
        selected_process_name=selected_process_name,
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
    )

    if "primary" in channel_values:
        return channel_values["primary"]

    if "x" in channel_values:
        return channel_values["x"]

    first_value = next(
        iter(channel_values.values()),
        None,
    )

    return first_value


def resolve_setting_value(
    *,
    selected_process_name: Any,
    setting_name: str,
    setting_ids: list[dict[str, Any]],
    setting_values: list[Any],
    fallback_value: Any = None,
) -> Any:
    selected_process_name_clean = clean_optional_string(
        selected_process_name,
    )

    for setting_id, setting_value in zip(
        setting_ids or [],
        setting_values or [],
        strict=False,
    ):
        if not isinstance(setting_id, dict):
            continue

        if setting_id.get("process") != selected_process_name_clean:
            continue

        if setting_id.get("setting") != setting_name:
            continue

        return setting_value

    return fallback_value


def should_refresh_graph_store(
    *,
    graph_toggle_value: Any,
    fcs_path: Any,
    channel_values: dict[str, str],
    logger: logging.Logger,
) -> tuple[bool, str]:
    graph_enabled = is_enabled(
        graph_toggle_value,
    )
    fcs_path_clean = clean_optional_string(
        fcs_path,
    )

    logger.debug(
        "should_refresh_graph_store graph_enabled=%r fcs_path=%r channel_values=%r",
        graph_enabled,
        fcs_path_clean,
        channel_values,
    )

    if not graph_enabled:
        return False, fcs_path_clean

    if not fcs_path_clean:
        return False, fcs_path_clean

    if not channel_values:
        return False, fcs_path_clean

    return True, fcs_path_clean


def build_fluorescence_1d_figure_dict(
    *,
    fcs_path: str,
    fluorescence_channel: str,
    nbins: Any,
    max_events_for_plots: Any,
) -> dict[str, Any]:
    resolved_nbins = casting.as_int(
        nbins,
        default=100,
        min_value=10,
        max_value=5000,
    )

    resolved_max_events = casting.as_int(
        max_events_for_plots,
        default=10000,
        min_value=1,
        max_value=5_000_000,
    )

    with FCSFile(
        str(fcs_path),
        writable=False,
    ) as fcs_file:
        values = fcs_file.column_copy(
            fluorescence_channel,
            dtype=float,
            n=resolved_max_events,
        )

    values = np.asarray(
        values,
        dtype=float,
    )
    values = values[
        np.isfinite(values)
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Histogram(
            x=values,
            nbinsx=resolved_nbins,
            name=fluorescence_channel,
        )
    )

    figure.update_layout(
        xaxis_title=f"{fluorescence_channel} [a.u.]",
        yaxis_title="Counts",
        separators=".,",
        hovermode="closest",
        uirevision=f"fluorescence_peak_1d|{fcs_path}|{fluorescence_channel}",
    )

    return figure.to_dict()


def build_fluorescence_2d_figure_dict(
    *,
    fcs_path: str,
    x_channel: str,
    y_channel: str,
    nbins: Any,
    max_events_for_plots: Any,
) -> dict[str, Any]:
    resolved_nbins = casting.as_int(
        nbins,
        default=100,
        min_value=10,
        max_value=1000,
    )

    resolved_max_events = casting.as_int(
        max_events_for_plots,
        default=10000,
        min_value=1,
        max_value=5_000_000,
    )

    with FCSFile(
        str(fcs_path),
        writable=False,
    ) as fcs_file:
        x_values = fcs_file.column_copy(
            x_channel,
            dtype=float,
            n=resolved_max_events,
        )
        y_values = fcs_file.column_copy(
            y_channel,
            dtype=float,
            n=resolved_max_events,
        )

    x_values = np.asarray(
        x_values,
        dtype=float,
    )
    y_values = np.asarray(
        y_values,
        dtype=float,
    )

    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
    x_values = x_values[finite_mask]
    y_values = y_values[finite_mask]

    figure = go.Figure()

    figure.add_trace(
        go.Histogram2d(
            x=x_values,
            y=y_values,
            nbinsx=resolved_nbins,
            nbinsy=resolved_nbins,
            colorscale="Viridis",
            showscale=True,
            name=f"{x_channel} / {y_channel}",
        )
    )

    figure.update_layout(
        xaxis_title=f"{x_channel} [a.u.]",
        yaxis_title=f"{y_channel} [a.u.]",
        separators=".,",
        hovermode="closest",
        uirevision=f"fluorescence_peak_2d|{fcs_path}|{x_channel}|{y_channel}",
    )

    return figure.to_dict()


def rebuild_fluorescence_graph_figure(
    *,
    graph_toggle_value: Any,
    yscale_selection: Any,
    xscale_selection: Any,
    stored_figure: Any,
    peak_lines: Any,
    is_two_dimensional: bool,
    logger: logging.Logger,
) -> go.Figure:
    graph_enabled = is_enabled(
        graph_toggle_value,
    )

    if not graph_enabled:
        return _make_info_figure(
            "Graph is hidden.",
        )

    if not stored_figure:
        return _make_info_figure(
            "Select file and channels first.",
        )

    try:
        figure = go.Figure(
            stored_figure,
        )
    except Exception:
        logger.exception(
            "Failed to reconstruct fluorescence peak graph."
        )
        return _make_info_figure(
            "Failed to render fluorescence graph.",
        )

    use_y_log_scale = isinstance(yscale_selection, list) and ("log" in yscale_selection)
    use_x_log_scale = isinstance(xscale_selection, list) and ("log" in xscale_selection)

    figure.update_xaxes(
        type="log" if use_x_log_scale else "linear",
    )
    figure.update_yaxes(
        type="log" if use_y_log_scale else "linear",
    )

    if is_two_dimensional:
        figure = add_vertical_lines_from_peak_payload(
            figure=figure,
            peak_lines=peak_lines,
        )
    else:
        line_positions = []
        line_labels = []

        if isinstance(peak_lines, dict):
            line_positions = peak_lines.get("positions") or []
            line_labels = peak_lines.get("labels") or []

        figure = add_vertical_lines(
            fig=figure,
            line_positions=line_positions,
            line_labels=line_labels,
        )

    figure.update_layout(
        separators=".,",
    )

    return figure


def add_vertical_lines_from_peak_payload(
    *,
    figure: go.Figure,
    peak_lines: Any,
) -> go.Figure:
    if not isinstance(peak_lines, dict):
        return figure

    x_positions = peak_lines.get("x_positions") or peak_lines.get("positions") or []
    labels = peak_lines.get("labels") or []

    for index, x_position in enumerate(x_positions):
        try:
            x_value = float(x_position)
        except Exception:
            continue

        label = labels[index] if index < len(labels) else ""

        figure.add_vline(
            x=x_value,
            line_dash="dash",
            annotation_text=str(label),
            annotation_position="top",
        )

    return figure


def extract_x_position_from_click_data(
    click_data: Any,
) -> Optional[float]:
    if not isinstance(click_data, dict):
        return None

    points = click_data.get("points")

    if not isinstance(points, list) or not points:
        return None

    first_point = points[0]

    if not isinstance(first_point, dict):
        return None

    if "x" not in first_point:
        return None

    try:
        return float(first_point["x"])
    except Exception:
        return None


def build_peak_payload_from_x_positions(
    *,
    x_positions: list[float],
    prefix: str,
) -> dict[str, list[Any]]:
    return {
        "positions": [
            float(value)
            for value in x_positions
        ],
        "x_positions": [
            float(value)
            for value in x_positions
        ],
        "y_positions": [],
        "points": [
            {
                "x": float(value),
            }
            for value in x_positions
        ],
        "labels": [
            f"{prefix} {index + 1}"
            for index in range(len(x_positions))
        ],
    }


def extract_x_positions_from_peak_payload(
    peak_lines: Any,
) -> list[float]:
    if not isinstance(peak_lines, dict):
        return []

    raw_positions = peak_lines.get("x_positions") or peak_lines.get("positions") or []
    positions: list[float] = []

    for value in raw_positions:
        try:
            positions.append(
                float(value)
            )
        except Exception:
            continue

    return positions


def write_x_positions_to_calibration_table(
    *,
    table_data: Any,
    x_positions: list[float],
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    while len(rows) < len(x_positions):
        rows.append(
            {
                "col1": "",
                "col2": "",
            }
        )

    for row_index, x_position in enumerate(x_positions):
        rows[row_index]["col2"] = f"{float(x_position):.6g}"

    return rows


def clear_measured_peak_positions_from_table(
    *,
    table_data: Any,
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    for row in rows:
        row["col2"] = ""

    return rows


def estimate_histogram_peak_positions(
    *,
    values: np.ndarray,
    peak_count: int,
    nbins: int,
) -> list[float]:
    values = np.asarray(
        values,
        dtype=float,
    )
    values = values[
        np.isfinite(values)
    ]

    if values.size == 0:
        return []

    counts, edges = np.histogram(
        values,
        bins=int(nbins),
    )

    if counts.size == 0:
        return []

    candidate_indices: list[int] = []

    for index in range(1, counts.size - 1):
        if counts[index] >= counts[index - 1] and counts[index] >= counts[index + 1]:
            candidate_indices.append(index)

    if not candidate_indices:
        candidate_indices = list(
            np.argsort(counts)[-int(peak_count):]
        )

    candidate_indices = sorted(
        candidate_indices,
        key=lambda index: counts[index],
        reverse=True,
    )

    selected_indices = sorted(
        candidate_indices[: int(peak_count)]
    )

    centers = 0.5 * (
        edges[:-1] + edges[1:]
    )

    return [
        float(centers[index])
        for index in selected_indices
        if 0 <= index < centers.size
    ]


def run_automatic_peak_finding(
    *,
    fcs_path: str,
    fluorescence_channel: str,
    peak_count: Any,
    max_events_for_plots: Any,
    table_data: Any,
) -> tuple[Any, dict[str, list[Any]], str]:
    resolved_peak_count = casting.as_int(
        peak_count,
        default=4,
        min_value=1,
        max_value=100,
    )

    resolved_max_events = casting.as_int(
        max_events_for_plots,
        default=10000,
        min_value=1,
        max_value=5_000_000,
    )

    with FCSFile(
        str(fcs_path),
        writable=False,
    ) as fcs_file:
        values = fcs_file.column_copy(
            fluorescence_channel,
            dtype=float,
            n=resolved_max_events,
        )

    peak_positions = estimate_histogram_peak_positions(
        values=np.asarray(values, dtype=float),
        peak_count=resolved_peak_count,
        nbins=200,
    )

    peak_payload = build_peak_payload_from_x_positions(
        x_positions=peak_positions,
        prefix="Peak",
    )

    updated_table_data = write_x_positions_to_calibration_table(
        table_data=table_data,
        x_positions=peak_positions,
    )

    return (
        updated_table_data,
        peak_payload,
        f"Found {len(peak_positions)} fluorescence peak(s).",
    )