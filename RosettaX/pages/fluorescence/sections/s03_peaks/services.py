# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash
import plotly.graph_objs as go

from RosettaX.utils.plottings import add_vertical_lines, _make_info_figure


def is_enabled(value: Any) -> bool:
    return isinstance(value, list) and ("enabled" in value)


def clean_optional_string(value: Any) -> str:
    if value is None:
        return ""

    cleaned_value = str(value).strip()
    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def clear_peak_lines_payload() -> dict[str, list[Any]]:
    return {"positions": [], "labels": []}


def lock_source_channel(
    *,
    fluorescence_channel: Optional[str],
    current_locked: Optional[str],
    logger: Any,
) -> Any:
    fluorescence_channel_clean = clean_optional_string(fluorescence_channel)

    logger.debug(
        "lock_source_channel called with fluorescence_channel=%r cleaned=%r current_locked=%r",
        fluorescence_channel,
        fluorescence_channel_clean,
        current_locked,
    )

    if not fluorescence_channel_clean:
        logger.debug("No valid fluorescence channel selected. Returning dash.no_update.")
        return dash.no_update

    if isinstance(current_locked, str) and current_locked.strip():
        logger.debug(
            "Source channel already locked to %r. Returning dash.no_update.",
            current_locked,
        )
        return dash.no_update

    logger.debug("Locking fluorescence source channel to %r.", fluorescence_channel_clean)
    return fluorescence_channel_clean


def should_refresh_histogram_store(
    *,
    graph_toggle_value: Any,
    fcs_path: Optional[str],
    scattering_channel: Optional[str],
    fluorescence_channel: Optional[str],
    logger: Any,
) -> tuple[bool, str, str, str]:
    graph_enabled = is_enabled(graph_toggle_value)
    fcs_path_clean = clean_optional_string(fcs_path)
    scattering_channel_clean = clean_optional_string(scattering_channel)
    fluorescence_channel_clean = clean_optional_string(fluorescence_channel)

    logger.debug(
        "should_refresh_histogram_store resolved graph_enabled=%r fcs_path_clean=%r scattering_channel_clean=%r fluorescence_channel_clean=%r",
        graph_enabled,
        fcs_path_clean,
        scattering_channel_clean,
        fluorescence_channel_clean,
    )

    if not graph_enabled:
        logger.debug("Histogram graph is disabled.")
        return False, fcs_path_clean, scattering_channel_clean, fluorescence_channel_clean

    if not fcs_path_clean or not scattering_channel_clean or not fluorescence_channel_clean:
        logger.debug("Missing required input for fluorescence histogram build.")
        return False, fcs_path_clean, scattering_channel_clean, fluorescence_channel_clean

    return True, fcs_path_clean, scattering_channel_clean, fluorescence_channel_clean


def rebuild_fluorescence_histogram_figure(
    *,
    graph_toggle_value: Any,
    yscale_selection: Any,
    stored_figure: Any,
    peak_lines: Any,
    logger: Any,
) -> go.Figure:
    graph_enabled = is_enabled(graph_toggle_value)

    logger.debug(
        "rebuild_fluorescence_histogram_figure called with graph_enabled=%r yscale_selection=%r stored_figure_type=%s peak_lines=%r",
        graph_enabled,
        yscale_selection,
        type(stored_figure).__name__,
        peak_lines,
    )

    if not graph_enabled:
        logger.debug("Histogram graph is hidden. Returning info figure.")
        return _make_info_figure("Histogram is hidden.")

    if not stored_figure:
        logger.debug("No stored figure available. Returning info figure.")
        return _make_info_figure("Select file and channels first.")

    try:
        figure = go.Figure(stored_figure)
    except Exception:
        logger.exception(
            "Failed to reconstruct Plotly figure from stored_figure with type=%s value=%r",
            type(stored_figure).__name__,
            stored_figure,
        )
        raise

    line_positions: list[Any] = []
    line_labels: list[Any] = []

    if isinstance(peak_lines, dict):
        line_positions = peak_lines.get("positions") or []
        line_labels = peak_lines.get("labels") or []

    logger.debug(
        "Applying peak lines to fluorescence figure with line_positions=%r line_labels=%r",
        line_positions,
        line_labels,
    )

    figure = add_vertical_lines(
        fig=figure,
        line_positions=line_positions,
        line_labels=line_labels,
    )

    use_log_scale = isinstance(yscale_selection, list) and ("log" in yscale_selection)
    figure.update_yaxes(type="log" if use_log_scale else "linear")
    figure.update_layout(separators=".,")

    logger.debug(
        "Updated fluorescence figure y axis to %r scale.",
        "log" if use_log_scale else "linear",
    )

    return figure