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

    def test_make_histogram_with_lines_uses_zero_bar_gap(self) -> None:
        figure = plottings.make_histogram_with_lines(
            values=np.asarray([1.0, 2.0, 3.0, 4.0], dtype=float),
            nbins=4,
            xaxis_title="Signal",
            line_positions=[],
            line_labels=[],
        )

        assert figure.layout.bargap == 0.0

    def test_build_histogram_figure_uses_filled_step_trace(self) -> None:
        histogram_result = plottings.HistogramResult(
            values=np.asarray([1.0, 2.0, 4.0, 8.0], dtype=float),
            counts=np.asarray([3.0, 1.0, 2.0], dtype=float),
            edges=np.asarray([1.0, 2.0, 4.0, 8.0], dtype=float),
            centers=np.asarray(
                [np.sqrt(2.0), np.sqrt(8.0), np.sqrt(32.0)],
                dtype=float,
            ),
        )

        figure = plottings.build_histogram_figure(
            detector_column="FL1-A",
            histogram_result=histogram_result,
        )

        assert len(figure.data) == 1
        assert figure.data[0].type == "scatter"
        assert figure.data[0].fill == "tozeroy"
        assert tuple(figure.data[0].x) == (1.0, 2.0, 2.0, 4.0, 4.0, 8.0)
        assert tuple(figure.data[0].y) == (3.0, 3.0, 1.0, 1.0, 2.0, 2.0)
