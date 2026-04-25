# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.peak_script import DEFAULT_PROCESS_NAME
from RosettaX.pages.scattering.sections.s02_peaks import services as scattering_peak_services
from RosettaX.utils import casting
from RosettaX.utils.reader import FCSFile
from RosettaX.utils import plottings

from . import registry


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
        with FCSFile(self.fcs_file_path, writable=False) as fcs_file:
            values = fcs_file.column_copy(
                str(detector_column),
                dtype=dtype,
                n=n,
            )

        return np.asarray(values, dtype=dtype)

    def build_histogram(
        self,
        *,
        detector_column: str,
        n_bins_for_plots: Any,
        max_events_for_analysis: Any,
    ) -> FluorescenceHistogramResult:
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

        values = np.asarray(values, dtype=float)
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
            counts=np.asarray(counts, dtype=float),
            bin_edges=np.asarray(bin_edges, dtype=float),
        )

    def build_histogram_figure(
        self,
        *,
        histogram_result: FluorescenceHistogramResult,
        detector_column: str,
        use_log_counts: bool,
        peak_positions: Optional[list[float]] = None,
    ) -> go.Figure:
        values = np.asarray(histogram_result.values, dtype=float)
        counts = np.asarray(histogram_result.counts, dtype=float)
        bin_edges = np.asarray(histogram_result.bin_edges, dtype=float)

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
            peak_positions=np.asarray(peak_positions, dtype=float),
        )


def get_peak_processes() -> list[Any]:
    return registry.load_peak_scripts()


def build_process_options() -> list[dict[str, str]]:
    return [
        process.get_process_option()
        for process in get_peak_processes()
    ]


def resolve_process_name(process_name: Any) -> str:
    process_name_clean = clean_optional_string(process_name)

    if process_name_clean:
        return process_name_clean

    return DEFAULT_PROCESS_NAME


def get_process_instance_for_name(process_name: Any) -> Any:
    resolved_process_name = resolve_process_name(process_name)

    for process in get_peak_processes():
        if getattr(process, "process_name", None) == resolved_process_name:
            return process

    for process in get_peak_processes():
        if process.get_process_option().get("value") == resolved_process_name:
            return process

    return None


def is_enabled(value: Any) -> bool:
    return scattering_peak_services.is_enabled(value)


def clean_optional_string(value: Any) -> str:
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def build_empty_peak_lines_payload() -> dict[str, list[Any]]:
    return scattering_peak_services.build_empty_peak_lines_payload()


def populate_peak_script_detector_dropdowns(
    *,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    current_detector_values: list[Any],
    logger: logging.Logger,
) -> tuple[list[list[dict[str, Any]]], list[Any]]:
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
    return scattering_peak_services.build_process_visibility_styles(
        process_name=process_name,
        process_container_ids=process_container_ids,
    )


