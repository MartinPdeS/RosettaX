# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import (
    BasePeakProcess,
    PeakProcessResult,
    deduplicate_2d_peak_positions,
    resolve_float_setting,
    resolve_integer_setting,
    resolve_integer_value,
    resolve_yes_no_setting,
)
from RosettaX.utils.io import column_copy


logger = logging.getLogger(__name__)


class QuantileGatedKMeans2DPeakProcess(BasePeakProcess):
    """
    Quantile gated 2D K means peak registration.

    The process gates events on both axes using lower and upper quantiles, then
    runs K means on the remaining two dimensional cloud.

    The table receives only the x coordinate of each detected center through the
    page adapter. The graph receives the full 2D centers, the gate thresholds,
    and grouped event coordinates for colored cluster rendering.
    """

    process_name = "Gated K-means 2D"
    process_label = "Gated K-means 2D"
    description = (
        "Gate events on both axes using quantiles, then run K-means on the "
        "remaining 2D event coordinates."
    )
    graph_type = "2d_scatter"
    sort_order = 50

    supports_manual_click = False
    supports_clear = True
    supports_automatic_action = True
    force_graph_visible = True

    def get_required_detector_channels(self) -> list[str]:
        """
        Return logical detector channels used by this process.
        """
        return [
            "x_axis",
            "y_axis",
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """
        Return user visible detector labels.
        """
        return {
            "x_axis": "X axis channel",
            "y_axis": "Y axis channel",
        }

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return configurable process settings.
        """
        return [
            {
                "name": "cluster_count",
                "label": "Cluster count",
                "kind": "integer",
                "default_value": 2,
                "min_value": 1,
                "max_value": 20,
                "step": 1,
            },
            {
                "name": "minimum_cluster_size",
                "label": "Min cluster size",
                "kind": "integer",
                "default_value": 10,
                "min_value": 1,
                "max_value": 100000,
                "step": 1,
            },
            {
                "name": "x_axis_lower_gate_quantile",
                "label": "X axis lower gate quantile",
                "kind": "float",
                "default_value": 0.0,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
            },
            {
                "name": "x_axis_upper_gate_quantile",
                "label": "X axis upper gate quantile",
                "kind": "float",
                "default_value": 1.0,
                "min_value": 0.501,
                "max_value": 1.0,
                "step": 0.001,
            },
            {
                "name": "y_axis_lower_gate_quantile",
                "label": "Y axis lower gate quantile",
                "kind": "float",
                "default_value": 0.0,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
            },
            {
                "name": "y_axis_upper_gate_quantile",
                "label": "Y axis upper gate quantile",
                "kind": "float",
                "default_value": 1.0,
                "min_value": 0.501,
                "max_value": 1.0,
                "step": 0.001,
            },
            {
                "name": "maximum_iterations",
                "label": "Max iterations",
                "kind": "integer",
                "default_value": 100,
                "min_value": 1,
                "max_value": 1000,
                "step": 10,
            },
            {
                "name": "use_log_transform",
                "label": "Log transform",
                "kind": "select",
                "default_value": "yes",
                "options": [
                    {
                        "label": "Yes",
                        "value": "yes",
                    },
                    {
                        "label": "No",
                        "value": "no",
                    },
                ],
            },
            {
                "name": "include_group_values",
                "label": "Include grouped values for colored graph",
                "kind": "select",
                "default_value": "yes",
                "options": [
                    {
                        "label": "Yes",
                        "value": "yes",
                    },
                    {
                        "label": "No",
                        "value": "no",
                    },
                ],
            },
            {
                "name": "maximum_group_values_per_cluster",
                "label": "Max grouped points per cluster",
                "kind": "integer",
                "default_value": 5000,
                "min_value": 10,
                "max_value": 100000,
                "step": 100,
            },
        ]

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        process_settings: dict[str, Any],
        peak_count: Any = None,
        max_events_for_analysis: Any = None,
        max_events_for_plots: Any = None,
        **_kwargs: Any,
    ) -> Optional[PeakProcessResult]:
        """
        Run quantile gated K means.
        """
        del peak_count

        if backend is None or not hasattr(backend, "fcs_file_path"):
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="The backend does not expose fcs_file_path.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        x_axis_column = detector_channels.get(
            "x_axis",
        )

        y_axis_column = detector_channels.get(
            "y_axis",
        )

        if not str(x_axis_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select an x axis channel first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        if not str(y_axis_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a y axis channel first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        settings = QuantileGatedKMeansSettings.from_process_settings(
            process_settings=process_settings,
        )

        maximum_events = resolve_integer_value(
            value=max_events_for_analysis
            if max_events_for_analysis is not None
            else max_events_for_plots,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        x_axis_values = np.asarray(
            column_copy(
                fcs_file_path=backend.fcs_file_path,
                detector_column=str(x_axis_column),
                dtype=float,
                n=maximum_events,
            ),
            dtype=float,
        )

        y_axis_values = np.asarray(
            column_copy(
                fcs_file_path=backend.fcs_file_path,
                detector_column=str(y_axis_column),
                dtype=float,
                n=maximum_events,
            ),
            dtype=float,
        )

        result = compute_quantile_gated_kmeans_peaks(
            x_axis_values=x_axis_values,
            y_axis_values=y_axis_values,
            settings=settings,
        )

        peak_positions = deduplicate_2d_peak_positions(
            peak_positions=result.peak_positions,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=peak_positions,
            cluster_sizes=result.cluster_sizes,
            grouped_points=result.grouped_points,
            x_axis_lower_gate=result.x_axis_lower_gate,
            x_axis_upper_gate=result.x_axis_upper_gate,
            y_axis_lower_gate=result.y_axis_lower_gate,
            y_axis_upper_gate=result.y_axis_upper_gate,
            include_group_values=settings.include_group_values,
            maximum_group_values_per_cluster=settings.maximum_group_values_per_cluster,
        )

        status = (
            f"Quantile gated K means found {len(peak_positions)} cluster center(s) "
            f"from {result.gated_event_count} gated event(s). "
            f"X gate=[{result.x_axis_lower_gate:.6g}, {result.x_axis_upper_gate:.6g}], "
            f"Y gate=[{result.y_axis_lower_gate:.6g}, {result.y_axis_upper_gate:.6g}]."
        )

        logger.debug(
            "Quantile gated K means completed with x_axis_column=%r y_axis_column=%r "
            "settings=%r gated_event_count=%r peak_positions=%r",
            x_axis_column,
            y_axis_column,
            settings,
            result.gated_event_count,
            peak_positions,
        )

        return PeakProcessResult(
            peak_positions=peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=peak_positions,
            clear_existing_table_peaks=False,
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear graph overlays without modifying the calibration table.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared quantile gated K means graph overlays. Table values were preserved.",
            new_peak_positions=[],
            clear_existing_table_peaks=False,
        )

    def build_empty_peak_lines_payload(self) -> dict[str, Any]:
        """
        Build an empty peak payload.
        """
        return {
            "positions": [],
            "x_positions": [],
            "y_positions": [],
            "points": [],
            "labels": [],
            "cluster_sizes": [],
            "group_points": [],
            "group_labels": [],
            "x_axis_lower_gate": 0.0,
            "x_axis_upper_gate": 0.0,
            "y_axis_lower_gate": 0.0,
            "y_axis_upper_gate": 0.0,
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
        cluster_sizes: list[int],
        grouped_points: list[dict[str, np.ndarray]],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        y_axis_lower_gate: float,
        y_axis_upper_gate: float,
        include_group_values: bool,
        maximum_group_values_per_cluster: int,
    ) -> dict[str, Any]:
        """
        Build graph annotation payload.

        ``group_points`` and ``group_labels`` are included so the graph builder
        can render each K means cluster with a different color.
        """
        x_positions = [
            float(position["x"])
            for position in peak_positions
        ]

        y_positions = [
            float(position["y"])
            for position in peak_positions
        ]

        labels = [
            f"K means cluster {index + 1} | n={cluster_sizes[index]}"
            if index < len(cluster_sizes)
            else f"K means cluster {index + 1}"
            for index in range(len(peak_positions))
        ]

        payload = {
            "positions": x_positions,
            "x_positions": x_positions,
            "y_positions": y_positions,
            "points": [
                {
                    "x": float(position["x"]),
                    "y": float(position["y"]),
                }
                for position in peak_positions
            ],
            "labels": labels,
            "cluster_sizes": [
                int(cluster_size)
                for cluster_size in cluster_sizes
            ],
            "x_axis_lower_gate": float(x_axis_lower_gate),
            "x_axis_upper_gate": float(x_axis_upper_gate),
            "y_axis_lower_gate": float(y_axis_lower_gate),
            "y_axis_upper_gate": float(y_axis_upper_gate),
            "group_points": [],
            "group_labels": [],
        }

        if include_group_values:
            payload["group_points"] = [
                downsample_points(
                    x_values=grouped_points[index]["x_values"],
                    y_values=grouped_points[index]["y_values"],
                    maximum_size=maximum_group_values_per_cluster,
                )
                for index in range(len(grouped_points))
            ]
            payload["group_labels"] = labels

        return payload


class QuantileGatedKMeansSettings:
    """
    Settings for quantile gated 2D K means.
    """

    def __init__(
        self,
        *,
        cluster_count: int,
        minimum_cluster_size: int,
        x_axis_lower_gate_quantile: float,
        x_axis_upper_gate_quantile: float,
        y_axis_lower_gate_quantile: float,
        y_axis_upper_gate_quantile: float,
        maximum_iterations: int,
        use_log_transform: bool,
        include_group_values: bool,
        maximum_group_values_per_cluster: int,
    ) -> None:
        self.cluster_count = cluster_count
        self.minimum_cluster_size = minimum_cluster_size
        self.x_axis_lower_gate_quantile = x_axis_lower_gate_quantile
        self.x_axis_upper_gate_quantile = x_axis_upper_gate_quantile
        self.y_axis_lower_gate_quantile = y_axis_lower_gate_quantile
        self.y_axis_upper_gate_quantile = y_axis_upper_gate_quantile
        self.maximum_iterations = maximum_iterations
        self.use_log_transform = use_log_transform
        self.include_group_values = include_group_values
        self.maximum_group_values_per_cluster = maximum_group_values_per_cluster

    @classmethod
    def from_process_settings(
        cls,
        *,
        process_settings: dict[str, Any],
    ) -> "QuantileGatedKMeansSettings":
        """
        Build settings from Dash process settings.
        """
        x_axis_lower_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="x_axis_lower_gate_quantile",
            default=0.0,
            minimum=0.0,
            maximum=0.499,
        )

        x_axis_upper_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="x_axis_upper_gate_quantile",
            default=1.0,
            minimum=0.501,
            maximum=1.0,
        )

        y_axis_lower_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="y_axis_lower_gate_quantile",
            default=0.0,
            minimum=0.0,
            maximum=0.499,
        )

        y_axis_upper_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="y_axis_upper_gate_quantile",
            default=1.0,
            minimum=0.501,
            maximum=1.0,
        )

        if x_axis_lower_gate_quantile >= x_axis_upper_gate_quantile:
            x_axis_lower_gate_quantile = 0.0
            x_axis_upper_gate_quantile = 1.0

        if y_axis_lower_gate_quantile >= y_axis_upper_gate_quantile:
            y_axis_lower_gate_quantile = 0.0
            y_axis_upper_gate_quantile = 1.0

        return cls(
            cluster_count=resolve_integer_setting(
                settings=process_settings,
                name="cluster_count",
                default=2,
                minimum=1,
                maximum=20,
            ),
            minimum_cluster_size=resolve_integer_setting(
                settings=process_settings,
                name="minimum_cluster_size",
                default=10,
                minimum=1,
                maximum=100000,
            ),
            x_axis_lower_gate_quantile=x_axis_lower_gate_quantile,
            x_axis_upper_gate_quantile=x_axis_upper_gate_quantile,
            y_axis_lower_gate_quantile=y_axis_lower_gate_quantile,
            y_axis_upper_gate_quantile=y_axis_upper_gate_quantile,
            maximum_iterations=resolve_integer_setting(
                settings=process_settings,
                name="maximum_iterations",
                default=100,
                minimum=1,
                maximum=1000,
            ),
            use_log_transform=resolve_yes_no_setting(
                settings=process_settings,
                name="use_log_transform",
                default=True,
            ),
            include_group_values=resolve_yes_no_setting(
                settings=process_settings,
                name="include_group_values",
                default=True,
            ),
            maximum_group_values_per_cluster=resolve_integer_setting(
                settings=process_settings,
                name="maximum_group_values_per_cluster",
                default=5000,
                minimum=10,
                maximum=100000,
            ),
        )

    def __repr__(self) -> str:
        """
        Return a compact debug representation.
        """
        return (
            "QuantileGatedKMeansSettings("
            f"cluster_count={self.cluster_count!r}, "
            f"minimum_cluster_size={self.minimum_cluster_size!r}, "
            f"x_axis_lower_gate_quantile={self.x_axis_lower_gate_quantile!r}, "
            f"x_axis_upper_gate_quantile={self.x_axis_upper_gate_quantile!r}, "
            f"y_axis_lower_gate_quantile={self.y_axis_lower_gate_quantile!r}, "
            f"y_axis_upper_gate_quantile={self.y_axis_upper_gate_quantile!r}, "
            f"maximum_iterations={self.maximum_iterations!r}, "
            f"use_log_transform={self.use_log_transform!r}, "
            f"include_group_values={self.include_group_values!r}, "
            f"maximum_group_values_per_cluster={self.maximum_group_values_per_cluster!r})"
        )


class QuantileGatedKMeansResult:
    """
    Result from quantile gated 2D K means.
    """

    def __init__(
        self,
        *,
        peak_positions: list[dict[str, float]],
        cluster_sizes: list[int],
        grouped_points: list[dict[str, np.ndarray]],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        y_axis_lower_gate: float,
        y_axis_upper_gate: float,
        gated_event_count: int,
    ) -> None:
        self.peak_positions = peak_positions
        self.cluster_sizes = cluster_sizes
        self.grouped_points = grouped_points
        self.x_axis_lower_gate = x_axis_lower_gate
        self.x_axis_upper_gate = x_axis_upper_gate
        self.y_axis_lower_gate = y_axis_lower_gate
        self.y_axis_upper_gate = y_axis_upper_gate
        self.gated_event_count = gated_event_count


def compute_quantile_gated_kmeans_peaks(
    *,
    x_axis_values: Any,
    y_axis_values: Any,
    settings: QuantileGatedKMeansSettings,
) -> QuantileGatedKMeansResult:
    """
    Compute K means centers after x and y quantile gating.
    """
    x_axis_values, y_axis_values = prepare_axis_values(
        x_axis_values=x_axis_values,
        y_axis_values=y_axis_values,
        use_log_transform=settings.use_log_transform,
    )

    if x_axis_values.size == 0:
        return build_empty_quantile_gated_kmeans_result()

    x_axis_lower_gate, x_axis_upper_gate = compute_quantile_gate(
        values=x_axis_values,
        lower_quantile=settings.x_axis_lower_gate_quantile,
        upper_quantile=settings.x_axis_upper_gate_quantile,
    )

    y_axis_lower_gate, y_axis_upper_gate = compute_quantile_gate(
        values=y_axis_values,
        lower_quantile=settings.y_axis_lower_gate_quantile,
        upper_quantile=settings.y_axis_upper_gate_quantile,
    )

    gate_mask = (
        (x_axis_values >= x_axis_lower_gate)
        & (x_axis_values <= x_axis_upper_gate)
        & (y_axis_values >= y_axis_lower_gate)
        & (y_axis_values <= y_axis_upper_gate)
    )

    gated_x_axis_values = x_axis_values[
        gate_mask
    ]

    gated_y_axis_values = y_axis_values[
        gate_mask
    ]

    if gated_x_axis_values.size == 0:
        return QuantileGatedKMeansResult(
            peak_positions=[],
            cluster_sizes=[],
            grouped_points=[],
            x_axis_lower_gate=float(x_axis_lower_gate),
            x_axis_upper_gate=float(x_axis_upper_gate),
            y_axis_lower_gate=float(y_axis_lower_gate),
            y_axis_upper_gate=float(y_axis_upper_gate),
            gated_event_count=0,
        )

    feature_matrix = build_feature_matrix(
        x_axis_values=gated_x_axis_values,
        y_axis_values=gated_y_axis_values,
        use_log_transform=settings.use_log_transform,
    )

    standardized_feature_matrix, feature_center, feature_scale = standardize_feature_matrix(
        feature_matrix=feature_matrix,
    )

    resolved_cluster_count = min(
        int(settings.cluster_count),
        standardized_feature_matrix.shape[0],
    )

    if resolved_cluster_count <= 0:
        return QuantileGatedKMeansResult(
            peak_positions=[],
            cluster_sizes=[],
            grouped_points=[],
            x_axis_lower_gate=float(x_axis_lower_gate),
            x_axis_upper_gate=float(x_axis_upper_gate),
            y_axis_lower_gate=float(y_axis_lower_gate),
            y_axis_upper_gate=float(y_axis_upper_gate),
            gated_event_count=int(gated_x_axis_values.size),
        )

    labels, centers = run_kmeans(
        feature_matrix=standardized_feature_matrix,
        cluster_count=resolved_cluster_count,
        maximum_iterations=settings.maximum_iterations,
    )

    peak_positions, cluster_sizes, grouped_points = convert_kmeans_centers_to_peak_positions(
        labels=labels,
        centers=centers,
        feature_center=feature_center,
        feature_scale=feature_scale,
        gated_x_axis_values=gated_x_axis_values,
        gated_y_axis_values=gated_y_axis_values,
        use_log_transform=settings.use_log_transform,
        minimum_cluster_size=settings.minimum_cluster_size,
    )

    peak_positions, cluster_sizes, grouped_points = sort_peak_positions_by_x_axis(
        peak_positions=peak_positions,
        cluster_sizes=cluster_sizes,
        grouped_points=grouped_points,
    )

    return QuantileGatedKMeansResult(
        peak_positions=peak_positions,
        cluster_sizes=cluster_sizes,
        grouped_points=grouped_points,
        x_axis_lower_gate=float(x_axis_lower_gate),
        x_axis_upper_gate=float(x_axis_upper_gate),
        y_axis_lower_gate=float(y_axis_lower_gate),
        y_axis_upper_gate=float(y_axis_upper_gate),
        gated_event_count=int(gated_x_axis_values.size),
    )


def prepare_axis_values(
    *,
    x_axis_values: Any,
    y_axis_values: Any,
    use_log_transform: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert event coordinates to finite NumPy arrays.
    """
    x_axis_values = np.asarray(
        x_axis_values,
        dtype=float,
    )

    y_axis_values = np.asarray(
        y_axis_values,
        dtype=float,
    )

    finite_mask = np.isfinite(x_axis_values) & np.isfinite(y_axis_values)

    if use_log_transform:
        finite_mask = finite_mask & (x_axis_values > 0.0) & (y_axis_values > 0.0)

    return (
        x_axis_values[finite_mask],
        y_axis_values[finite_mask],
    )


def compute_quantile_gate(
    *,
    values: np.ndarray,
    lower_quantile: float,
    upper_quantile: float,
) -> tuple[float, float]:
    """
    Compute lower and upper gate thresholds from quantiles.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

    if values.size == 0:
        return 0.0, 0.0

    lower_gate, upper_gate = np.quantile(
        values,
        [
            lower_quantile,
            upper_quantile,
        ],
    )

    return (
        float(lower_gate),
        float(upper_gate),
    )


def build_feature_matrix(
    *,
    x_axis_values: np.ndarray,
    y_axis_values: np.ndarray,
    use_log_transform: bool,
) -> np.ndarray:
    """
    Build the two dimensional feature matrix.
    """
    if use_log_transform:
        return np.column_stack(
            [
                np.log10(
                    x_axis_values,
                ),
                np.log10(
                    y_axis_values,
                ),
            ]
        )

    return np.column_stack(
        [
            x_axis_values,
            y_axis_values,
        ]
    )


def standardize_feature_matrix(
    *,
    feature_matrix: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Standardize columns of a feature matrix.
    """
    feature_center = np.median(
        feature_matrix,
        axis=0,
    )

    feature_scale = np.std(
        feature_matrix,
        axis=0,
    )

    feature_scale = np.where(
        feature_scale > 0.0,
        feature_scale,
        1.0,
    )

    standardized_feature_matrix = (
        feature_matrix
        - feature_center
    ) / feature_scale

    return (
        standardized_feature_matrix,
        feature_center,
        feature_scale,
    )


def run_kmeans(
    *,
    feature_matrix: np.ndarray,
    cluster_count: int,
    maximum_iterations: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Run deterministic K means.
    """
    feature_matrix = np.asarray(
        feature_matrix,
        dtype=float,
    )

    if feature_matrix.ndim != 2:
        raise ValueError("feature_matrix must be two dimensional.")

    if feature_matrix.shape[0] == 0:
        return (
            np.asarray([], dtype=int),
            np.asarray([], dtype=float).reshape(0, feature_matrix.shape[1]),
        )

    centers = initialize_kmeans_centers(
        feature_matrix=feature_matrix,
        cluster_count=cluster_count,
    )

    labels = np.zeros(
        feature_matrix.shape[0],
        dtype=int,
    )

    for _iteration_index in range(int(maximum_iterations)):
        distances = np.sum(
            (
                feature_matrix[:, None, :]
                - centers[None, :, :]
            )
            ** 2,
            axis=2,
        )

        next_labels = np.argmin(
            distances,
            axis=1,
        )

        next_centers = centers.copy()

        for cluster_index in range(int(cluster_count)):
            cluster_mask = next_labels == cluster_index

            if np.any(cluster_mask):
                next_centers[cluster_index] = np.mean(
                    feature_matrix[cluster_mask],
                    axis=0,
                )

        if np.array_equal(next_labels, labels) and np.allclose(
            next_centers,
            centers,
            rtol=1e-7,
            atol=1e-9,
        ):
            labels = next_labels
            centers = next_centers
            break

        labels = next_labels
        centers = next_centers

    return labels, centers


def initialize_kmeans_centers(
    *,
    feature_matrix: np.ndarray,
    cluster_count: int,
) -> np.ndarray:
    """
    Initialize K means centers deterministically along the x feature axis.
    """
    initialization_axis = feature_matrix[:, 0]

    quantile_positions = np.linspace(
        0.0,
        1.0,
        int(cluster_count) + 2,
    )[1:-1]

    center_indices = [
        int(
            np.argmin(
                np.abs(
                    initialization_axis
                    - np.quantile(
                        initialization_axis,
                        quantile_position,
                    )
                )
            )
        )
        for quantile_position in quantile_positions
    ]

    return feature_matrix[
        center_indices,
    ].copy()


def convert_kmeans_centers_to_peak_positions(
    *,
    labels: np.ndarray,
    centers: np.ndarray,
    feature_center: np.ndarray,
    feature_scale: np.ndarray,
    gated_x_axis_values: np.ndarray,
    gated_y_axis_values: np.ndarray,
    use_log_transform: bool,
    minimum_cluster_size: int,
) -> tuple[list[dict[str, float]], list[int], list[dict[str, np.ndarray]]]:
    """
    Convert standardized K means centers back to data coordinates.
    """
    peak_positions: list[dict[str, float]] = []
    cluster_sizes: list[int] = []
    grouped_points: list[dict[str, np.ndarray]] = []

    for cluster_index in range(centers.shape[0]):
        cluster_mask = labels == cluster_index

        cluster_size = int(
            np.count_nonzero(
                cluster_mask,
            )
        )

        if cluster_size < int(minimum_cluster_size):
            continue

        center_standardized = centers[
            cluster_index,
        ]

        center_feature = center_standardized * feature_scale + feature_center

        if use_log_transform:
            center_x = float(
                10.0 ** center_feature[0],
            )

            center_y = float(
                10.0 ** center_feature[1],
            )

        else:
            center_x = float(
                center_feature[0],
            )

            center_y = float(
                center_feature[1],
            )

        if not np.isfinite(center_x) or not np.isfinite(center_y):
            continue

        peak_positions.append(
            {
                "x": center_x,
                "y": center_y,
            }
        )

        cluster_sizes.append(
            cluster_size,
        )

        grouped_points.append(
            {
                "x_values": np.asarray(
                    gated_x_axis_values[cluster_mask],
                    dtype=float,
                ),
                "y_values": np.asarray(
                    gated_y_axis_values[cluster_mask],
                    dtype=float,
                ),
            }
        )

    return (
        peak_positions,
        cluster_sizes,
        grouped_points,
    )


def sort_peak_positions_by_x_axis(
    *,
    peak_positions: list[dict[str, float]],
    cluster_sizes: list[int],
    grouped_points: list[dict[str, np.ndarray]],
) -> tuple[list[dict[str, float]], list[int], list[dict[str, np.ndarray]]]:
    """
    Sort peak positions by increasing x coordinate.
    """
    order = np.argsort(
        [
            position["x"]
            for position in peak_positions
        ]
    )

    return (
        [
            peak_positions[int(index)]
            for index in order
        ],
        [
            cluster_sizes[int(index)]
            for index in order
        ],
        [
            grouped_points[int(index)]
            for index in order
        ],
    )


def downsample_points(
    *,
    x_values: Any,
    y_values: Any,
    maximum_size: int,
) -> dict[str, list[float]]:
    """
    Deterministically downsample 2D points for graph payloads.
    """
    x_values = np.asarray(
        x_values,
        dtype=float,
    ).reshape(-1)

    y_values = np.asarray(
        y_values,
        dtype=float,
    ).reshape(-1)

    common_size = min(
        x_values.size,
        y_values.size,
    )

    x_values = x_values[
        :common_size
    ]

    y_values = y_values[
        :common_size
    ]

    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)

    x_values = x_values[
        finite_mask
    ]

    y_values = y_values[
        finite_mask
    ]

    if x_values.size > int(maximum_size):
        indices = np.linspace(
            0,
            x_values.size - 1,
            int(maximum_size),
        ).astype(int)

        x_values = x_values[
            indices
        ]

        y_values = y_values[
            indices
        ]

    return {
        "x_values": x_values.tolist(),
        "y_values": y_values.tolist(),
    }


def build_empty_quantile_gated_kmeans_result() -> QuantileGatedKMeansResult:
    """
    Build an empty result.
    """
    return QuantileGatedKMeansResult(
        peak_positions=[],
        cluster_sizes=[],
        grouped_points=[],
        x_axis_lower_gate=0.0,
        x_axis_upper_gate=0.0,
        y_axis_lower_gate=0.0,
        y_axis_upper_gate=0.0,
        gated_event_count=0,
    )


PROCESS = QuantileGatedKMeans2DPeakProcess()