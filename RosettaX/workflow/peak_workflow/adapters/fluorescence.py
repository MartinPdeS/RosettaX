# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import numpy as np
import plotly.graph_objs as go

from RosettaX.workflow.peak_workflow.adapters.base import BasePeakWorkflowAdapter
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

    The shared peak scripts use the scattering backend API. This adapter exposes
    the same method names for fluorescence FCS files.
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
        Return an owned copy of a detector column.
        """
        with FCSFile(
            self.fcs_file_path,
            writable=False,
        ) as fcs_file:
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
        """
        resolved_number_of_bins = casting.as_int(
            n_bins_for_plots,
            default=100,
            min_value=10,
            max_value=5000,
        )

        resolved_max_events_for_analysis = casting.as_int(
            max_events_for_analysis,
            default=10000,
            min_value=1,
            max_value=5_000_000,
        )

        values = self.column_copy(
            str(detector_column),
            dtype=float,
            n=resolved_max_events_for_analysis,
        )

        values = np.asarray(
            values,
            dtype=float,
        )

        values = values[
            np.isfinite(values)
        ]

        if values.size == 0:
            return FluorescenceHistogramResult(
                values=values,
                counts=np.asarray(
                    [],
                    dtype=float,
                ),
                bin_edges=np.asarray(
                    [],
                    dtype=float,
                ),
            )

        counts, bin_edges = np.histogram(
            values,
            bins=int(resolved_number_of_bins),
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
            bin_centers = 0.5 * (
                bin_edges[:-1] + bin_edges[1:]
            )
            bin_widths = np.diff(
                bin_edges,
            )

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

        resolved_peak_positions = [
            float(value)
            for value in (peak_positions or [])
        ]

        if resolved_peak_positions:
            figure = plottings.add_vertical_lines(
                fig=figure,
                line_positions=resolved_peak_positions,
                line_labels=[
                    f"Peak {index + 1}"
                    for index in range(
                        len(resolved_peak_positions),
                    )
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

        resolved_max_events_for_analysis = casting.as_int(
            max_events_for_analysis,
            default=10000,
            min_value=1,
            max_value=5_000_000,
        )

        values = self.column_copy(
            str(detector_column),
            dtype=float,
            n=resolved_max_events_for_analysis,
        )

        peak_positions = estimate_histogram_peak_positions(
            values=values,
            peak_count=resolved_peak_count,
            number_of_bins=512,
        )

        return FluorescencePeakDetectionResult(
            peak_positions=np.asarray(
                peak_positions,
                dtype=float,
            ),
        )


class FluorescencePeakWorkflowAdapter(BasePeakWorkflowAdapter):
    """
    Adapter for the fluorescence calibration peak workflow.

    This adapter appends only scalar x axis values into the fluorescence
    calibration table. It never writes y values, point dictionaries, lists, or
    full payload objects into the table.
    """

    uploaded_fcs_path_keys: tuple[str, ...] = (
        "uploaded_fcs_path",
        "uploaded_fcs_file_path",
        "fluorescence_uploaded_fcs_path",
        "fcs_path",
    )

    peak_lines_payload_keys: tuple[str, ...] = (
        "fluorescence_peak_lines_payload",
        "peak_lines_payload",
        "peak_lines",
    )

    default_peak_lines_payload_key: str = "fluorescence_peak_lines_payload"

    fluorescence_intensity_column_name: str = "col2"

    fluorescence_intensity_column_candidates: tuple[str, ...] = (
        "col2",
        "Intensity",
        "intensity",
        "Fluorescence intensity",
        "fluorescence_intensity",
        "Measured fluorescence",
        "measured_fluorescence",
        "Peak position",
        "peak_position",
        "Peak",
        "peak",
    )

    automatic_peak_position_names: tuple[str, ...] = (
        "peak_positions",
        "detected_peak_positions",
        "automatic_peak_positions",
        "new_peak_positions",
        "x_positions",
        "x_values",
        "new_x_positions",
    )

    manual_peak_position_names: tuple[str, ...] = (
        "clicked_x",
        "clicked_x_position",
        "clicked_point",
        "new_point",
        "manual_x",
        "manual_x_position",
    )

    def get_backend(
        self,
        *,
        page: Any,
        uploaded_fcs_path: Any,
    ) -> Any:
        """
        Return a backend compatible with the shared peak workflow.
        """
        if hasattr(
            page,
            "get_fluorescence_backend",
        ):
            return page.get_fluorescence_backend(
                uploaded_fcs_path=uploaded_fcs_path,
            )

        if hasattr(
            page,
            "get_backend",
        ):
            return page.get_backend(
                uploaded_fcs_path=uploaded_fcs_path,
            )

        backend = getattr(
            page,
            "backend",
            None,
        )

        if backend is not None and hasattr(
            backend,
            "build_histogram",
        ):
            return backend

        uploaded_fcs_path_clean = str(
            uploaded_fcs_path or "",
        ).strip()

        if not uploaded_fcs_path_clean:
            return None

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
    ) -> Any:
        """
        Append x axis peak values to the fluorescence calibration table.

        Manual graph clicks append exactly one scalar x value. Automatic peak
        detection appends one scalar x value for every detected peak.
        """
        del context

        if getattr(
            result,
            "clear_existing_table_peaks",
            False,
        ):
            return self.clear_fluorescence_peak_column(
                table_data=table_data,
            )

        x_values_to_append = self.extract_x_values_to_append(
            result=result,
        )

        if not x_values_to_append:
            logger.debug(
                "Fluorescence peak process produced no x values to append."
            )

            return dash.no_update

        logger.debug(
            "Appending fluorescence peak x values to table: count=%d values=%r",
            len(x_values_to_append),
            x_values_to_append,
        )

        return self.append_x_values_to_fluorescence_table(
            table_data=table_data,
            x_values=x_values_to_append,
        )

    def extract_x_values_to_append(
        self,
        *,
        result: Any,
    ) -> list[Any]:
        """
        Extract x values to append to the table.

        Priority
        --------
        1. automatic peak arrays, keeping all detected peak values
        2. manual click values, keeping only the latest click
        3. peak line payload arrays, keeping all available values
        """
        if result is None:
            return []

        automatic_value = self.extract_first_existing_attribute_or_key(
            source=result,
            names=self.automatic_peak_position_names,
        )

        if automatic_value is not None:
            return self.extract_x_scalars_from_any_value(
                value=automatic_value,
                keep_only_latest=False,
            )

        manual_value = self.extract_first_existing_attribute_or_key(
            source=result,
            names=self.manual_peak_position_names,
        )

        if manual_value is not None:
            return self.extract_x_scalars_from_any_value(
                value=manual_value,
                keep_only_latest=True,
            )

        peak_lines_payload = getattr(
            result,
            "peak_lines_payload",
            None,
        )

        if peak_lines_payload is None and isinstance(
            result,
            dict,
        ):
            peak_lines_payload = result.get(
                "peak_lines_payload",
            )

        if isinstance(
            peak_lines_payload,
            dict,
        ):
            x_values = self.extract_x_values_from_peak_lines_payload(
                peak_lines_payload=peak_lines_payload,
                keep_only_latest=False,
            )

            if x_values:
                return x_values

        return []

    def extract_first_existing_attribute_or_key(
        self,
        *,
        source: Any,
        names: tuple[str, ...],
    ) -> Any:
        """
        Return the first non None value found as an attribute or dict key.
        """
        for name in names:
            value = getattr(
                source,
                name,
                None,
            )

            if value is not None:
                return value

        if isinstance(
            source,
            dict,
        ):
            for name in names:
                value = source.get(
                    name,
                    None,
                )

                if value is not None:
                    return value

        return None

    def extract_x_scalars_from_any_value(
        self,
        *,
        value: Any,
        keep_only_latest: bool,
    ) -> list[Any]:
        """
        Extract only scalar x values from an arbitrary payload.

        Examples
        --------
        {"x": 12.3, "y": 45.6} -> [12.3]
        [{"x": 1, "y": 2}, {"x": 3, "y": 4}] -> [1, 3]
        np.array([1, 2, 3]) -> [1, 2, 3]
        """
        raw_x_values = self.collect_raw_x_values(
            value=value,
        )

        normalized_x_values = [
            self.normalize_single_x_value_for_table(
                value=raw_x_value,
            )
            for raw_x_value in raw_x_values
        ]

        normalized_x_values = [
            normalized_x_value
            for normalized_x_value in normalized_x_values
            if normalized_x_value != ""
        ]

        if keep_only_latest and normalized_x_values:
            return [
                normalized_x_values[-1],
            ]

        return normalized_x_values

    def collect_raw_x_values(
        self,
        *,
        value: Any,
    ) -> list[Any]:
        """
        Collect raw x values from nested values without normalizing them.
        """
        if value is None:
            return []

        if isinstance(
            value,
            dict,
        ):
            for key in (
                "x",
                "clicked_x",
                "clicked_x_position",
                "x_position",
                "position",
                "value",
                "peak_position",
            ):
                if key in value:
                    return [
                        value[key],
                    ]

            for key in self.automatic_peak_position_names:
                if key in value:
                    return self.collect_raw_x_values(
                        value=value[key],
                    )

            return []

        if isinstance(
            value,
            np.ndarray,
        ):
            if value.ndim == 0:
                return [
                    value.item(),
                ]

            raw_x_values: list[Any] = []

            for item in value.reshape(
                -1,
            ).tolist():
                raw_x_values.extend(
                    self.collect_raw_x_values(
                        value=item,
                    )
                )

            return raw_x_values

        if isinstance(
            value,
            np.generic,
        ):
            return [
                value.item(),
            ]

        if isinstance(
            value,
            (list, tuple),
        ):
            raw_x_values = []

            for item in value:
                raw_x_values.extend(
                    self.collect_raw_x_values(
                        value=item,
                    )
                )

            return raw_x_values

        return [
            value,
        ]

    def extract_x_values_from_peak_lines_payload(
        self,
        *,
        peak_lines_payload: dict[str, Any],
        keep_only_latest: bool,
    ) -> list[Any]:
        """
        Extract x values from a peak line payload.
        """
        candidate_values: list[Any] = []

        points = peak_lines_payload.get(
            "points",
        )

        if isinstance(
            points,
            list,
        ):
            candidate_values.extend(
                points,
            )

        for key in (
            "new_peak_positions",
            "new_x_positions",
            "x_positions",
            "positions",
            "peak_positions",
            "x_values",
            "values",
        ):
            if key not in peak_lines_payload:
                continue

            candidate_values.append(
                peak_lines_payload.get(
                    key,
                )
            )

        if not candidate_values:
            return []

        return self.extract_x_scalars_from_any_value(
            value=candidate_values,
            keep_only_latest=keep_only_latest,
        )

    def extract_latest_x_value_from_peak_lines_payload(
        self,
        *,
        peak_lines_payload: dict[str, Any],
    ) -> Any:
        """
        Extract only the latest x value from a peak line payload.
        """
        x_values = self.extract_x_values_from_peak_lines_payload(
            peak_lines_payload=peak_lines_payload,
            keep_only_latest=True,
        )

        if x_values:
            return x_values[-1]

        return None

    def extract_single_x_value_from_mapping(
        self,
        *,
        mapping: dict[str, Any],
    ) -> Any:
        """
        Extract one x value from a dictionary.
        """
        for key in (
            "x",
            "clicked_x",
            "clicked_x_position",
            "x_position",
            "position",
            "value",
            "peak_position",
        ):
            if key in mapping:
                return mapping[key]

        return None

    def append_x_values_to_fluorescence_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        x_values: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Append x values to the next empty fluorescence table rows.

        Existing filled rows are preserved. New rows are created when there is no
        empty ``col2`` cell left.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        if not rows:
            rows = [
                self.build_empty_fluorescence_table_row(),
            ]

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=self.fluorescence_intensity_column_candidates,
        )

        if target_column_name is None:
            target_column_name = self.fluorescence_intensity_column_name

        for x_value in x_values:
            normalized_x_value = self.normalize_single_x_value_for_table(
                value=x_value,
            )

            if normalized_x_value == "":
                continue

            empty_row_index = self.find_first_empty_value_row_index(
                rows=rows,
                column_name=target_column_name,
            )

            if empty_row_index is None:
                rows.append(
                    self.build_empty_fluorescence_table_row(),
                )
                empty_row_index = len(rows) - 1

            rows[empty_row_index][target_column_name] = normalized_x_value

        return self.normalize_table_data(
            table_data=rows,
        )

    def normalize_single_x_value_for_table(
        self,
        *,
        value: Any,
    ) -> Any:
        """
        Convert one x value to a Dash DataTable scalar.

        Dictionaries are explicitly reduced to their x component. This prevents
        values like {"x": ..., "y": ...} from being written into ``col2``.
        """
        if isinstance(
            value,
            dict,
        ):
            extracted_x_value = self.extract_single_x_value_from_mapping(
                mapping=value,
            )

            if extracted_x_value is None:
                return ""

            return self.normalize_single_x_value_for_table(
                value=extracted_x_value,
            )

        if isinstance(
            value,
            np.ndarray,
        ):
            if value.ndim == 0:
                return self.normalize_single_x_value_for_table(
                    value=value.item(),
                )

            if value.size == 1:
                return self.normalize_single_x_value_for_table(
                    value=value.reshape(-1)[0],
                )

            return ""

        if isinstance(
            value,
            np.generic,
        ):
            return self.normalize_single_x_value_for_table(
                value=value.item(),
            )

        if isinstance(
            value,
            (list, tuple),
        ):
            if not value:
                return ""

            return self.normalize_single_x_value_for_table(
                value=value[-1],
            )

        normalized_value = self.normalize_datatable_value(
            value=value,
        )

        if isinstance(
            normalized_value,
            (str, int, float, bool),
        ):
            return normalized_value

        return str(
            normalized_value,
        )

    def clear_fluorescence_peak_column(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
    ) -> Any:
        """
        Clear the fluorescence measured peak column.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        if not rows:
            return dash.no_update

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=self.fluorescence_intensity_column_candidates,
        )

        if target_column_name is None:
            target_column_name = self.fluorescence_intensity_column_name

        for row in rows:
            row[target_column_name] = ""

        return self.normalize_table_data(
            table_data=rows,
        )

    def find_first_empty_value_row_index(
        self,
        *,
        rows: list[dict[str, Any]],
        column_name: str,
    ) -> Optional[int]:
        """
        Return the first row where the target column is empty.
        """
        for row_index, row in enumerate(
            rows,
        ):
            value = row.get(
                column_name,
                "",
            )

            if value is None:
                return row_index

            if isinstance(
                value,
                str,
            ) and not value.strip():
                return row_index

        return None

    def build_empty_fluorescence_table_row(self) -> dict[str, str]:
        """
        Build an empty fluorescence calibration table row.
        """
        return {
            "col1": "",
            "col2": "",
        }


def estimate_histogram_peak_positions(
    *,
    values: np.ndarray,
    peak_count: int,
    number_of_bins: int,
) -> list[float]:
    """
    Estimate peak positions from a one dimensional histogram.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

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

    counts, bin_edges = np.histogram(
        values,
        bins=int(number_of_bins),
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
        candidate_indices = [
            int(index)
            for index in np.argsort(smoothed_counts)[-int(peak_count):]
        ]

    candidate_indices = sorted(
        candidate_indices,
        key=lambda index: smoothed_counts[index],
        reverse=True,
    )

    selected_indices = sorted(
        candidate_indices[: int(peak_count)]
    )

    bin_centers = 0.5 * (
        bin_edges[:-1] + bin_edges[1:]
    )

    return [
        float(bin_centers[index])
        for index in selected_indices
        if 0 <= index < bin_centers.size
    ]


def smooth_counts(
    *,
    counts: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth histogram counts using a moving average.
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
    Find local maxima indices in a one dimensional signal.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    maxima_indices: list[int] = []

    for index in range(
        1,
        values.size - 1,
    ):
        if values[index] >= values[index - 1] and values[index] >= values[index + 1]:
            maxima_indices.append(
                index,
            )

    return maxima_indices