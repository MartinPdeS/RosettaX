# -*- coding: utf-8 -*-

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
    finite_plot_values,
    smooth_histogram_counts,
)


class TestPlottingModels:
    def test_plot_options_validate_shared_controls(self) -> None:
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
        with pytest.raises(ValueError, match=message):
            factory(**value)


class TestPlottingTransforms:
    def test_finite_plot_values_filters_nonfinite_and_nonpositive_values(self) -> None:
        values = finite_plot_values([1.0, np.nan, -2.0, np.inf, 3.0])
        positive_values = finite_plot_values(
            [1.0, np.nan, -2.0, np.inf, 3.0],
            positive_only=True,
        )

        np.testing.assert_array_equal(values, [1.0, -2.0, 3.0])
        np.testing.assert_array_equal(positive_values, [1.0, 3.0])

    def test_build_histogram_arrays_supports_linear_and_log_bins(self) -> None:
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
        with pytest.raises(ValueError, match="positive"):
            build_histogram_arrays([-2.0, 0.0, np.nan], bin_count=4, log_x=True)

    def test_smooth_histogram_counts_preserves_shape_and_zero_sigma(self) -> None:
        counts = np.asarray([0.0, 4.0, 0.0, 2.0, 0.0])

        unchanged = smooth_histogram_counts(counts, sigma_points=0.0)
        smoothed = smooth_histogram_counts(counts, sigma_points=1.0)

        np.testing.assert_array_equal(unchanged, counts)
        assert smoothed.shape == counts.shape
        assert not np.array_equal(smoothed, counts)
        assert np.all(np.isfinite(smoothed))
