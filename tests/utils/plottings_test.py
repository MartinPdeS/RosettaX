# -*- coding: utf-8 -*-

import numpy as np

from RosettaX.utils import plottings


class Test_PlottingsHistogram:
    def test_build_histogram_uses_log_spaced_edges_when_requested(self, monkeypatch) -> None:
        monkeypatch.setattr(
            plottings,
            "load_signal",
            lambda **kwargs: np.asarray([1.0, 10.0, 100.0, 1000.0], dtype=float),
        )

        histogram_result = plottings.build_histogram(
            fcs_file_path="/tmp/example.fcs",
            detector_column="FL1-A",
            n_bins_for_plots=3,
            use_log_x_bins=True,
        )

        assert histogram_result.edges.tolist() == [1.0, 10.0, 100.0, 1000.0]
        assert np.allclose(
            histogram_result.centers,
            [
                np.sqrt(10.0),
                np.sqrt(1000.0),
                np.sqrt(100000.0),
            ],
        )

    def test_build_histogram_log_bins_drops_non_positive_values(self, monkeypatch) -> None:
        monkeypatch.setattr(
            plottings,
            "load_signal",
            lambda **kwargs: np.asarray([-10.0, 0.0, 1.0, 10.0], dtype=float),
        )

        histogram_result = plottings.build_histogram(
            fcs_file_path="/tmp/example.fcs",
            detector_column="FL1-A",
            n_bins_for_plots=2,
            use_log_x_bins=True,
        )

        assert np.all(histogram_result.values > 0.0)
        assert histogram_result.values.tolist() == [1.0, 10.0]
