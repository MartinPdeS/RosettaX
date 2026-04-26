# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import BasePeakProcess
from .base import PeakProcessResult
from RosettaX.utils.io import column_copy


logger = logging.getLogger(__name__)


class QuantileGatedKMeans2DPeakProcess(BasePeakProcess):
    """
    Quantile gated 2D K means peak registration.

    The process gates events on both axes using lower and upper quantiles, then
    runs K means on the remaining two dimensional cloud.

    The table receives only the x coordinate of each detected center through the
    page adapter. The graph receives the full 2D centers and the gate thresholds.
    """

    process_name = "Quantile gated K means 2D peaks"
    process_label = "Quantile gated K means 2D peaks"
    description = (
        "Gate events on both axes using quantiles, then run K means on the "
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

        This is used only if the layout builder supports process provided labels.
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
                "default_value": 0.001,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
            },
            {
                "name": "x_axis_upper_gate_quantile",
                "label": "X axis upper gate quantile",
                "kind": "float",
                "default_value": 0.999,
                "min_value": 0.501,
                "max_value": 1.0,
                "step": 0.001,
            },
            {
                "name": "y_axis_lower_gate_quantile",
                "label": "Y axis lower gate quantile",
                "kind": "float",
                "default_value": 0.90,
                "min_value": 0.0,
                "max_value": 0.999,
                "step": 0.01,
            },
            {
                "name": "y_axis_upper_gate_quantile",
                "label": "Y axis upper gate quantile",
                "kind": "float",
                "default_value": 0.999,
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

        if backend is None:
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="The backend does not expose column_copy.",
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
            x_axis_lower_gate=result.x_axis_lower_gate,
            x_axis_upper_gate=result.x_axis_upper_gate,
            y_axis_lower_gate=result.y_axis_lower_gate,
            y_axis_upper_gate=result.y_axis_upper_gate,
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
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
        cluster_sizes: list[int],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        y_axis_lower_gate: float,
        y_axis_upper_gate: float,
    ) -> dict[str, Any]:
        """
        Build graph annotation payload.
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

        return {
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
            "x_axis_lower_gate": float(x_axis_lower_gate),
            "x_axis_upper_gate": float(x_axis_upper_gate),
            "y_axis_lower_gate": float(y_axis_lower_gate),
            "y_axis_upper_gate": float(y_axis_upper_gate),
        }


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
    ) -> None:
        self.cluster_count = cluster_count
        self.minimum_cluster_size = minimum_cluster_size
        self.x_axis_lower_gate_quantile = x_axis_lower_gate_quantile
        self.x_axis_upper_gate_quantile = x_axis_upper_gate_quantile
        self.y_axis_lower_gate_quantile = y_axis_lower_gate_quantile
        self.y_axis_upper_gate_quantile = y_axis_upper_gate_quantile
        self.maximum_iterations = maximum_iterations
        self.use_log_transform = use_log_transform

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
            default=0.001,
            minimum=0.0,
            maximum=0.499,
        )

        x_axis_upper_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="x_axis_upper_gate_quantile",
            default=0.999,
            minimum=0.501,
            maximum=1.0,
        )

        y_axis_lower_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="y_axis_lower_gate_quantile",
            default=0.90,
            minimum=0.0,
            maximum=0.999,
        )

        y_axis_upper_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="y_axis_upper_gate_quantile",
            default=0.999,
            minimum=0.501,
            maximum=1.0,
        )

        if x_axis_lower_gate_quantile >= x_axis_upper_gate_quantile:
            x_axis_lower_gate_quantile = 0.001
            x_axis_upper_gate_quantile = 0.999

        if y_axis_lower_gate_quantile >= y_axis_upper_gate_quantile:
            y_axis_lower_gate_quantile = 0.90
            y_axis_upper_gate_quantile = 0.999

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
            f"use_log_transform={self.use_log_transform!r})"
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
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        y_axis_lower_gate: float,
        y_axis_upper_gate: float,
        gated_event_count: int,
    ) -> None:
        self.peak_positions = peak_positions
        self.cluster_sizes = cluster_sizes
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

    peak_positions, cluster_sizes = convert_kmeans_centers_to_peak_positions(
        labels=labels,
        centers=centers,
        feature_center=feature_center,
        feature_scale=feature_scale,
        use_log_transform=settings.use_log_transform,
        minimum_cluster_size=settings.minimum_cluster_size,
    )

    peak_positions, cluster_sizes = sort_peak_positions_by_x_axis(
        peak_positions=peak_positions,
        cluster_sizes=cluster_sizes,
    )

    return QuantileGatedKMeansResult(
        peak_positions=peak_positions,
        cluster_sizes=cluster_sizes,
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
        raise ValueError(
            "feature_matrix must be two dimensional."
        )

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

        if np.array_equal(
            next_labels,
            labels,
        ) and np.allclose(
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
    use_log_transform: bool,
    minimum_cluster_size: int,
) -> tuple[list[dict[str, float]], list[int]]:
    """
    Convert standardized K means centers back to data coordinates.
    """
    peak_positions: list[dict[str, float]] = []
    cluster_sizes: list[int] = []

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

    return peak_positions, cluster_sizes


def sort_peak_positions_by_x_axis(
    *,
    peak_positions: list[dict[str, float]],
    cluster_sizes: list[int],
) -> tuple[list[dict[str, float]], list[int]]:
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
    )


def build_empty_quantile_gated_kmeans_result() -> QuantileGatedKMeansResult:
    """
    Build an empty result.
    """
    return QuantileGatedKMeansResult(
        peak_positions=[],
        cluster_sizes=[],
        x_axis_lower_gate=0.0,
        x_axis_upper_gate=0.0,
        y_axis_lower_gate=0.0,
        y_axis_upper_gate=0.0,
        gated_event_count=0,
    )


def resolve_integer_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve an integer process setting.
    """
    return resolve_integer_value(
        value=settings.get(
            name,
        ),
        default=default,
        minimum=minimum,
        maximum=maximum,
    )


