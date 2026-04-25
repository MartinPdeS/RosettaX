# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.pages.fluorescence.state import FluorescencePageState
from RosettaX.peak_workflow.adapters import PeakWorkflowAdapter
from RosettaX.peak_workflow.state import build_empty_peak_lines_payload
from RosettaX.peak_workflow.tables import append_positions_to_table_column
from RosettaX.peak_workflow.tables import clear_table_column
from RosettaX.utils import casting
from RosettaX.utils import plottings
from RosettaX.utils.reader import FCSFile


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FluorescencePeakDetectionResult:
    """
    Minimal peak detection result compatible with shared peak scripts.
    """

    peak_positions: np.ndarray


@dataclass(frozen=True)
class FluorescenceHistogramResult:
    """
    Histogram result compatible with the shared peak graph workflow.
    """

    values: np.ndarray
    counts: np.ndarray
    bin_edges: np.ndarray


class FluorescencePeakGraphBackendAdapter:
    """
    Backend adapter exposing the methods expected by shared peak scripts.

    The shared peak scripts were originally written against the scattering
    backend API. This adapter provides the same graph and peak detection method
    names for fluorescence FCS files.
    """

    def __init__(
        self,
        *,
        fcs_file_path: str,
    ) -> None:
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
        Return a copy of a detector column.

        Parameters
        ----------
        detector_column:
            Detector column name.

        dtype:
            Desired dtype.

        n:
            Maximum number of events.

        Returns
        -------
        np.ndarray
            Detector values.
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
        Build a fluorescence histogram.

        Parameters
        ----------
        detector_column:
            Detector column name.

        n_bins_for_plots:
            Histogram bin count.

        max_events_for_analysis:
            Maximum number of events.

        Returns
        -------
        FluorescenceHistogramResult
            Histogram result.
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

        Parameters
        ----------
        histogram_result:
            Histogram result.

        detector_column:
            Detector column name.

        use_log_counts:
            Whether to use log counts.

        peak_positions:
            Optional peak positions.

        Returns
        -------
        go.Figure
            Plotly figure.
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

        Parameters
        ----------
        detector_column:
            Detector column name.

        max_peaks:
            Maximum number of peaks.

        max_events_for_analysis:
            Maximum number of events.

        debug:
            Ignored.

        Returns
        -------
        FluorescencePeakDetectionResult
            Peak detection result.
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
            nbins=512,
        )

        return FluorescencePeakDetectionResult(
            peak_positions=np.asarray(
                peak_positions,
                dtype=float,
            ),
        )


class FluorescencePeakWorkflowAdapter(PeakWorkflowAdapter):
    """
    Adapter connecting the shared peak workflow to the fluorescence page.
    """

    page_kind = "fluorescence"

    def get_page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> FluorescencePageState:
        """
        Parse the fluorescence page state from Dash store data.

        Parameters
        ----------
        page_state_payload:
            Serialized page state.

        Returns
        -------
        FluorescencePageState
            Parsed page state.
        """
        return FluorescencePageState.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

    def get_uploaded_fcs_path(
        self,
        *,
        page_state: FluorescencePageState,
    ) -> Optional[str]:
        """
        Return the uploaded fluorescence FCS path.

        Parameters
        ----------
        page_state:
            Fluorescence page state.

        Returns
        -------
        Optional[str]
            Uploaded FCS path.
        """
        return page_state.uploaded_fcs_path

    def get_peak_lines_payload(
        self,
        *,
        page_state: FluorescencePageState,
    ) -> dict[str, Any]:
        """
        Return the fluorescence peak line payload.

        Parameters
        ----------
        page_state:
            Fluorescence page state.

        Returns
        -------
        dict[str, Any]
            Peak line payload.
        """
        peak_lines_payload = getattr(
            page_state,
            "peak_lines_payload",
            None,
        )

        if isinstance(peak_lines_payload, dict):
            return peak_lines_payload

        return build_empty_peak_lines_payload()

    def update_peak_lines_payload(
        self,
        *,
        page_state: FluorescencePageState,
        peak_lines_payload: Any,
    ) -> FluorescencePageState:
        """
        Return an updated fluorescence page state with a new peak line payload.

        Parameters
        ----------
        page_state:
            Current page state.

        peak_lines_payload:
            New peak line payload.

        Returns
        -------
        FluorescencePageState
            Updated page state.
        """
        return page_state.update(
            peak_lines_payload=peak_lines_payload,
            fluorescence_peak_lines=extract_x_positions_from_peak_lines_payload(
                peak_lines_payload,
            ),
        )

    def get_backend(
        self,
        *,
        page: Any,
        uploaded_fcs_path: Any,
    ) -> Any:
        """
        Return a backend compatible with shared peak scripts.

        Parameters
        ----------
        page:
            Fluorescence page object.

        uploaded_fcs_path:
            Uploaded FCS path.

        Returns
        -------
        Any
            Backend adapter or None.
        """
        fallback_backend = getattr(
            page,
            "backend",
            None,
        )

        if fallback_backend is not None and hasattr(fallback_backend, "build_histogram"):
            return fallback_backend

        uploaded_fcs_path_clean = str(
            uploaded_fcs_path or "",
        ).strip()

        if not uploaded_fcs_path_clean:
            return fallback_backend

        return FluorescencePeakGraphBackendAdapter(
            fcs_file_path=uploaded_fcs_path_clean,
        )

    def apply_peak_process_result_to_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        result: Any,
        context: dict[str, Any],
        logger: logging.Logger,
    ) -> list[dict[str, Any]]:
        """
        Apply a peak process result to the fluorescence calibration table.

        Fluorescence calibration uses:
        - col1 for known MESF or reference value.
        - col2 for measured fluorescence peak position.

        Parameters
        ----------
        table_data:
            Existing table rows.

        result:
            PeakProcessResult.

        context:
            Workflow context.

        logger:
            Logger.

        Returns
        -------
        list[dict[str, Any]]
            Updated table rows.
        """
        del context

        if getattr(result, "clear_existing_table_peaks", False):
            return clear_table_column(
                table_data=table_data,
                column_name="col2",
            )

        peak_positions = getattr(
            result,
            "new_peak_positions",
            None,
        )

        if peak_positions is None:
            peak_positions = getattr(
                result,
                "peak_positions",
                [],
            )

        return append_positions_to_table_column(
            table_data=table_data,
            peak_positions=list(peak_positions or []),
            column_name="col2",
            empty_row_factory=build_empty_fluorescence_table_row,
            logger=logger,
        )


