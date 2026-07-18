# -*- coding: utf-8 -*-

import logging

import numpy as np
import pytest

import plotly.graph_objs as go

from RosettaX.pages.p02_fluorescence.sections.s04_calibration import services


class Test_FluorescenceCalibrationPreview:
    def test_log_fit_rejects_degenerate_measured_values(self) -> None:
        with pytest.raises(ValueError, match="distinct"):
            services.fit_log10_calibration(
                intensity_calibrated_units=np.asarray([100.0, 1000.0]),
                intensity_au=np.asarray([10.0, 10.0]),
            )

    def test_run_calibration_workflow_returns_preview_metrics_and_figure_store(
        self,
        monkeypatch,
    ) -> None:
        preview_figure = go.Figure()
        preview_figure.add_bar(x=[1.0, 2.0], y=[3.0, 4.0], name="signal")

        monkeypatch.setattr(
            services,
            "compute_valid_event_count_for_preview",
            lambda **_: 123,
        )
        monkeypatch.setattr(
            services,
            "build_raw_signal_preview_figure",
            lambda **_: preview_figure,
        )

        result = services.run_calibration_workflow(
            bead_file_path="/tmp/beads.fcs",
            table_data=[
                {
                    "col1": "1000",
                    "col2": "100",
                },
                {
                    "col1": "10000",
                    "col2": "1000",
                },
            ],
            detector_column="FITC-A",
            scattering_detector_column=None,
            scattering_threshold=None,
            logger=logging.getLogger(__name__),
        )

        assert result.point_count_out == "2"
        assert result.preview_event_count_out == "123"
        assert result.preview_figure_store["data"][0]["name"] == "signal"
        assert result.apply_status == (
            "Calibration fit created successfully. Preview computed for 123 valid events "
            "on detector 'FITC-A'."
        )
