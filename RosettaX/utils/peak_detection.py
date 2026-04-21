# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from RosettaX.utils.clusterings import SigmaThresholdHDBSCAN
from RosettaX.utils.casting import _as_float


@dataclass(frozen=True)
class PeakDetectionResult:
    peak_positions: np.ndarray
    cluster_modes: np.ndarray
    cluster_means: np.ndarray
    cluster_sizes: np.ndarray
    n_points: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_positions": self.peak_positions.tolist(),
            "cluster_modes": self.cluster_modes.tolist(),
            "cluster_means": self.cluster_means.tolist(),
            "cluster_sizes": self.cluster_sizes.tolist(),
            "n_points": int(self.n_points),
        }


def find_1d_signal_peaks(
    *,
    values: np.ndarray,
    max_peaks: int,
    min_cluster_size: int = 100,
    threshold: float = 0.0,
    debug: bool = False,
) -> PeakDetectionResult:
    values = np.asarray(values, dtype=float).reshape(-1)
    values = values[np.isfinite(values)]

    if values.size == 0:
        return PeakDetectionResult(
            peak_positions=np.asarray([], dtype=float),
            cluster_modes=np.asarray([], dtype=float),
            cluster_means=np.asarray([], dtype=float),
            cluster_sizes=np.asarray([], dtype=int),
            n_points=0,
        )

    max_peaks = max(1, int(max_peaks))
    min_cluster_size = max(2, int(min_cluster_size))

    model = SigmaThresholdHDBSCAN()

    labels, means, modes, clean_data, clean_mask = model.fit(
        x=values,
        n_clusters=max_peaks,
        threshold_x=float(threshold),
        min_cluster_size=min_cluster_size,
        debug=debug,
    )

    labels = np.asarray(labels)
    means = np.atleast_1d(np.asarray(means, dtype=float).squeeze())
    modes = np.atleast_1d(np.asarray(modes, dtype=float).squeeze())

    if modes.size == 0:
        return PeakDetectionResult(
            peak_positions=np.asarray([], dtype=float),
            cluster_modes=np.asarray([], dtype=float),
            cluster_means=np.asarray([], dtype=float),
            cluster_sizes=np.asarray([], dtype=int),
            n_points=int(values.size),
        )

    valid_labels = labels[labels >= 0]
    if valid_labels.size == 0:
        return PeakDetectionResult(
            peak_positions=np.asarray([], dtype=float),
            cluster_modes=np.asarray([], dtype=float),
            cluster_means=np.asarray([], dtype=float),
            cluster_sizes=np.asarray([], dtype=int),
            n_points=int(values.size),
        )

    unique_labels, counts = np.unique(valid_labels, return_counts=True)
    size_by_label = {int(label): int(count) for label, count in zip(unique_labels, counts)}

    clusters: list[dict[str, Any]] = []
    for index in range(int(modes.size)):
        mode_value = float(modes[index])

        if not np.isfinite(mode_value):
            continue

        mean_value = float(means[index]) if index < means.size and np.isfinite(means[index]) else float("nan")
        label = int(index)
        cluster_size = int(size_by_label.get(label, 0))

        if cluster_size <= 0:
            continue

        clusters.append(
            {
                "label": label,
                "mode": mode_value,
                "mean": mean_value,
                "size": cluster_size,
            }
        )

    if not clusters:
        return PeakDetectionResult(
            peak_positions=np.asarray([], dtype=float),
            cluster_modes=np.asarray([], dtype=float),
            cluster_means=np.asarray([], dtype=float),
            cluster_sizes=np.asarray([], dtype=int),
            n_points=int(values.size),
        )

    clusters.sort(key=lambda cluster: cluster["size"], reverse=True)
    clusters = clusters[:max_peaks]
    clusters.sort(key=lambda cluster: cluster["mode"])

    peak_positions = np.asarray([float(cluster["mode"]) for cluster in clusters], dtype=float)
    cluster_means = np.asarray([float(cluster["mean"]) for cluster in clusters], dtype=float)
    cluster_sizes = np.asarray([int(cluster["size"]) for cluster in clusters], dtype=int)

    return PeakDetectionResult(
        peak_positions=peak_positions,
        cluster_modes=peak_positions.copy(),
        cluster_means=cluster_means,
        cluster_sizes=cluster_sizes,
        n_points=int(values.size),
    )


def inject_peak_positions_into_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[float] | np.ndarray,
    peak_column_id: str,
    default_row_factory,
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in (table_data or [])]

    resolved_peak_positions = np.asarray(peak_positions, dtype=float).reshape(-1)
    resolved_peak_positions = resolved_peak_positions[np.isfinite(resolved_peak_positions)]

    while len(rows) < int(resolved_peak_positions.size):
        rows.append(default_row_factory())

    for row_index, peak_position in enumerate(resolved_peak_positions):
        current_value = rows[row_index].get(peak_column_id, "")
        if current_value is None or str(current_value).strip() == "":
            rows[row_index][peak_column_id] = f"{float(peak_position):.6g}"

    return rows