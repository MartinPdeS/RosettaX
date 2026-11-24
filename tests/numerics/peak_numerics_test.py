"""Check shared peak numerics against simple independent numerical examples."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import numpy as np
import pandas as pd
import pytest
from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.peak.scripts._events import (
    filter_finite_peak_events,
    read_peak_event_columns,
)
from RosettaX.workflow.peak.scripts._numerics import (
    compute_quantile_gate,
    inverse_transform_position,
    run_kmeans,
    standardize_feature_matrix,
)
from RosettaX.workflow.peak.scripts.manual_1d_click import Manual1DClickProcess
from RosettaX.workflow.peak.scripts.manual_2d_click import Manual2DClickProcess


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


def test_paired_event_read_preserves_prefix_alignment_and_filter_count(tmp_path):
    """Read the same event limit and remove whole rows with invalid channel values."""
    signals = {"scatter": [12.0, np.nan, 35.0, 46.0], "green": [120.0, 230.0, np.inf, 460.0]}

    path = tmp_path / "paired.fcs"
    FCSFile.builder_from_dataframe(pd.DataFrame(signals)).write(path)
    columns = read_peak_event_columns(fcs_file_path=str(path), detector_columns=("scatter", "green"), max_events=3)
    (scatter, green), removed = filter_finite_peak_events(columns=columns)
    np.testing.assert_array_equal(scatter, [12.0])
    np.testing.assert_array_equal(green, [120.0])
    assert removed == 2
    with pytest.raises(ValueError, match="paired FCS events"):
        filter_finite_peak_events(columns=(scatter, np.array([12.0, 24.0])))


def test_manual_selectors_ignore_nonfinite_and_incomplete_plot_points():
    """Require complete coordinates for a two-axis selection and a finite click."""
    one_dimension = Manual1DClickProcess()
    two_dimensions = Manual2DClickProcess()
    assert one_dimension.extract_clicked_x_position({"points": [{"x": np.nan}]}) is None
    assert two_dimensions.extract_clicked_xy_position({"points": [{"x": 2, "y": np.inf}]}) is None
    selection = {"points": [{"x": 1, "y": 3}, {"x": 2, "y": 4}, {"x": 100}, {"x": 5, "y": np.nan}]}
    assert one_dimension.extract_selected_x_range(selection) == (1, 100)
    assert two_dimensions.extract_selected_xy_range(selection) == {"x": (1, 2), "y": (3, 4)}


def test_manual_1d_snap_climbs_the_local_histogram_peak():
    """Select a local peak even when another interval has a larger peak."""
    edges = np.arange(7, dtype=float)
    position = Manual1DClickProcess()._climb_histogram_peak_1d(
        counts=np.array([1, 4, 9, 3, 2, 20]),
        edges=edges, centers=edges[:-1] + 0.5, clicked_value=1.5,
    )
    assert position == 2.5


def test_manual_2d_snap_uses_the_densest_bin_inside_the_selection():
    """Exclude a higher count outside the chosen scatter region."""
    position = Manual2DClickProcess()._find_histogram_peak_in_selected_range_2d(
        histogram=np.array([[1, 3, 100], [2, 12, 80], [4, 5, 60]]),
        x_centers=np.array([10, 20, 30]), y_centers=np.array([1, 2, 3]),
        selected_xy_range={"x": (5, 25), "y": (0.5, 2.5)}, fallback_point={"x": 15, "y": 1.5},
    )
    assert position == {"x": 20.0, "y": 2.0}
