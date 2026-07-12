# -*- coding: utf-8 -*-

from types import SimpleNamespace

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from RosettaX.pages.p04_calibrate.sections.s03_file_picker import services
from RosettaX.utils.plottings import HistogramResult


class Test_FilePickerPreview:
    def test_file_selection_uses_clean_names_and_preserves_selection(self) -> None:
        first = "/tmp/sample_one_20260712_120000_123456.fcs"
        second = "/tmp/sample_two_20260712_120001_654321.fcs"

        options, selected = services.build_preview_file_selection(
            [first, second],
            current_value=second,
        )

        assert options == [
            {"label": "sample_one.fcs", "value": first},
            {"label": "sample_two.fcs", "value": second},
        ]
        assert selected == second

    def test_selected_preview_path_must_belong_to_upload_store(self) -> None:
        assert services.resolve_selected_preview_path(
            selected_file="/tmp/not-uploaded.fcs",
            uploaded_fcs_paths=["/tmp/uploaded.fcs"],
        ) == "/tmp/uploaded.fcs"

    def test_channel_selection_reads_selected_fcs_file(
        self,
        monkeypatch,
    ) -> None:
        class FakeFCSFile:
            def __init__(self, path):
                self.path = path

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def get_column_names(self):
                return ["FSC-A", "SSC-A"]

        monkeypatch.setattr(services, "FCSFile", FakeFCSFile)

        options, selected = services.build_preview_channel_selection(
            selected_file="/tmp/input.fcs",
            uploaded_fcs_paths=["/tmp/input.fcs"],
            current_value="SSC-A",
        )

        assert options == [
            {"label": "FSC-A", "value": "FSC-A"},
            {"label": "SSC-A", "value": "SSC-A"},
        ]
        assert selected == "SSC-A"

    def test_channel_selection_filters_to_calibration_source_channels(
        self,
        monkeypatch,
    ) -> None:
        class FakeFCSFile:
            def __init__(self, path):
                self.path = path

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def get_column_names(self):
                return ["FSC-A", "SSC-A", "FITC-A"]

        monkeypatch.setattr(services, "FCSFile", FakeFCSFile)

        options, selected = services.build_preview_channel_selection(
            selected_file="/tmp/input.fcs",
            uploaded_fcs_paths=["/tmp/input.fcs"],
            selected_calibration_summary=[
                {"source_channel": "SSC-A"},
                {"source_channel": "FITC-A"},
            ],
            current_value="FITC-A",
        )

        assert options == [
            {"label": "SSC-A", "value": "SSC-A"},
            {"label": "FITC-A", "value": "FITC-A"},
        ]
        assert selected == "FITC-A"

    def test_histogram_uses_calibrated_values_for_the_selected_source_channel(
        self,
        monkeypatch,
    ) -> None:
        class FakeFCSFile:
            def __init__(self, path):
                self.path = path

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def dataframe_copy(self, *, columns):
                return pd.DataFrame({columns[0]: [1.0, 2.0, 3.0]})

        captured = SimpleNamespace(calibrated_values=None, detector_column=None)

        def fake_apply_legacy_calibration_to_series(*, values, calibration_payload, source_channel, warning_messages=None):
            captured.calibrated_values = np.asarray(values, dtype=float) * 10.0
            return captured.calibrated_values

        def fake_build_histogram_result_from_values(values, *, n_bins_for_plots, use_log_x_bins):
            captured.calibrated_values = np.asarray(values, dtype=float)
            return HistogramResult(
                values=np.asarray(values, dtype=float),
                counts=np.asarray([1.0, 2.0]),
                edges=np.asarray([10.0, 20.0, 30.0]),
                centers=np.asarray([15.0, 25.0]),
            )

        def fake_build_histogram_figure(detector_column, histogram_result, use_log_counts=False):
            captured.detector_column = detector_column
            return go.Figure(
                go.Scatter(
                    x=histogram_result.centers,
                    y=histogram_result.counts,
                )
            )

        monkeypatch.setattr(services, "FCSFile", FakeFCSFile)
        monkeypatch.setattr(services, "apply_legacy_calibration_to_series", fake_apply_legacy_calibration_to_series)
        monkeypatch.setattr(services, "_build_histogram_result_from_values", fake_build_histogram_result_from_values)
        monkeypatch.setattr(services.plottings, "build_histogram_figure", fake_build_histogram_figure)

        events_used, figure, style, status = services.build_preview_histogram_payload(
            selected_file="/tmp/input.fcs",
            selected_channel="FSC-A",
            uploaded_fcs_paths=["/tmp/input.fcs"],
            selected_calibration_summary=[
                {
                    "source_channel": "FSC-A",
                    "calibration_type": "fluorescence",
                    "calibration_payload": {
                        "scale": 10.0,
                        "offset": 0.0,
                    },
                }
            ],
            runtime_config_data={
                "calibration": {
                    "histogram_xscale": "log",
                    "histogram_yscale": "log",
                    "n_bins_for_plots": 64,
                    "max_events_for_analysis": 1234,
                },
                "visualization": {"graph_height": "420px"},
            },
            axis_scale_toggle_values=["x_log", "y_log"],
            preview_graph_visibility_toggle_values=["enabled"],
            n_bins_for_plots="64",
        )

        assert events_used == "3"
        assert np.asarray(captured.calibrated_values, dtype=float).tolist() == [10.0, 20.0, 30.0]
        assert captured.detector_column == "FSC-A"
        assert figure.layout.xaxis.type == "log"
        assert style == {"height": "420px"}
        assert "calibrated preview" in status

    def test_histogram_can_hide_preview_graph(self, monkeypatch) -> None:
        class FakeFCSFile:
            def __init__(self, path):
                self.path = path

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def dataframe_copy(self, *, columns):
                return pd.DataFrame({columns[0]: [1.0, 2.0]})

        monkeypatch.setattr(services, "FCSFile", FakeFCSFile)
        monkeypatch.setattr(
            services,
            "apply_legacy_calibration_to_series",
            lambda **kwargs: np.asarray(kwargs["values"], dtype=float),
        )

        events_used, _, style, _ = services.build_preview_histogram_payload(
            selected_file="/tmp/input.fcs",
            selected_channel="FSC-A",
            uploaded_fcs_paths=["/tmp/input.fcs"],
            selected_calibration_summary=[
                {
                    "source_channel": "FSC-A",
                    "calibration_type": "fluorescence",
                    "calibration_payload": {"scale": 1.0, "offset": 0.0},
                }
            ],
            runtime_config_data={"calibration": {"n_bins_for_plots": 64}},
            preview_graph_visibility_toggle_values=[],
            n_bins_for_plots="64",
        )

        assert events_used == "2"
        assert style["display"] == "none"

    def test_resolve_preview_control_defaults_use_preview_fallback_values(self) -> None:
        defaults = services.resolve_preview_control_defaults({})

        assert defaults["x_log_values"] == ["enabled"]
        assert defaults["n_bins_for_plots"] == 200

    def test_resolve_preview_control_defaults_uses_profile_values(self) -> None:
        defaults = services.resolve_preview_control_defaults(
            {
                "calibration": {
                    "histogram_xscale": "log",
                    "histogram_yscale": "linear",
                    "n_bins_for_plots": 128,
                },
                "visualization": {"graph_height": "400px"},
            }
        )

        assert defaults == {
            "graph_height": "400px",
            "x_log_values": ["enabled"],
            "y_log_values": [],
            "n_bins_for_plots": 128,
        }
