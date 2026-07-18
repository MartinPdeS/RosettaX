# -*- coding: utf-8 -*-

import pandas as pd

from RosettaX.pages.p10_visualization import services


class Test_VisualizationServices:
    def test_build_file_options_exposes_each_uploaded_file(self) -> None:
        file_store = {
            "files": [
                {
                    "uploaded_fcs_path": "/tmp/first.fcs",
                    "uploaded_filename": "first.fcs",
                },
                {
                    "uploaded_fcs_path": "/tmp/second.fcs",
                    "uploaded_filename": "second.fcs",
                },
            ]
        }

        assert services.build_file_options(file_store) == [
            {"label": "first.fcs", "value": "/tmp/first.fcs"},
            {"label": "second.fcs", "value": "/tmp/second.fcs"},
        ]
        assert services.resolve_default_file(
            file_store,
            current_value="/tmp/second.fcs",
        ) == "/tmp/second.fcs"

    def test_build_visualization_uirevision_changes_with_graph_identity(self) -> None:
        first_revision = services.build_visualization_uirevision(
            uploaded_fcs_path="/tmp/one.fcs",
            plot_type=services.PLOT_TYPE_SCATTER,
            x_channel="FSC-A",
            y_channel="SSC-A",
            log_x=True,
            log_y=False,
        )

        second_revision = services.build_visualization_uirevision(
            uploaded_fcs_path="/tmp/two.fcs",
            plot_type=services.PLOT_TYPE_SCATTER,
            x_channel="FSC-A",
            y_channel="SSC-A",
            log_x=True,
            log_y=False,
        )

        assert first_revision != second_revision

    def test_build_channel_options_returns_named_dropdown_entries(self) -> None:
        options = services.build_channel_options(["FSC-A", "SSC-A"])

        assert options == [
            {"label": "FSC-A", "value": "FSC-A"},
            {"label": "SSC-A", "value": "SSC-A"},
        ]

    def test_filter_dataframe_for_plot_filters_non_positive_log_values(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [10.0, 0.0, 5.0],
                "SSC-A": [1.0, 2.0, -1.0],
            }
        )

        filtered_dataframe, skipped_events = services.filter_dataframe_for_plot(
            dataframe,
            x_channel="FSC-A",
            y_channel="SSC-A",
            log_x=True,
            log_y=True,
        )

        assert len(filtered_dataframe) == 1
        assert skipped_events == 2

    def test_build_visualization_figure_returns_histogram_for_histogram_mode(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [1.0, 2.0, 3.0],
            }
        )

        figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/histogram.fcs",
            plot_type=services.PLOT_TYPE_HISTOGRAM,
            x_channel="FSC-A",
            y_channel=None,
            log_x=False,
            log_y=False,
        )

        assert len(figure.data) == 1
        assert figure.data[0].type == "bar"
        assert figure.layout.height == services.resolve_visualization_control_defaults()["figure_height_px"]
        assert isinstance(figure.layout.uirevision, str)

    def test_build_visualization_figure_supports_log_histogram_x_axis(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [1.0, 10.0, 100.0, 1000.0],
            }
        )

        figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/loghist.fcs",
            plot_type=services.PLOT_TYPE_HISTOGRAM,
            x_channel="FSC-A",
            y_channel=None,
            log_x=True,
            log_y=False,
        )

        assert len(figure.data) == 1
        assert figure.data[0].type == "bar"
        assert figure.layout.xaxis.type == "log"

    def test_build_visualization_figure_returns_filled_histogram(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )

        figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/example.fcs",
            plot_type=services.PLOT_TYPE_SMOOTHED_HISTOGRAM,
            x_channel="FSC-A",
            y_channel=None,
            log_x=False,
            log_y=False,
        )

        assert len(figure.data) == 1
        assert figure.data[0].type == "scatter"
        assert figure.data[0].fill == "tozeroy"
        assert figure.data[0].mode == "lines"
        assert figure.layout.title.text == "example.fcs"

    def test_smooth_histogram_counts_uses_sigma_points(self) -> None:
        smoothed_counts = services.smooth_histogram_counts(
            [0.0, 0.0, 10.0, 0.0, 0.0],
            sigma_points=1.0,
        )

        assert smoothed_counts[1] > 0.0
        assert smoothed_counts[2] < 10.0
        assert smoothed_counts[3] > 0.0

    def test_build_visualization_figure_supports_log_histogram_y_axis(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [1.0, 1.0, 1.0, 2.0, 3.0, 4.0],
            }
        )

        figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/log-y-histogram.fcs",
            plot_type=services.PLOT_TYPE_HISTOGRAM,
            x_channel="FSC-A",
            y_channel=None,
            log_x=False,
            log_y=True,
        )

        assert figure.layout.yaxis.type == "log"
        assert figure.layout.yaxis.title.text == "Count"

    def test_build_visualization_figure_returns_density_colored_scatter(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [1.0, 2.0, 10.0, 20.0, 100.0],
                "SSC-A": [5.0, 6.0, 7.0, 30.0, 40.0],
            }
        )

        figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/example.fcs",
            plot_type=services.PLOT_TYPE_SCATTER,
            x_channel="FSC-A",
            y_channel="SSC-A",
            log_x=True,
            log_y=True,
            colormap_log_scale=True,
            marker_size=7,
            marker_opacity=0.8,
        )

        assert len(figure.data) == 1
        assert figure.data[0].type == "scattergl"
        assert figure.layout.xaxis.type == "log"
        assert figure.layout.yaxis.type == "log"
        assert figure.data[0].marker.colorscale[0][1] == "#30123b"
        assert figure.data[0].marker.size == 7
        assert figure.data[0].marker.opacity == 0.8
        assert figure.layout.showlegend is False
        assert figure.layout.xaxis.title.text == "FSC-A [a.u.]"
        assert figure.layout.yaxis.title.text == "SSC-A [a.u.]"
        assert isinstance(figure.layout.uirevision, str)
        assert "/tmp/example.fcs" in figure.layout.uirevision

    def test_build_visualization_figure_uirevision_ignores_marker_styling(self) -> None:
        dataframe = pd.DataFrame(
            {
                "FSC-A": [1.0, 2.0, 10.0, 20.0, 100.0],
                "SSC-A": [5.0, 6.0, 7.0, 30.0, 40.0],
            }
        )

        first_figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/example.fcs",
            plot_type=services.PLOT_TYPE_SCATTER,
            x_channel="FSC-A",
            y_channel="SSC-A",
            log_x=True,
            log_y=True,
            marker_size=5,
            marker_opacity=0.6,
        )

        second_figure = services.build_visualization_figure(
            dataframe=dataframe,
            uploaded_fcs_path="/tmp/example.fcs",
            plot_type=services.PLOT_TYPE_SCATTER,
            x_channel="FSC-A",
            y_channel="SSC-A",
            log_x=True,
            log_y=True,
            marker_size=9,
            marker_opacity=1.0,
        )

        assert first_figure.layout.uirevision == second_figure.layout.uirevision

    def test_resolve_visualization_control_defaults_uses_default_profile(self) -> None:
        defaults = services.resolve_visualization_control_defaults()

        assert defaults["max_events"] == 100000
        assert defaults["x_log_values"] == ["enabled"]
        assert defaults["y_log_values"] == ["enabled"]
        assert defaults["colormap_log_values"] == ["enabled"]
        assert defaults["marker_size"] == 7.0
        assert defaults["marker_opacity"] == 1.0
        assert defaults["graph_style"] == {"height": "450px"}
        assert defaults["figure_height_px"] == 450
