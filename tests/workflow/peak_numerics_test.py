"""Check shared peak numerics against simple independent numerical examples."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import numpy as np
import pytest
from RosettaX.workflow.peak.scripts._numerics import (
    compute_quantile_gate,
    inverse_transform_position,
    run_kmeans,
    standardize_feature_matrix,
)


@pytest.mark.parametrize("dimensions", [1, 2])
def test_kmeans_recovers_separated_populations(dimensions):
    """Recover known population means and memberships in one and two dimensions."""
    values = np.array([[0.0], [2.0], [10.0], [12.0]])
    if dimensions == 2:
        values = np.column_stack((values[:, 0], [5.0, 7.0, 15.0, 17.0]))
    labels, centers = run_kmeans(feature_matrix=values, cluster_count=2, maximum_iterations=100)
    np.testing.assert_array_equal(labels, [0, 0, 1, 1])
    np.testing.assert_allclose(centers, [[1.0], [11.0]] if dimensions == 1 else [[1.0, 6.0], [11.0, 16.0]])


def test_empty_kmeans_preserves_feature_dimensions():
    """An empty input produces no labels or centers without losing dimensions."""
    labels, centers = run_kmeans(feature_matrix=np.empty((0, 2)), cluster_count=2, maximum_iterations=10)
    assert labels.shape == (0,)
    assert centers.shape == (0, 2)


def test_quantile_gate_ignores_nonfinite_intensities():
    """Known finite quantiles are unaffected by NaN or infinite values."""
    assert compute_quantile_gate(
        values=np.array([0, 4, 8, 12, 16, np.nan, np.inf]), lower_quantile=0.25, upper_quantile=0.75,
    ) == (4.0, 12.0)


def test_standardization_retains_constant_features_and_reverses_scaling():
    """Constant features stay finite and the returned scaling recovers input units."""
    values = np.array([[1.0, 7.0], [3.0, 7.0], [8.0, 7.0]])
    standardized, center, scale = standardize_feature_matrix(feature_matrix=values)
    np.testing.assert_allclose(center, [3.0, 7.0])
    np.testing.assert_allclose(standardized[:, 1], 0.0)
    assert scale[1] == 1.0
    np.testing.assert_allclose(standardized * scale + center, values)
    assert inverse_transform_position(transformed_position=2.0, use_log_transform=True) == 100.0
    assert inverse_transform_position(transformed_position=2.0, use_log_transform=False) == 2.0
