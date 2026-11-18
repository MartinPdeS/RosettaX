"""Common numerical operations for histogram and K-means peak scripts."""

import numpy as np


def compute_quantile_gate(
    *, values: np.ndarray, lower_quantile: float, upper_quantile: float,
) -> tuple[float, float]:
    """Compute a quantile gate after excluding nonfinite detector values.

    Parameters
    ----------
    values : numpy.ndarray
        Detector intensities, shape (n,).
    lower_quantile, upper_quantile : float
        Quantile fractions in [0, 1].

    Returns
    -------
    tuple[float, float]
        Gate limits in detector units, or (0, 0) for empty finite input.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 0.0, 0.0
    lower_gate, upper_gate = np.quantile(values, [lower_quantile, upper_quantile])
    return float(lower_gate), float(upper_gate)


def standardize_feature_matrix(
    *, feature_matrix: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Center features by their medians and scale by standard deviations.

    Parameters
    ----------
    feature_matrix : numpy.ndarray
        Finite feature values, shape (n, d).

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        Standardized values (n, d), centers (d,), and scales (d,).
        Constant columns use a scale of one.
    """
    feature_center = np.median(feature_matrix, axis=0)
    feature_scale = np.std(feature_matrix, axis=0)
    feature_scale = np.where(feature_scale > 0.0, feature_scale, 1.0)
    standardized_feature_matrix = (feature_matrix - feature_center) / feature_scale
    return standardized_feature_matrix, feature_center, feature_scale


def run_kmeans(
    *, feature_matrix: np.ndarray, cluster_count: int, maximum_iterations: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit deterministic K-means without replacing centers of empty clusters.

    Parameters
    ----------
    feature_matrix : numpy.ndarray
        Finite feature values, shape (n, d).
    cluster_count : int
        Positive number of clusters.
    maximum_iterations : int
        Maximum number of label and center updates.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Integer labels (n,) and centers (cluster_count, d). Empty input
        returns empty labels and centers of shape (0, d).
    """
    feature_matrix = np.asarray(feature_matrix, dtype=float)
    if feature_matrix.ndim != 2:
        raise ValueError("feature_matrix must be two dimensional.")
    if feature_matrix.shape[0] == 0:
        return np.asarray([], dtype=int), np.asarray([], dtype=float).reshape(0, feature_matrix.shape[1])

    centers = initialize_kmeans_centers(feature_matrix=feature_matrix, cluster_count=cluster_count)
    labels = np.zeros(feature_matrix.shape[0], dtype=int)
    for _iteration_index in range(int(maximum_iterations)):
        distances = np.sum((feature_matrix[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        next_labels = np.argmin(distances, axis=1)
        next_centers = centers.copy()
        for cluster_index in range(int(cluster_count)):
            cluster_mask = next_labels == cluster_index
            if np.any(cluster_mask):
                next_centers[cluster_index] = np.mean(feature_matrix[cluster_mask], axis=0)
        converged = np.array_equal(next_labels, labels) and np.allclose(
            next_centers, centers, rtol=1e-7, atol=1e-9,
        )
        labels, centers = next_labels, next_centers
        if converged:
            break
    return labels, centers


def initialize_kmeans_centers(
    *, feature_matrix: np.ndarray, cluster_count: int,
) -> np.ndarray:
    """Choose initial rows nearest evenly spaced quantiles of the first feature.

    Parameters
    ----------
    feature_matrix : numpy.ndarray
        Nonempty finite features, shape (n, d), with d >= 1.
    cluster_count : int
        Positive number of initial centers.

    Returns
    -------
    numpy.ndarray
        Copied feature rows, shape (cluster_count, d).
    """
    initialization_axis = feature_matrix[:, 0]
    quantile_positions = np.linspace(0.0, 1.0, int(cluster_count) + 2)[1:-1]
    center_indices = [
        int(np.argmin(np.abs(initialization_axis - np.quantile(initialization_axis, quantile_position))))
        for quantile_position in quantile_positions
    ]
    return feature_matrix[center_indices].copy()


def inverse_transform_position(
    *, transformed_position: float, use_log_transform: bool,
) -> float:
    """Convert a peak center back to its detector intensity units.

    Parameters
    ----------
    transformed_position : float
        Peak center on the linear or log10 detection axis.
    use_log_transform : bool
        Whether the detection axis uses log10 intensities.

    Returns
    -------
    float
        Peak center in original detector units.
    """
    return float(10.0 ** float(transformed_position)) if use_log_transform else float(transformed_position)