def build_empty_fluorescence_table_row() -> dict[str, str]:
    """
    Build an empty fluorescence calibration table row.

    Returns
    -------
    dict[str, str]
        Empty fluorescence row.
    """
    return {
        "col1": "",
        "col2": "",
    }


def extract_x_positions_from_peak_lines_payload(
    peak_lines_payload: Any,
) -> list[float]:
    """
    Extract x positions from any peak payload produced by shared peak scripts.

    Parameters
    ----------
    peak_lines_payload:
        Peak annotation payload.

    Returns
    -------
    list[float]
        X positions.
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


def estimate_histogram_peak_positions(
    *,
    values: np.ndarray,
    peak_count: int,
    nbins: int,
) -> list[float]:
    """
    Estimate peak positions from a one dimensional histogram.

    Parameters
    ----------
    values:
        Input values.

    peak_count:
        Maximum number of peaks.

    nbins:
        Number of histogram bins.

    Returns
    -------
    list[float]
        Estimated peak positions.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[np.isfinite(values)]

    if values.size == 0:
        return []

    lower_quantile, upper_quantile = np.quantile(
        values,
        [
            0.001,
            0.999,
        ],
    )

    values = values[
        (values >= lower_quantile)
        & (values <= upper_quantile)
    ]

    if values.size == 0:
        return []

    counts, edges = np.histogram(
        values,
        bins=int(nbins),
    )

    if counts.size == 0:
        return []

    smoothed_counts = smooth_counts(
        counts=np.asarray(
            counts,
            dtype=float,
        ),
        window_size=7,
    )

    candidate_indices = find_local_maxima_indices(
        values=smoothed_counts,
    )

    if not candidate_indices:
        candidate_indices = list(
            np.argsort(smoothed_counts)[-int(peak_count):]
        )

    candidate_indices = sorted(
        candidate_indices,
        key=lambda index: smoothed_counts[index],
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


def smooth_counts(
    *,
    counts: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth histogram counts using a moving average.

    Parameters
    ----------
    counts:
        Histogram counts.

    window_size:
        Smoothing window size.

    Returns
    -------
    np.ndarray
        Smoothed counts.
    """
    counts = np.asarray(
        counts,
        dtype=float,
    )

    if counts.size < 3:
        return counts

    resolved_window_size = max(
        3,
        int(window_size),
    )

    if resolved_window_size % 2 == 0:
        resolved_window_size += 1

    if counts.size < resolved_window_size:
        resolved_window_size = counts.size

        if resolved_window_size % 2 == 0:
            resolved_window_size -= 1

    if resolved_window_size < 3:
        return counts

    kernel = np.ones(
        resolved_window_size,
        dtype=float,
    ) / float(resolved_window_size)

    return np.convolve(
        counts,
        kernel,
        mode="same",
    )


def find_local_maxima_indices(
    *,
    values: np.ndarray,
) -> list[int]:
    """
    Find local maxima indices.

    Parameters
    ----------
    values:
        One dimensional signal.

    Returns
    -------
    list[int]
        Local maxima indices.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    maxima_indices: list[int] = []

    for index in range(1, values.size - 1):
        if values[index] >= values[index - 1] and values[index] >= values[index + 1]:
            maxima_indices.append(index)

    return maxima_indices