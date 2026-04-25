# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.peak_script.registry import build_peak_process_options
from RosettaX.peak_script.registry import get_peak_process_instances
from RosettaX.peak_script.registry import get_process_instance
from RosettaX.peak_script.registry import resolve_process_name as resolve_shared_process_name
from RosettaX.pages.scattering.sections.s02_peaks import services as scattering_peak_services
from RosettaX.utils import casting
from RosettaX.utils import plottings
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FluorescencePeakDetectionResult:
    """
    Minimal peak detection result compatible with the shared peak workflow.
    """

    peak_positions: np.ndarray


@dataclass(frozen=True)
class FluorescenceHistogramResult:
    """
    Minimal histogram result compatible with the shared peak graph workflow.
    """

    values: np.ndarray
    counts: np.ndarray
    bin_edges: np.ndarray


class FluorescencePeakGraphBackendAdapter:
    """
    Adapter exposing the graph and peak methods expected by the shared peak
    services.

    This adapter allows fluorescence peak detection to reuse the same process
    scripts and graph rendering behavior as scattering peak detection without
    forcing the fluorescence backend class to implement scattering specific
    methods.
    """

    def __init__(self, *, fcs_file_path: str) -> None:
        self.fcs_file_path = str(fcs_file_path)
        self.file_path = str(fcs_file_path)

    def column_copy(
        self,
        detector_column: str,
        *,
        dtype: Any = float,
        n: Optional[int] = None,
    ) -> np.ndarray:
        """
        Return a copy of a detector column from the FCS file.
        """
        with FCSFile(self.fcs_file_path, writable=False) as fcs_file:
            values = fcs_file.column_copy(
                str(detector_column),
                dtype=dtype,
                n=n,
            )

        return np.asarray(
            values,
            dtype=dtype,
        )

    def build_histogram(
        self,
        *,
        detector_column: str,
        n_bins_for_plots: Any,
        max_events_for_analysis: Any,
    ) -> FluorescenceHistogramResult:
        """
        Build a histogram for a fluorescence detector column.
        """
        resolved_nbins = casting.as_int(
            n_bins_for_plots,
            default=100,
            min_value=10,
            max_value=5000,
        )

        resolved_max_events = casting.as_int(
            max_events_for_analysis,
            default=10000,
            min_value=1,
            max_value=5_000_000,
        )

        values = self.column_copy(
            str(detector_column),
            dtype=float,
            n=resolved_max_events,
        )

        values = np.asarray(
            values,
            dtype=float,
        )

        values = values[np.isfinite(values)]

        if values.size == 0:
            counts = np.asarray([], dtype=float)
            bin_edges = np.asarray([], dtype=float)

        else:
            counts, bin_edges = np.histogram(
                values,
                bins=int(resolved_nbins),
            )

        return FluorescenceHistogramResult(
            values=values,
            counts=np.asarray(
                counts,
                dtype=float,
            ),
            bin_edges=np.asarray(
                bin_edges,
                dtype=float,
            ),
        )

    def build_histogram_figure(
        self,
        *,
        histogram_result: FluorescenceHistogramResult,
        detector_column: str,
        use_log_counts: bool,
        peak_positions: Optional[list[float]] = None,
    ) -> go.Figure:
        """
        Build a fluorescence histogram figure.
        """
        values = np.asarray(
            histogram_result.values,
            dtype=float,
        )

        counts = np.asarray(
            histogram_result.counts,
            dtype=float,
        )

        bin_edges = np.asarray(
            histogram_result.bin_edges,
            dtype=float,
        )

        figure = go.Figure()

        if counts.size > 0 and bin_edges.size == counts.size + 1:
            bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
            bin_widths = np.diff(bin_edges)

            figure.add_trace(
                go.Bar(
                    x=bin_centers,
                    y=counts,
                    width=bin_widths,
                    name=str(detector_column),
                )
            )

        else:
            figure.add_trace(
                go.Histogram(
                    x=values,
                    name=str(detector_column),
                )
            )

        figure.update_layout(
            xaxis_title=f"{detector_column} [a.u.]",
            yaxis_title="Counts",
            separators=".,",
            hovermode="closest",
            uirevision=f"fluorescence_peak_histogram|{self.fcs_file_path}|{detector_column}",
        )

        figure.update_yaxes(
            type="log" if use_log_counts else "linear",
        )

        if peak_positions:
            figure = plottings.add_vertical_lines(
                fig=figure,
                line_positions=[
                    float(value)
                    for value in peak_positions
                ],
                line_labels=[
                    f"Peak {index + 1}"
                    for index in range(len(peak_positions))
                ],
            )

        return figure

    def find_scattering_peaks(
        self,
        *,
        detector_column: str,
        max_peaks: Any,
        max_events_for_analysis: Any,
        debug: bool = False,
    ) -> FluorescencePeakDetectionResult:
        """
        Find fluorescence peak positions.

        The method name intentionally matches the scattering backend API used by
        shared peak scripts.
        """
        del debug

        resolved_peak_count = casting.as_int(
            max_peaks,
            default=3,
            min_value=1,
            max_value=100,
        )

        resolved_max_events = casting.as_int(
            max_events_for_analysis,
            default=10000,
            min_value=1,
            max_value=5_000_000,
        )

        values = self.column_copy(
            str(detector_column),
            dtype=float,
            n=resolved_max_events,
        )

        peak_positions = estimate_histogram_peak_positions(
            values=values,
            peak_count=resolved_peak_count,
            nbins=200,
        )

        return FluorescencePeakDetectionResult(
            peak_positions=np.asarray(
                peak_positions,
                dtype=float,
            ),
        )


