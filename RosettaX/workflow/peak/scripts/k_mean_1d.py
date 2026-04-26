# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import BasePeakProcess, PeakProcessResult
from RosettaX.utils.io import column_copy


logger = logging.getLogger(__name__)


class QuantileGatedKMeans1DPeakProcess(BasePeakProcess):
    """
    Quantile gated 1D K means peak registration.

    The process gates events on one detector axis using lower and upper
    quantiles, then runs K means on the remaining one dimensional values.

    The table receives the detected cluster centers. The graph receives peak
    positions, gate thresholds, cluster sizes, and optional grouped values that
    can be rendered with different colors if the graph layer supports grouped
    traces.
    """

    process_name = "Gated K-means 1D"
    process_label = "Gated K-means 1D peaks"
    description = (
        "Gate events on one detector axis using quantiles, then run K-means on "
        "the remaining 1D values."
    )
    graph_type = "1d_histogram"
    sort_order = 45

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
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """
        Return user visible detector labels.
        """
        return {
            "x_axis": "Signal channel",
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
                "default_value": 3,
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
                "label": "Lower gate quantile",
                "kind": "float",
                "default_value": 0.001,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
            },
            {
                "name": "x_axis_upper_gate_quantile",
                "label": "Upper gate quantile",
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
                "label": "Max grouped values per cluster",
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
        Run quantile gated 1D K means.
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

        if not str(x_axis_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a signal channel first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        settings = QuantileGatedKMeans1DSettings.from_process_settings(
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

        result = compute_quantile_gated_kmeans_1d_peaks(
            x_axis_values=x_axis_values,
            settings=settings,
        )

        peak_positions = deduplicate_1d_peak_positions(
            peak_positions=result.peak_positions,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=peak_positions,
            cluster_sizes=result.cluster_sizes,
            x_axis_lower_gate=result.x_axis_lower_gate,
            x_axis_upper_gate=result.x_axis_upper_gate,
            grouped_values=result.grouped_values,
            include_group_values=settings.include_group_values,
            maximum_group_values_per_cluster=settings.maximum_group_values_per_cluster,
        )

        status = (
            f"Quantile gated K means found {len(peak_positions)} cluster center(s) "
            f"from {result.gated_event_count} gated event(s). "
            f"Gate=[{result.x_axis_lower_gate:.6g}, {result.x_axis_upper_gate:.6g}]."
        )

        logger.debug(
            "Quantile gated 1D K means completed with x_axis_column=%r "
            "settings=%r gated_event_count=%r peak_positions=%r",
            x_axis_column,
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
            "points": [],
            "labels": [],
            "cluster_sizes": [],
            "group_values": [],
            "group_labels": [],
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
        cluster_sizes: list[int],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        grouped_values: list[np.ndarray],
        include_group_values: bool,
        maximum_group_values_per_cluster: int,
    ) -> dict[str, Any]:
        """
        Build graph annotation payload.

        ``group_values`` and ``group_labels`` are included so the graph builder
        can render each K means cluster with a different color.
        """
        labels = [
            f"K means cluster {index + 1} | n={cluster_sizes[index]}"
            if index < len(cluster_sizes)
            else f"K means cluster {index + 1}"
            for index in range(len(peak_positions))
        ]

        payload = {
            "positions": [
                float(position)
                for position in peak_positions
            ],
            "x_positions": [
                float(position)
                for position in peak_positions
            ],
            "points": [
                {
                    "x": float(position),
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
            "group_values": [],
            "group_labels": [],
        }

        if include_group_values:
            payload["group_values"] = [
                downsample_values(
                    values=grouped_values[index],
                    maximum_size=maximum_group_values_per_cluster,
                ).tolist()
                for index in range(len(grouped_values))
            ]
            payload["group_labels"] = labels

        return payload


class QuantileGatedKMeans1DSettings:
    """
    Settings for quantile gated 1D K means.
    """

    def __init__(
        self,
        *,
        cluster_count: int,
        minimum_cluster_size: int,
        x_axis_lower_gate_quantile: float,
        x_axis_upper_gate_quantile: float,
        maximum_iterations: int,
        use_log_transform: bool,
        include_group_values: bool,
        maximum_group_values_per_cluster: int,
    ) -> None:
        self.cluster_count = cluster_count
        self.minimum_cluster_size = minimum_cluster_size
        self.x_axis_lower_gate_quantile = x_axis_lower_gate_quantile
        self.x_axis_upper_gate_quantile = x_axis_upper_gate_quantile
        self.maximum_iterations = maximum_iterations
        self.use_log_transform = use_log_transform
        self.include_group_values = include_group_values
        self.maximum_group_values_per_cluster = maximum_group_values_per_cluster

    @classmethod
    def from_process_settings(
        cls,
        *,
        process_settings: dict[str, Any],
    ) -> "QuantileGatedKMeans1DSettings":
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

        if x_axis_lower_gate_quantile >= x_axis_upper_gate_quantile:
            x_axis_lower_gate_quantile = 0.001
            x_axis_upper_gate_quantile = 0.999

        return cls(
            cluster_count=resolve_integer_setting(
                settings=process_settings,
                name="cluster_count",
                default=3,
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
            "QuantileGatedKMeans1DSettings("
            f"cluster_count={self.cluster_count!r}, "
            f"minimum_cluster_size={self.minimum_cluster_size!r}, "
            f"x_axis_lower_gate_quantile={self.x_axis_lower_gate_quantile!r}, "
            f"x_axis_upper_gate_quantile={self.x_axis_upper_gate_quantile!r}, "
            f"maximum_iterations={self.maximum_iterations!r}, "
            f"use_log_transform={self.use_log_transform!r}, "
            f"include_group_values={self.include_group_values!r}, "
            f"maximum_group_values_per_cluster={self.maximum_group_values_per_cluster!r})"
        )


class QuantileGatedKMeans1DResult:
    """
    Result from quantile gated 1D K means.
    """

    def __init__(
        self,
        *,
        peak_positions: list[float],
        cluster_sizes: list[int],
        grouped_values: list[np.ndarray],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        gated_event_count: int,
    ) -> None:
        self.peak_positions = peak_positions
        self.cluster_sizes = cluster_sizes
        self.grouped_values = grouped_values
        self.x_axis_lower_gate = x_axis_lower_gate
        self.x_axis_upper_gate = x_axis_upper_gate
        self.gated_event_count = gated_event_count


def compute_quantile_gated_kmeans_1d_peaks(
    *,
    x_axis_values: Any,
    settings: QuantileGatedKMeans1DSettings,
) -> QuantileGatedKMeans1DResult:
    """
    Compute K means centers after 1D quantile gating.
    """
    original_x_axis_values, transformed_x_axis_values = prepare_axis_values(
        x_axis_values=x_axis_values,
        use_log_transform=settings.use_log_transform,
    )

    if original_x_axis_values.size == 0:
        return build_empty_quantile_gated_kmeans_1d_result()

    x_axis_lower_gate, x_axis_upper_gate = compute_quantile_gate(
        values=original_x_axis_values,
        lower_quantile=settings.x_axis_lower_gate_quantile,
        upper_quantile=settings.x_axis_upper_gate_quantile,
    )

    gate_mask = (
        (original_x_axis_values >= x_axis_lower_gate)
        & (original_x_axis_values <= x_axis_upper_gate)
    )

    gated_original_x_axis_values = original_x_axis_values[
        gate_mask
    ]

    gated_transformed_x_axis_values = transformed_x_axis_values[
        gate_mask
    ]

    if gated_original_x_axis_values.size == 0:
        return QuantileGatedKMeans1DResult(
            peak_positions=[],
            cluster_sizes=[],
            grouped_values=[],
            x_axis_lower_gate=float(x_axis_lower_gate),
            x_axis_upper_gate=float(x_axis_upper_gate),
            gated_event_count=0,
        )

    feature_matrix = gated_transformed_x_axis_values.reshape(
        -1,
        1,
    )

    standardized_feature_matrix, feature_center, feature_scale = standardize_feature_matrix(
        feature_matrix=feature_matrix,
    )

    resolved_cluster_count = min(
        int(settings.cluster_count),
        standardized_feature_matrix.shape[0],
    )

    if resolved_cluster_count <= 0:
        return QuantileGatedKMeans1DResult(
            peak_positions=[],
            cluster_sizes=[],
            grouped_values=[],
            x_axis_lower_gate=float(x_axis_lower_gate),
            x_axis_upper_gate=float(x_axis_upper_gate),
            gated_event_count=int(gated_original_x_axis_values.size),
        )

    labels, centers = run_kmeans(
        feature_matrix=standardized_feature_matrix,
        cluster_count=resolved_cluster_count,
        maximum_iterations=settings.maximum_iterations,
    )

    peak_positions, cluster_sizes, grouped_values = convert_kmeans_centers_to_peak_positions(
        labels=labels,
        centers=centers,
        feature_center=feature_center,
        feature_scale=feature_scale,
        gated_original_x_axis_values=gated_original_x_axis_values,
        use_log_transform=settings.use_log_transform,
        minimum_cluster_size=settings.minimum_cluster_size,
    )

    peak_positions, cluster_sizes, grouped_values = sort_peak_positions_by_value(
        peak_positions=peak_positions,
        cluster_sizes=cluster_sizes,
        grouped_values=grouped_values,
    )

    return QuantileGatedKMeans1DResult(
        peak_positions=peak_positions,
        cluster_sizes=cluster_sizes,
        grouped_values=grouped_values,
        x_axis_lower_gate=float(x_axis_lower_gate),
        x_axis_upper_gate=float(x_axis_upper_gate),
        gated_event_count=int(gated_original_x_axis_values.size),
    )


def prepare_axis_values(
    *,
    x_axis_values: Any,
    use_log_transform: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert event coordinates to finite NumPy arrays.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Original finite values and transformed values used for clustering.
    """
    original_x_axis_values = np.asarray(
        x_axis_values,
        dtype=float,
    )

    finite_mask = np.isfinite(
        original_x_axis_values,
    )

    if use_log_transform:
        finite_mask = finite_mask & (
            original_x_axis_values > 0.0
        )

    original_x_axis_values = original_x_axis_values[
        finite_mask
    ]

    if use_log_transform:
        transformed_x_axis_values = np.log10(
            original_x_axis_values,
        )
    else:
        transformed_x_axis_values = original_x_axis_values.copy()

    return (
        original_x_axis_values,
        transformed_x_axis_values,
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
    Initialize K means centers deterministically along the 1D feature axis.
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
    gated_original_x_axis_values: np.ndarray,
    use_log_transform: bool,
    minimum_cluster_size: int,
) -> tuple[list[float], list[int], list[np.ndarray]]:
    """
    Convert standardized K means centers back to data coordinates.
    """
    peak_positions: list[float] = []
    cluster_sizes: list[int] = []
    grouped_values: list[np.ndarray] = []

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
        else:
            center_x = float(
                center_feature[0],
            )

        if not np.isfinite(center_x):
            continue

        peak_positions.append(
            center_x,
        )

        cluster_sizes.append(
            cluster_size,
        )

        grouped_values.append(
            np.asarray(
                gated_original_x_axis_values[cluster_mask],
                dtype=float,
            )
        )

    return (
        peak_positions,
        cluster_sizes,
        grouped_values,
    )


def sort_peak_positions_by_value(
    *,
    peak_positions: list[float],
    cluster_sizes: list[int],
    grouped_values: list[np.ndarray],
) -> tuple[list[float], list[int], list[np.ndarray]]:
    """
    Sort peak positions by increasing value.
    """
    order = np.argsort(
        peak_positions,
    )

    return (
        [
            float(peak_positions[int(index)])
            for index in order
        ],
        [
            int(cluster_sizes[int(index)])
            for index in order
        ],
        [
            grouped_values[int(index)]
            for index in order
        ],
    )


def downsample_values(
    *,
    values: Any,
    maximum_size: int,
) -> np.ndarray:
    """
    Deterministically downsample values for graph payloads.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

    if values.size <= int(maximum_size):
        return values

    indices = np.linspace(
        0,
        values.size - 1,
        int(maximum_size),
    ).astype(int)

    return values[
        indices
    ]


def build_empty_quantile_gated_kmeans_1d_result() -> QuantileGatedKMeans1DResult:
    """
    Build an empty result.
    """
    return QuantileGatedKMeans1DResult(
        peak_positions=[],
        cluster_sizes=[],
        grouped_values=[],
        x_axis_lower_gate=0.0,
        x_axis_upper_gate=0.0,
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


def deduplicate_1d_peak_positions(
    *,
    peak_positions: list[float],
    decimal_places: int = 12,
) -> list[float]:
    """
    Remove duplicate 1D peak positions while preserving order.
    """
    unique_peak_positions: list[float] = []
    seen_keys: set[float] = set()

    for peak_position in peak_positions:
        try:
            x_value = float(
                peak_position,
            )

        except (TypeError, ValueError):
            continue

        if not np.isfinite(
            x_value,
        ):
            continue

        key = round(
            x_value,
            int(decimal_places),
        )

        if key in seen_keys:
            continue

        seen_keys.add(
            key,
        )

        unique_peak_positions.append(
            x_value,
        )

    return unique_peak_positions


PROCESS = QuantileGatedKMeans1DPeakProcess()