def resolve_float_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Resolve a bounded float process setting.
    """
    try:
        resolved_value = float(
            settings.get(
                name,
                default,
            )
        )

    except (TypeError, ValueError):
        resolved_value = float(
            default,
        )

    if not np.isfinite(
        resolved_value,
    ):
        resolved_value = float(
            default,
        )

    resolved_value = max(
        float(minimum),
        resolved_value,
    )

    resolved_value = min(
        float(maximum),
        resolved_value,
    )

    return resolved_value


def resolve_integer_value(
    *,
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve a bounded integer value.
    """
    try:
        resolved_value = int(
            value,
        )

    except (TypeError, ValueError):
        resolved_value = int(
            default,
        )

    resolved_value = max(
        int(minimum),
        resolved_value,
    )

    resolved_value = min(
        int(maximum),
        resolved_value,
    )

    return resolved_value


def resolve_yes_no_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: bool,
) -> bool:
    """
    Resolve a yes or no setting.
    """
    value = settings.get(
        name,
        None,
    )

    if value is None:
        return bool(
            default,
        )

    if isinstance(value, bool):
        return value

    return str(
        value,
    ).strip().lower() in (
        "yes",
        "true",
        "1",
        "on",
        "enabled",
    )


def deduplicate_2d_peak_positions(
    *,
    peak_positions: list[dict[str, float]],
    decimal_places: int = 12,
) -> list[dict[str, float]]:
    """
    Remove duplicate 2D peak positions while preserving order.
    """
    unique_peak_positions: list[dict[str, float]] = []
    seen_keys: set[tuple[float, float]] = set()

    for peak_position in peak_positions:
        try:
            x_value = float(
                peak_position["x"],
            )

            y_value = float(
                peak_position["y"],
            )

        except (KeyError, TypeError, ValueError):
            continue

        key = (
            round(
                x_value,
                int(decimal_places),
            ),
            round(
                y_value,
                int(decimal_places),
            ),
        )

        if key in seen_keys:
            continue

        seen_keys.add(
            key,
        )

        unique_peak_positions.append(
            {
                "x": x_value,
                "y": y_value,
            }
        )

    return unique_peak_positions


PROCESS = QuantileGatedKMeans2DPeakProcess()