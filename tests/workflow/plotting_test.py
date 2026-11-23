"""Regression tests for workflow plotting."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import numpy as np
import pytest
from RosettaX.workflow.plotting.models import (
    AxisOptions,
    HistogramOptions,
    PlotStyleOptions,
    ScatterOptions,
    SmoothedHistogramOptions,
    SmoothingOptions,
)
from RosettaX.workflow.plotting.transforms import (
    build_histogram_arrays,
    compute_2d_density_values,
    finite_plot_values,
    smooth_histogram_counts,
)


class TestPlottingModels:
    """Test double for test plotting models."""

    def test_plot_options_validate_shared_controls(self) -> None:
        """Check plot options validate shared controls."""
        assert HistogramOptions(bin_count=12, axes=AxisOptions(x_log=True)).bin_count == 12
        assert SmoothingOptions(sigma_points=0.0).sigma_points == 0.0
        assert ScatterOptions(marker_size=4.0, marker_opacity=0.5).marker_size == 4.0
        assert SmoothedHistogramOptions().smoothing.sigma_points == 2.0
        assert PlotStyleOptions(show_grid=False).show_grid is False

    @pytest.mark.parametrize(
        ("factory", "value", "message"),
        [
            (HistogramOptions, {"bin_count": 0}, "bin_count"),
            (SmoothingOptions, {"sigma_points": -1}, "sigma_points"),
            (ScatterOptions, {"marker_size": 0}, "marker_size"),
            (ScatterOptions, {"marker_opacity": 2}, "marker_opacity"),
            (HistogramOptions, {"max_events": 0}, "max_events"),
            (ScatterOptions, {"density_bin_count": 0}, "density_bin_count"),
            (PlotStyleOptions, {"marker_opacity": 2}, "marker_opacity"),
        ],
    )
    def test_plot_options_reject_invalid_values(self, factory, value, message) -> None:
        """Check plot options reject invalid values."""
        with pytest.raises(ValueError, match=message):
            factory(**value)


class TestPlottingTransforms:
    """Test double for test plotting transforms."""

    def test_finite_plot_values_filters_nonfinite_and_nonpositive_values(self) -> None:
        """Check finite plot values filters nonfinite and nonpositive values."""
        values = finite_plot_values([1.0, np.nan, -2.0, np.inf, 3.0])
        positive_values = finite_plot_values(
            [1.0, np.nan, -2.0, np.inf, 3.0],
            positive_only=True,
        )

        np.testing.assert_array_equal(values, [1.0, -2.0, 3.0])
        np.testing.assert_array_equal(positive_values, [1.0, 3.0])

    def test_build_histogram_arrays_supports_linear_and_log_bins(self) -> None:
        """Check build histogram arrays supports linear and log bins."""
        linear_counts, linear_edges, linear_centers = build_histogram_arrays(
            [1.0, 2.0, 3.0, 4.0],
            bin_count=4,
        )
        log_counts, log_edges, log_centers = build_histogram_arrays(
            [1.0, 10.0, 100.0],
            bin_count=2,
            log_x=True,
        )

        assert linear_counts.size == 4
        assert linear_edges.size == 5
        assert linear_centers.size == 4
        assert log_counts.size == 2
        assert log_edges[0] == pytest.approx(1.0)
        assert log_edges[-1] == pytest.approx(100.0)
        assert np.all(log_centers > 0.0)

    def test_build_histogram_arrays_rejects_empty_log_input(self) -> None:
        """Check build histogram arrays rejects empty log input."""
        with pytest.raises(ValueError, match="positive"):
            build_histogram_arrays([-2.0, 0.0, np.nan], bin_count=4, log_x=True)

    def test_smooth_histogram_counts_preserves_shape_and_zero_sigma(self) -> None:
        """Check smooth histogram counts preserves shape and zero sigma."""
        counts = np.asarray([0.0, 4.0, 0.0, 2.0, 0.0])

        unchanged = smooth_histogram_counts(counts, sigma_points=0.0)
        smoothed = smooth_histogram_counts(counts, sigma_points=1.0)

        np.testing.assert_array_equal(unchanged, counts)
        assert smoothed.shape == counts.shape
        assert not np.array_equal(smoothed, counts)
        assert np.all(np.isfinite(smoothed))


@pytest.mark.parametrize("log_x", [False, True])
@pytest.mark.parametrize("log_y", [False, True])
@pytest.mark.parametrize("log_color", [False, True])
def test_density_matches_histogram_with_invalid_pairs_and_bin_edges(log_x, log_y, log_color):
    """Match NumPy bin counts, including exact internal edges and the right endpoint."""
    x = np.array([-1, 0, 1, 1, 2, 4, 8, 16, np.inf, 16], dtype=float)
    y = np.array([0, 1, 2, 2, 2, 4, 8, 16, 2, np.nan], dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    if log_x:
        valid &= x > 0
    if log_y:
        valid &= y > 0
    xx = np.log10(x[valid]) if log_x else x[valid]
    yy = np.log10(y[valid]) if log_y else y[valid]
    counts, x_edges, y_edges = np.histogram2d(xx, yy, bins=4)
    expected = np.zeros_like(x)
    x_bin = np.clip(np.digitize(xx, x_edges) - 1, 0, counts.shape[0] - 1)
    y_bin = np.clip(np.digitize(yy, y_edges) - 1, 0, counts.shape[1] - 1)
    expected[valid] = counts[x_bin, y_bin]
    if log_color:
        expected = np.log10(1.0 + expected)
    density = compute_2d_density_values(
        x_values=x, y_values=y, x_log_scale=log_x, y_log_scale=log_y,
        colormap_log_scale=log_color, number_of_bins=4,
    )
    np.testing.assert_array_equal(density, expected)


def test_density_resolves_nearly_identical_coordinates():
    """Keep distinct endpoints when the bin width falls below floating-point precision."""
    x = [1.0, 1.0, np.nextafter(1.0, 2.0)]
    values = compute_2d_density_values(
        x_values=x, y_values=[1e16] * 3, x_log_scale=False, y_log_scale=False,
        colormap_log_scale=False, number_of_bins=5,
    )
    np.testing.assert_array_equal(values, [2, 2, 1])