def resolve_graph_toggle_for_process(
    *,
    process_name: Any,
    current_graph_toggle_value: Any,
) -> Any:
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

    uploaded_fcs_path_clean = clean_optional_string(uploaded_fcs_path)

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
):
    """
    Build the fluorescence graph using the exact same graph pipeline as
    scattering peaks.

    Important
    ---------
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
    return scattering_peak_services.build_status_children(
        status_component_ids=status_component_ids,
        target_process_name=target_process_name,
        status=status,
    )


def extract_x_positions_from_peak_lines_payload(
    peak_lines_payload: Any,
) -> list[float]:
    """
    Extract x positions from any peak payload produced by the shared peak scripts.

    This function is only used for fluorescence table writing. The graph still
    receives the original payload unchanged.
    """
    if not isinstance(peak_lines_payload, dict):
        return []

    candidate_values = (
        peak_lines_payload.get("x_positions")
        or peak_lines_payload.get("positions")
        or []
    )

    if not candidate_values and isinstance(peak_lines_payload.get("points"), list):
        candidate_values = [
            point.get("x")
            for point in peak_lines_payload["points"]
            if isinstance(point, dict)
        ]

    x_positions: list[float] = []

    for value in candidate_values:
        try:
            x_positions.append(float(value))
        except Exception:
            continue

    return x_positions


def write_x_positions_to_fluorescence_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
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

    for index, x_position in enumerate(x_positions):
        rows[index]["col2"] = f"{float(x_position):.6g}"

    return rows


def clear_fluorescence_table_peak_positions(
    *,
    table_data: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    for row in rows:
        row["col2"] = ""

    return rows


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
    Resolve a manual graph click using the exact same click behavior as
    scattering peaks.

    The returned peak payload is intentionally not converted. It must remain the
    original shared payload so the shared graph renderer can draw 2D annotations
    exactly as it does in scattering.
    """
    table_result, peak_lines_result, status = scattering_peak_services.resolve_manual_peak_click(
        click_data=click_data,
        process_name=process_name,
        uploaded_fcs_path=uploaded_fcs_path,
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        peak_lines_payload=peak_lines_payload,
        table_data=None,
        mie_model="Solid Sphere",
        logger=logger,
    )

    del table_result

    if peak_lines_result is None:
        return None, None, status

    x_positions = extract_x_positions_from_peak_lines_payload(
        peak_lines_result,
    )

    fluorescence_table_data = write_x_positions_to_fluorescence_table(
        table_data=table_data,
        x_positions=x_positions,
    )

    return fluorescence_table_data, peak_lines_result, status


def estimate_histogram_peak_positions(
    *,
    values: np.ndarray,
    peak_count: int,
    nbins: int,
) -> list[float]:
    values = np.asarray(values, dtype=float)
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
        candidate_indices = list(np.argsort(counts)[-int(peak_count):])

    candidate_indices = sorted(
        candidate_indices,
        key=lambda index: counts[index],
        reverse=True,
    )

    selected_indices = sorted(candidate_indices[: int(peak_count)])
    centers = 0.5 * (edges[:-1] + edges[1:])

    return [
        float(centers[index])
        for index in selected_indices
        if 0 <= index < centers.size
    ]


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
    Resolve a process action using the same process behavior as scattering peaks.

    The returned peak payload is intentionally not converted. Only the table
    update is adapted for fluorescence.
    """
    graph_backend = build_fluorescence_graph_backend(
        uploaded_fcs_path=uploaded_fcs_path,
        fallback_backend=backend,
    )

    table_result, peak_lines_result, status, target_process_name = (
        scattering_peak_services.resolve_process_action(
            triggered_action_id=triggered_action_id,
            backend=graph_backend,
            process_name=process_name,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_dropdown_ids=detector_dropdown_ids,
            detector_dropdown_values=detector_dropdown_values,
            peak_count=peak_count,
            max_events_for_plots=max_events_for_plots,
            table_data=None,
            mie_model="Solid Sphere",
            runtime_config_data=runtime_config_data,
            logger=logger,
        )
    )

    del table_result

    if triggered_action_id is None:
        return None, None, status, target_process_name

    if isinstance(triggered_action_id, dict):
        action_name = clean_optional_string(triggered_action_id.get("action"))
    else:
        action_name = ""

    if action_name == "clear_peaks":
        return (
            clear_fluorescence_table_peak_positions(
                table_data=table_data,
            ),
            build_empty_peak_lines_payload(),
            status or "Cleared fluorescence peaks.",
            target_process_name,
        )

    if peak_lines_result is None:
        return None, None, status, target_process_name

    x_positions = extract_x_positions_from_peak_lines_payload(
        peak_lines_result,
    )

    fluorescence_table_data = write_x_positions_to_fluorescence_table(
        table_data=table_data,
        x_positions=x_positions,
    )

    return (
        fluorescence_table_data,
        peak_lines_result,
        status,
        target_process_name,
    )