def get_peak_processes() -> list[Any]:
    """
    Return dynamically discovered peak process instances.
    """
    return get_peak_process_instances()


def build_process_options() -> list[dict[str, str]]:
    """
    Build peak detection process dropdown options from discovered peak scripts.
    """
    options = build_peak_process_options()

    logger.debug(
        "Built peak process options option_count=%d options=%r",
        len(options),
        options,
    )

    return options


def resolve_process_name(process_name: Any) -> str:
    """
    Resolve the selected peak process name using the shared peak script registry.
    """
    return resolve_shared_process_name(
        process_name,
    )


def get_process_instance_for_name(process_name: Any) -> Any:
    """
    Return a discovered peak process instance for a selected process name.
    """
    return get_process_instance(
        process_name=process_name,
    )


def is_enabled(value: Any) -> bool:
    """
    Return whether a checklist like value means enabled.
    """
    return scattering_peak_services.is_enabled(
        value,
    )


def clean_optional_string(value: Any) -> str:
    """
    Normalize an optional string value.
    """
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def build_empty_peak_lines_payload() -> dict[str, list[Any]]:
    """
    Build an empty peak line payload.
    """
    return scattering_peak_services.build_empty_peak_lines_payload()


def populate_peak_script_detector_dropdowns(
    *,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    current_detector_values: list[Any],
    logger: logging.Logger,
) -> tuple[list[list[dict[str, Any]]], list[Any]]:
    """
    Populate peak script detector dropdowns.
    """
    return scattering_peak_services.populate_peak_script_detector_dropdowns(
        uploaded_fcs_path=uploaded_fcs_path,
        detector_dropdown_ids=detector_dropdown_ids,
        current_detector_values=current_detector_values,
        logger=logger,
    )


def build_process_visibility_styles(
    *,
    process_name: Any,
    process_container_ids: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build process visibility styles.
    """
    return scattering_peak_services.build_process_visibility_styles(
        process_name=process_name,
        process_container_ids=process_container_ids,
    )


def resolve_graph_toggle_for_process(
    *,
    process_name: Any,
    current_graph_toggle_value: Any,
) -> Any:
    """
    Resolve graph visibility when the selected process changes.
    """
    return scattering_peak_services.resolve_graph_toggle_for_process(
        process_name=process_name,
        current_graph_toggle_value=current_graph_toggle_value,
    )


def build_fluorescence_graph_backend(
    *,
    uploaded_fcs_path: Any,
    fallback_backend: Any,
) -> Any:
    """
    Return a backend compatible with the shared peak graph services.
    """
    if fallback_backend is not None and hasattr(fallback_backend, "build_histogram"):
        return fallback_backend

    uploaded_fcs_path_clean = clean_optional_string(
        uploaded_fcs_path,
    )

    if not uploaded_fcs_path_clean:
        return fallback_backend

    return FluorescencePeakGraphBackendAdapter(
        fcs_file_path=uploaded_fcs_path_clean,
    )


def build_fluorescence_graph_figure(
    *,
    backend: Any,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    graph_toggle_value: Any,
    yscale_selection: Any,
    fluorescence_nbins: Any,
    peak_lines_payload: Any,
    max_events_for_plots: Any,
    runtime_config_data: Any,
) -> go.Figure:
    """
    Build the fluorescence graph using the same graph pipeline as scattering.

    The peak_lines_payload is passed through unchanged. This is required for 2D
    manual workflows because the shared graph renderer expects the original
    process payload structure.
    """
    graph_backend = build_fluorescence_graph_backend(
        uploaded_fcs_path=uploaded_fcs_path,
        fallback_backend=backend,
    )

    return scattering_peak_services.build_scattering_graph_figure(
        backend=graph_backend,
        uploaded_fcs_path=uploaded_fcs_path,
        process_name=process_name,
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        graph_toggle_value=graph_toggle_value,
        yscale_selection=yscale_selection,
        scattering_nbins=fluorescence_nbins,
        peak_lines_payload=peak_lines_payload,
        max_events_for_plots=max_events_for_plots,
        runtime_config_data=runtime_config_data,
    )


def build_status_children(
    *,
    status_component_ids: list[dict[str, Any]],
    target_process_name: Any,
    status: str,
) -> list[Any]:
    """
    Build status children for process specific status components.
    """
    return scattering_peak_services.build_status_children(
        status_component_ids=status_component_ids,
        target_process_name=target_process_name,
        status=status,
    )


def resolve_manual_peak_click(
    *,
    click_data: Any,
    process_name: Any,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    peak_lines_payload: Any,
    table_data: Optional[list[dict[str, Any]]],
    logger: logging.Logger,
) -> tuple[Optional[list[dict[str, Any]]], Any, str]:
    """
    Resolve a manual graph click for the fluorescence page.

    The selected peak script owns the click semantics. This service only maps
    the script result into the fluorescence calibration table schema.

    Important
    ---------
    The table is updated from ``result.new_peak_positions`` only. It is not
    updated from the cumulative ``result.peak_lines_payload``.
    """
    resolved_process_name = resolve_process_name(
        process_name,
    )

    process = get_process_instance_for_name(
        resolved_process_name,
    )

    if process is None:
        return None, None, f"Unknown peak process: {resolved_process_name}"

    if not getattr(process, "supports_manual_click", False):
        return None, None, f"Process {resolved_process_name} does not support manual clicks."

    if not clean_optional_string(uploaded_fcs_path):
        return None, None, "Upload an FCS file first."

    detector_channels = scattering_peak_services.resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
    )

    missing_channels = build_missing_detector_channel_names(
        process=process,
        detector_channels=detector_channels,
    )

    if missing_channels:
        missing_channels_text = ", ".join(missing_channels)

        return (
            None,
            None,
            f"Upload an FCS file and select {missing_channels_text} detector channel first.",
        )

    result = process.add_clicked_peak(
        click_data=click_data,
        existing_peak_lines_payload=peak_lines_payload,
    )

    if result is None:
        return None, None, "No valid peak was selected."

    table_result = apply_peak_process_result_to_fluorescence_table(
        table_data=table_data,
        result=result,
    )

    return (
        table_result,
        result.peak_lines_payload,
        result.status,
    )


def resolve_process_action(
    *,
    triggered_action_id: Any,
    backend: Any,
    process_name: Any,
    uploaded_fcs_path: Optional[str],
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    peak_count: Any,
    max_events_for_plots: Any,
    table_data: Optional[list[dict[str, Any]]],
    runtime_config_data: Any,
    logger: logging.Logger,
) -> tuple[Optional[list[dict[str, Any]]], Any, str, str]:
    """
    Resolve a process action for the fluorescence page.

    The selected peak script owns action semantics. This service only maps the
    script result into the fluorescence calibration table schema.
    """
    target_process_name = resolve_process_name(
        process_name,
    )

    process = get_process_instance_for_name(
        target_process_name,
    )

    if process is None:
        return None, None, f"Unknown peak process: {target_process_name}", target_process_name

    action_name = extract_action_name(
        triggered_action_id,
    )

    if action_name in {"clear", "clear_peaks"}:
        result = process.clear_peaks()

        table_result = apply_peak_process_result_to_fluorescence_table(
            table_data=table_data,
            result=result,
        )

        return (
            table_result,
            result.peak_lines_payload,
            result.status,
            target_process_name,
        )

    if not getattr(process, "supports_automatic_action", False):
        return (
            None,
            None,
            f"Process {target_process_name} does not support automatic actions.",
            target_process_name,
        )

    graph_backend = build_fluorescence_graph_backend(
        uploaded_fcs_path=uploaded_fcs_path,
        fallback_backend=backend,
    )

    if graph_backend is None:
        return (
            None,
            None,
            "Backend is not initialized.",
            target_process_name,
        )

    if not clean_optional_string(uploaded_fcs_path):
        return (
            None,
            None,
            "Upload an FCS file first.",
            target_process_name,
        )

    detector_channels = scattering_peak_services.resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=target_process_name,
    )

    missing_channels = build_missing_detector_channel_names(
        process=process,
        detector_channels=detector_channels,
    )

    if missing_channels:
        missing_channels_text = ", ".join(missing_channels)

        return (
            None,
            None,
            f"Upload an FCS file and select {missing_channels_text} detector channel first.",
            target_process_name,
        )

    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    resolved_max_events_for_analysis = casting.as_int(
        max_events_for_plots,
        default=runtime_config.get_int(
            "calibration.max_events_for_analysis",
            default=10000,
        ),
        min_value=1,
        max_value=5_000_000,
    )

    result = process.run_automatic_action(
        backend=graph_backend,
        detector_channels=detector_channels,
        peak_count=peak_count,
        max_events_for_analysis=resolved_max_events_for_analysis,
    )

    if result is None:
        return (
            None,
            None,
            "No peak result was produced.",
            target_process_name,
        )

    table_result = apply_peak_process_result_to_fluorescence_table(
        table_data=table_data,
        result=result,
    )

    return (
        table_result,
        result.peak_lines_payload,
        result.status,
        target_process_name,
    )


def apply_peak_process_result_to_fluorescence_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    result: Any,
) -> list[dict[str, Any]]:
    """
    Apply a peak process result to the fluorescence calibration table.

    The table update uses the result delta, not the cumulative graph payload.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    if getattr(result, "clear_existing_table_peaks", False):
        rows = clear_fluorescence_table_peak_positions(
            table_data=rows,
        )

    new_peak_positions = getattr(
        result,
        "new_peak_positions",
        None,
    )

    if new_peak_positions is None:
        new_peak_positions = []

    x_positions = extract_x_positions_from_new_peak_positions(
        new_peak_positions,
    )

    if not x_positions:
        return rows

    return append_x_positions_to_fluorescence_table(
        table_data=rows,
        x_positions=x_positions,
    )


def extract_x_positions_from_new_peak_positions(
    new_peak_positions: Any,
) -> list[float]:
    """
    Extract fluorescence table x positions from result.new_peak_positions.

    Supported item shapes:
    - float or int
    - string convertible to float
    - dict with key "x"
    """
    if not isinstance(new_peak_positions, list):
        return []

    x_positions: list[float] = []

    for item in new_peak_positions:
        try:
            if isinstance(item, dict):
                x_positions.append(
                    float(item["x"]),
                )

            else:
                x_positions.append(
                    float(item),
                )

        except Exception:
            logger.debug(
                "Ignoring invalid new peak position item=%r",
                item,
            )

    return x_positions


def append_x_positions_to_fluorescence_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    x_positions: list[float],
) -> list[dict[str, Any]]:
    """
    Append x positions into the fluorescence calibration table.

    Existing measured peak positions in col2 are preserved. New values fill
    empty col2 rows first, then append new rows as needed.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    for x_position in x_positions:
        formatted_position = f"{float(x_position):.6g}"
        row_index = find_first_empty_value_row_index(
            rows=rows,
            column_name="col2",
        )

        if row_index is None:
            rows.append(
                {
                    "col1": "",
                    "col2": formatted_position,
                }
            )

        else:
            rows[row_index]["col2"] = formatted_position

    return rows


def find_first_empty_value_row_index(
    *,
    rows: list[dict[str, Any]],
    column_name: str,
) -> Optional[int]:
    """
    Find the first row index where column_name is empty.
    """
    for row_index, row in enumerate(rows):
        if row.get(column_name) in ("", None):
            return row_index

    return None


def clear_fluorescence_table_peak_positions(
    *,
    table_data: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Clear fluorescence measured peak positions from the calibration table.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    for row in rows:
        row["col2"] = ""

    return rows


def build_missing_detector_channel_names(
    *,
    process: Any,
    detector_channels: dict[str, Any],
) -> list[str]:
    """
    Return detector channel names required by process but not selected.
    """
    missing_channels: list[str] = []

    for channel_name in process.get_required_detector_channels():
        channel_value = detector_channels.get(channel_name)

        if channel_value in ("", None):
            missing_channels.append(
                str(channel_name),
            )

    return missing_channels


def extract_action_name(triggered_action_id: Any) -> str:
    """
    Extract action name from a pattern matched action button id.
    """
    if isinstance(triggered_action_id, dict):
        return clean_optional_string(
            triggered_action_id.get("action"),
        )

    return ""


def estimate_histogram_peak_positions(
    *,
    values: np.ndarray,
    peak_count: int,
    nbins: int,
) -> list[float]:
    """
    Estimate peak positions from a one dimensional histogram.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[np.isfinite(values)]

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

    centers = 0.5 * (edges[:-1] + edges[1:])

    return [
        float(centers[index])
        for index in selected_indices
        if 0 <= index < centers.size
    ]