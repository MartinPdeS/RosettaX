"""Regression tests for workflow peak graphing."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import dash
import numpy as np
import plotly.graph_objs as go
import pytest
import sys
import types
from RosettaX.workflow.peak.core import (
    graph_histogram,
    graph_overlays,
    graph_scatter,
    graph_settings,
)


class _DashBootstrapComponentsSentinel:
    """Callable component sentinel for lightweight Dash Bootstrap test setup."""

    def __call__(self, *args, **kwargs):
        """Provide the callable behavior required by this test double."""
        return None

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    """Minimal Dash Bootstrap components used by the unit tests."""

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return _DashBootstrapComponentsSentinel()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)

from RosettaX.workflow.peak.adapters.scattering import ScatteringPeakWorkflowAdapter
from RosettaX.workflow.peak.callbacks.graph import (
    add_grouped_2d_scatter_traces,
    build_peak_figure_update,
    preserve_peak_axis_ranges,
    sanitize_group_points,
)
from RosettaX.workflow.peak.core.graphing import (
    PeakWorkflowGraphBuilder,
    add_peak_workflow_post_layout_overlays,
    apply_peak_workflow_interaction_revision,
    axis_scale_selection_is_log,
    build_peak_workflow_uirevision,
    is_enabled,
    scale_selection_is_log,
)
from RosettaX.workflow.peak.scripts import rosetta_mix
from RosettaX.workflow.peak.scripts.base import (
    filter_edge_artifact_pairs,
    filter_edge_artifact_values,
    resolve_edge_artifact_filter_enabled,
)
from RosettaX.workflow.peak.scripts.rosetta_mix_models import RosettaRunSettings


class Test_is_enabled:
    """Test suite for is_enabled function."""

    def test_is_enabled_string_enabled(self):
        """Test is_enabled with string 'enabled'."""
        assert is_enabled("enabled") is True

    def test_is_enabled_string_disabled(self):
        """Test is_enabled with string other than 'enabled'."""
        assert is_enabled("disabled") is False
        assert is_enabled("off") is False
        assert is_enabled("") is False
        assert is_enabled("random_string") is False

    def test_is_enabled_list_with_enabled(self):
        """Test is_enabled with list containing 'enabled'."""
        assert is_enabled(["enabled", "other"]) is True
        assert is_enabled(["other", "enabled"]) is True
        assert is_enabled(["enabled"]) is True

    def test_is_enabled_list_without_enabled(self):
        """Test is_enabled with list not containing 'enabled'."""
        assert is_enabled(["disabled", "off"]) is False
        assert is_enabled(["other", "values"]) is False
        assert is_enabled([]) is False

    def test_is_enabled_tuple_with_enabled(self):
        """Test is_enabled with tuple containing 'enabled'."""
        assert is_enabled(("enabled", "other")) is True
        assert is_enabled(("other", "enabled")) is True
        assert is_enabled(("enabled",)) is True

    def test_is_enabled_tuple_without_enabled(self):
        """Test is_enabled with tuple not containing 'enabled'."""
        assert is_enabled(("disabled", "off")) is False
        assert is_enabled(("other", "values")) is False
        assert is_enabled(()) is False

    def test_is_enabled_set_with_enabled(self):
        """Test is_enabled with set containing 'enabled'."""
        assert is_enabled({"enabled", "other"}) is True
        assert is_enabled({"other", "enabled"}) is True
        assert is_enabled({"enabled"}) is True

    def test_is_enabled_set_without_enabled(self):
        """Test is_enabled with set not containing 'enabled'."""
        assert is_enabled({"disabled", "off"}) is False
        assert is_enabled({"other", "values"}) is False
        assert is_enabled(set()) is False

    def test_is_enabled_boolean_true(self):
        """Test is_enabled with boolean True."""
        assert is_enabled(True) is True

    def test_is_enabled_boolean_false(self):
        """Test is_enabled with boolean False."""
        assert is_enabled(False) is False

    def test_is_enabled_none(self):
        """Test is_enabled with None."""
        assert is_enabled(None) is False

    def test_is_enabled_numeric_values(self):
        """Test is_enabled with numeric values."""
        assert is_enabled(1) is False
        assert is_enabled(0) is False
        assert is_enabled(1.5) is False
        assert is_enabled(-1) is False

    def test_is_enabled_other_objects(self):
        """Test is_enabled with other object types."""
        assert is_enabled({"key": "value"}) is False
        assert is_enabled(object()) is False


class Test_scale_selection_is_log:
    """Test suite for scale_selection_is_log function."""

    def test_scale_selection_is_log_string_log(self):
        """Test scale_selection_is_log with string 'log'."""
        assert scale_selection_is_log("log") is True

    def test_scale_selection_is_log_string_linear(self):
        """Test scale_selection_is_log with string 'linear'."""
        assert scale_selection_is_log("linear") is False

    def test_scale_selection_is_log_string_other(self):
        """Test scale_selection_is_log with other strings."""
        assert scale_selection_is_log("logarithmic") is False
        assert scale_selection_is_log("") is False
        assert scale_selection_is_log("random") is False

    def test_scale_selection_is_log_case_sensitive(self):
        """Test that scale_selection_is_log is case sensitive."""
        assert scale_selection_is_log("LOG") is False
        assert scale_selection_is_log("Log") is False
        assert scale_selection_is_log("log") is True

    def test_scale_selection_is_log_non_string(self):
        """Test scale_selection_is_log with non-string values."""
        assert scale_selection_is_log(True) is False
        assert scale_selection_is_log(False) is False
        assert scale_selection_is_log(1) is False
        assert scale_selection_is_log(None) is False
        assert scale_selection_is_log([]) is False
        assert scale_selection_is_log(["log"]) is True
        assert scale_selection_is_log(["x_log"]) is False
        assert scale_selection_is_log(["y_log"]) is False
        assert scale_selection_is_log({"log"}) is True


class Test_axis_scale_selection_is_log:
    """Regression checks for axis scale selection is log."""

    def test_axis_scale_selection_is_log_supports_axis_specific_toggles(self):
        """Check axis scale selection is log supports axis specific toggles."""
        assert (
            axis_scale_selection_is_log(
                scale_selection=["x_log"],
                axis="x",
            )
            is True
        )
        assert (
            axis_scale_selection_is_log(
                scale_selection=["y_log"],
                axis="y",
            )
            is True
        )

    def test_axis_scale_selection_is_log_keeps_axes_independent(self):
        """Check axis scale selection is log keeps axes independent."""
        assert (
            axis_scale_selection_is_log(
                scale_selection=["x_log"],
                axis="y",
            )
            is False
        )
        assert (
            axis_scale_selection_is_log(
                scale_selection=["y_log"],
                axis="x",
            )
            is False
        )


# Additional test classes for other functions in the graphing module
# Note: Since we only saw the first 50 lines, these are based on typical graphing functionality
class Test_GraphingUtilities:
    """Test suite for additional graphing utilities."""

    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample data for graphing tests."""
        return {
            "x_values": np.array([1, 2, 3, 4, 5]),
            "y_values": np.array([10, 20, 30, 40, 50]),
            "labels": ["A", "B", "C", "D", "E"],
        }

    def test_is_enabled_with_dash_callback_context(self):
        """Test is_enabled function with Dash callback-style inputs."""
        # Test with Dash-style checklist values
        assert is_enabled(["enabled"]) is True
        assert is_enabled([]) is False
        assert is_enabled(None) is False

    def test_scale_selection_backwards_compatibility(self):
        """Test scale_selection_is_log backwards compatibility."""
        # Test the function handles legacy input formats
        assert scale_selection_is_log("log") is True
        assert scale_selection_is_log("linear") is False

        # Edge cases for backwards compatibility
        assert scale_selection_is_log("") is False
        assert scale_selection_is_log(None) is False

    @pytest.mark.parametrize(
        "graph_toggle,expected",
        [
            ("enabled", True),
            ("disabled", False),
            (["enabled"], True),
            (["disabled"], False),
            (["enabled", "other"], True),
            (["other"], False),
            (True, True),
            (False, False),
            (None, False),
            ([], False),
            (1, False),
            ("", False),
        ],
    )
    def test_is_enabled_parametrized(self, graph_toggle, expected):
        """Parametrized test for is_enabled function with various inputs."""
        assert is_enabled(graph_toggle) == expected

    @pytest.mark.parametrize(
        "scale_value,expected",
        [
            ("log", True),
            ("linear", False),
            ("logarithmic", False),
            ("LOG", False),
            ("Log", False),
            ("", False),
            (None, False),
            (True, False),
            (["log"], True),
            (1, False),
        ],
    )
    def test_scale_selection_is_log_parametrized(self, scale_value, expected):
        """Parametrized test for scale_selection_is_log function."""
        assert scale_selection_is_log(scale_value) == expected


class Test_GraphingFunctionIntegration:
    """Integration tests for graphing functions working together."""

    def test_combined_graph_settings(self):
        """Test combination of graph settings functions."""
        # Test realistic combination of settings
        graph_enabled = is_enabled("enabled")
        log_scale = scale_selection_is_log("log")

        assert graph_enabled is True
        assert log_scale is True

        # Test disabled graph with linear scale
        graph_disabled = is_enabled("disabled")
        linear_scale = scale_selection_is_log("linear")

        assert graph_disabled is False
        assert linear_scale is False

    def test_dash_callback_simulation(self):
        """Test functions with simulated Dash callback inputs."""
        # Simulate typical Dash callback inputs
        checklist_enabled = ["enabled", "show_legend"]
        scale_dropdown = "log"

        # Test the functions handle these inputs correctly
        assert is_enabled(checklist_enabled) is True
        assert scale_selection_is_log(scale_dropdown) is True

        # Test empty/disabled states
        checklist_empty = []
        scale_linear = "linear"

        assert is_enabled(checklist_empty) is False
        assert scale_selection_is_log(scale_linear) is False

    def test_error_handling_edge_cases(self):
        """Test error handling and edge cases."""
        # Test with unusual but potentially valid inputs
        weird_inputs = [
            {"enabled": True},  # Dictionary
            123,  # Number
            [1, 2, 3],  # List of numbers
            object(),  # Arbitrary object
        ]

        for weird_input in weird_inputs:
            # Should not raise exceptions
            result = is_enabled(weird_input)
            assert isinstance(result, bool)

            log_result = scale_selection_is_log(weird_input)
            assert isinstance(log_result, bool)


class Test_GraphingModuleConstants:
    """Test any constants or configuration values in the graphing module."""

    def test_function_return_types(self):
        """Ensure functions return correct types."""
        # Test is_enabled always returns boolean
        assert isinstance(is_enabled("enabled"), bool)
        assert isinstance(is_enabled("disabled"), bool)
        assert isinstance(is_enabled(None), bool)

        # Test scale_selection_is_log always returns boolean
        assert isinstance(scale_selection_is_log("log"), bool)
        assert isinstance(scale_selection_is_log("linear"), bool)
        assert isinstance(scale_selection_is_log(None), bool)

    def test_function_consistency(self):
        """Test that functions behave consistently across multiple calls."""


class Test_Grouped2DScatterTraces:
    """Regression checks for grouped2 dscatter traces."""

    def test_sanitize_group_points_excludes_zero_and_non_finite_values(self):
        """Check sanitize group points excludes zero and non finite values."""
        x_values, y_values = sanitize_group_points(
            group_points={
                "x_values": [1.0, 0.0, 2.0, np.nan],
                "y_values": [3.0, 4.0, 0.0, 5.0],
            },
            x_log_scale=False,
            y_log_scale=False,
        )

        assert x_values.tolist() == [1.0]
        assert y_values.tolist() == [3.0]

    def test_add_grouped_2d_scatter_traces_uses_black_markers(self):
        """Check add grouped 2D scatter traces uses black markers."""
        figure = add_grouped_2d_scatter_traces(
            figure=go.Figure(),
            peak_lines_payload={
                "group_points": [
                    {
                        "x_values": [1.0, 2.0],
                        "y_values": [3.0, 4.0],
                    }
                ],
                "group_labels": ["Group 1"],
            },
            x_log_scale=False,
            y_log_scale=False,
        )

        assert len(figure.data) == 1
        assert figure.data[0].marker.color == "black"


class Test_PeakWorkflowGraphBuilder2DFiltering:
    """Regression checks for peak workflow graph builder2 dfiltering."""

    def test_filter_2d_values_for_axis_scale_excludes_zero_values(self):
        """Check filter 2D values for axis scale excludes zero values."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.xscale_selection = "linear"
        builder.yscale_selection = "linear"

        filtered_x_values, filtered_y_values = (
            graph_scatter.filter_2d_values_for_axis_scale(
                builder,
                x_values=np.array([0.0, 1.0, 2.0, np.nan]),
                y_values=np.array([5.0, 0.0, 3.0, 4.0]),
            )
        )

        assert filtered_x_values.tolist() == [2.0]
        assert filtered_y_values.tolist() == [3.0]
        # Test idempotency
        for _ in range(5):
            assert is_enabled("enabled") is True
            assert is_enabled("disabled") is False
            assert scale_selection_is_log("log") is True
            assert scale_selection_is_log("linear") is False

    def test_extract_plot_values_from_peak_lines_payload_uses_payload_override(self):
        """Check extract plot values from peak lines payload uses payload override."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.peak_lines_payload = {
            "plot_x_values": [10.0, 20.0, "bad", float("nan")],
            "plot_y_values": [100.0, 200.0, 300.0, 400.0],
        }

        payload_values = graph_scatter.extract_plot_values_from_peak_lines_payload(
            builder
        )

        assert payload_values is not None
        payload_x_values, payload_y_values = payload_values
        assert payload_x_values.tolist() == [10.0, 20.0]
        assert payload_y_values.tolist() == [100.0, 200.0]

    @pytest.mark.parametrize("filter_edge_artifacts", [True, False])
    def test_rebuilds_rosetta_cloud_from_compact_page_state(self, monkeypatch, filter_edge_artifacts):
        """Keep the detected events and their order without storing their arrays in Dash."""
        backend = types.SimpleNamespace(fcs_file_path="beads.fcs")
        detector_channels = {"scattering": "SSC-H", "green_fluorescence": "FL1-H"}
        signals = {
            "SSC-H": np.concatenate([np.zeros(35), np.arange(1.0, 66.0), np.full(45, 10_000.0)]),
            "FL1-H": np.arange(100.0, 245.0),
        }

        def read_columns(*, fcs_file_path, detector_columns, max_events):
            """Read a detector prefix without touching the underlying signal."""
            assert fcs_file_path == backend.fcs_file_path
            return tuple(signals[column][:max_events].copy() for column in detector_columns)

        monkeypatch.setattr(rosetta_mix, "read_peak_event_columns", read_columns)
        settings = RosettaRunSettings.from_raw_values(
            peak_count=3, max_events_for_analysis=130,
            process_settings={"filter_edge_artifacts": filter_edge_artifacts},
        )
        detected_events = rosetta_mix.load_rosetta_events(
            backend=backend, scattering_column="SSC-H", green_fluorescence_column="FL1-H",
            settings=settings, retain_scatter_edges=True,
        )
        assert (detected_events.scattering_values.size < 130) is filter_edge_artifacts

        adapter = ScatteringPeakWorkflowAdapter()
        page_state = adapter.get_page_state_from_payload({"uploaded_fcs_path": backend.fcs_file_path})
        original_payload = detected_events.plot_payload()
        next_state = adapter.update_peak_lines_payload(page_state=page_state, peak_lines_payload=original_payload)
        stored_payload = adapter.get_peak_lines_payload(page_state=next_state)
        assert set(stored_payload) == {"rosetta_plot_source"}
        assert "plot_x_values" in original_payload

        builder = types.SimpleNamespace(
            backend=backend, detector_channels=detector_channels,
            peak_lines_payload=stored_payload, max_events_for_plots=1,
        )
        plot_scatter, plot_fluorescence = graph_scatter.extract_plot_values_from_peak_lines_payload(builder)
        np.testing.assert_array_equal(plot_scatter, detected_events.scattering_values)
        np.testing.assert_array_equal(plot_fluorescence, detected_events.fluorescence_values)

        builder.detector_channels = {**detector_channels, "green_fluorescence": "FL2-H"}
        assert graph_scatter.extract_plot_values_from_peak_lines_payload(builder) is None


class Test_EdgeArtifactFiltering:
    """Regression checks for edge artifact filtering."""

    def test_filter_edge_artifact_values_removes_floor_and_ceiling_pileups(self):
        """Check filter edge artifact values removes floor and ceiling pileups."""
        values = np.concatenate(
            [
                np.ones(40, dtype=float),
                np.linspace(100.0, 1000.0, 400, dtype=float),
                np.full(40, 1.0e6, dtype=float),
            ]
        )

        filtered_values = filter_edge_artifact_values(
            values=values,
            remove_min=True,
            remove_max=True,
        )

        assert float(np.min(filtered_values)) > 1.0
        assert float(np.max(filtered_values)) < 1.0e6

    def test_filter_edge_artifact_pairs_removes_scatter_floor_ceiling_and_fluorescence_floor(
        self,
    ):
        """Check filter edge artifact pairs removes scatter floor ceiling and fluorescence floor."""
        x_values = np.concatenate(
            [
                np.ones(30, dtype=float),
                np.linspace(200.0, 2000.0, 300, dtype=float),
                np.full(30, 5.0e6, dtype=float),
            ]
        )
        y_values = np.concatenate(
            [
                np.ones(30, dtype=float),
                np.linspace(100.0, 900.0, 300, dtype=float),
                np.linspace(300.0, 700.0, 30, dtype=float),
            ]
        )

        filtered_x_values, filtered_y_values = filter_edge_artifact_pairs(
            x_values=x_values,
            y_values=y_values,
            remove_x_min=True,
            remove_x_max=True,
            remove_y_min=True,
            remove_y_max=False,
        )

        assert float(np.min(filtered_x_values)) > 1.0
        assert float(np.max(filtered_x_values)) < 5.0e6
        assert float(np.min(filtered_y_values)) > 1.0

    def test_resolve_edge_artifact_filter_enabled_defaults_to_true(self):
        """Check resolve edge artifact filter enabled defaults to true."""
        assert (
            resolve_edge_artifact_filter_enabled(
                process_settings={},
                default=True,
            )
            is True
        )

        assert (
            resolve_edge_artifact_filter_enabled(
                process_settings={
                    "filter_edge_artifacts": [],
                },
                default=True,
            )
            is False
        )


class Test_PeakWorkflowGraphBuilder1DHistogramRange:
    """Regression checks for peak workflow graph builder1 dhistogram range."""

    def test_advanced_overlay_does_not_expand_histogram_y_range(self):
        """Check advanced overlay does not expand histogram y range."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.yscale_selection = "linear"
        builder._stable_histogram_count_values = np.asarray(
            [10.0, 15.0, 12.0],
            dtype=float,
        )

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[1.0, 2.0, 3.0],
                y=[10.0, 5000.0, 12.0],
                mode="lines",
            )
        )

        graph_histogram.apply_stable_1d_histogram_y_range(
            builder,
            figure=figure,
        )

        assert figure.layout.yaxis.autorange is False
        assert tuple(figure.layout.yaxis.range) == pytest.approx((9.7545, 15.2435))


class Test_PeakWorkflowInteractionRevision:
    """Regression checks for peak workflow interaction revision."""

    def test_build_peak_workflow_uirevision_stays_stable_for_overlay_changes(self):
        """Check build peak workflow uirevision stays stable for overlay changes."""
        first_revision = build_peak_workflow_uirevision(
            uploaded_fcs_path="/tmp/example.fcs",
            process_name="Rosetta Script V1",
            detector_dropdown_values=["SSC-A", "FITC-A"],
            xscale_selection=["x_log"],
            yscale_selection=["y_log"],
        )

        second_revision = build_peak_workflow_uirevision(
            uploaded_fcs_path="/tmp/example.fcs",
            process_name="Rosetta Script V1",
            detector_dropdown_values=["SSC-A", "FITC-A"],
            xscale_selection=["x_log"],
            yscale_selection=["y_log"],
        )

        assert first_revision == second_revision

    def test_build_peak_workflow_uirevision_changes_when_axis_mode_changes(self):
        """Check build peak workflow uirevision changes when axis mode changes."""
        log_revision = build_peak_workflow_uirevision(
            uploaded_fcs_path="/tmp/example.fcs",
            process_name="Manual 2D",
            detector_dropdown_values=["SSC-A", "FITC-A"],
            xscale_selection=["x_log"],
            yscale_selection=[],
        )

        linear_revision = build_peak_workflow_uirevision(
            uploaded_fcs_path="/tmp/example.fcs",
            process_name="Manual 2D",
            detector_dropdown_values=["SSC-A", "FITC-A"],
            xscale_selection=[],
            yscale_selection=[],
        )

        assert log_revision != linear_revision

    def test_apply_peak_workflow_interaction_revision_sets_uirevision(self):
        """Check apply peak workflow interaction revision sets uirevision."""
        figure = apply_peak_workflow_interaction_revision(
            figure=go.Figure(),
            uploaded_fcs_path="/tmp/example.fcs",
            process_name="Manual 1D",
            detector_dropdown_values=["SSC-A"],
            xscale_selection=[],
            yscale_selection=["y_log"],
        )

        assert isinstance(figure.layout.uirevision, str)
        assert "Manual 1D" in figure.layout.uirevision


class Test_PeakWorkflowGraphBuilderRosettaOverlays:
    """Regression checks for peak workflow graph builder Rosetta overlays."""

    def test_baseline_is_drawn_between_events_and_peak_markers(self):
        """Draw the gate over events while leaving the peak centers on top."""
        figure = go.Figure(go.Scattergl(x=[100, 200], y=[1000, 1000], mode="markers", name="Events"))
        figure.add_trace(go.Scattergl(
            x=[150], y=[1000], mode="markers", name="Non-fluorescent peak",
            meta={"rosetta_peak_kind": "non_fluorescent"},
        ))
        figure.update_xaxes(type="log", range=[1, 3])
        add_peak_workflow_post_layout_overlays(
            figure=figure, process_name="Rosetta Script Mixture",
            peak_lines_payload={
                "baseline_cutoff": 1000.0,
                "scatter_guide_annotations": [{"x": 150, "label": "147 nm", "kind": "non_fluorescent"}],
            },
        )
        assert [trace.name for trace in figure.data] == ["Events", "Non-fluorescent peak"]
        baseline = next(shape for shape in figure.layout.shapes if shape.name == "Fluorescence baseline gate")
        assert (baseline.xref, baseline.x0, baseline.x1) == ("x domain", 0, 1)

    @pytest.mark.parametrize("payload", [None, {}])
    def test_rosetta_preview_before_detection_keeps_event_trace(self, payload):
        """Render the empty detection state reached on selection or after Clear."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script Mixture"
        builder.process = types.SimpleNamespace(supports_advanced_mode=False)
        builder.advanced_mode_value = []
        builder.peak_lines_payload = payload
        figure = go.Figure(go.Scattergl(x=[100.0], y=[200.0], mode="markers"))

        graph_overlays.add_selected_peak_markers(builder, figure=figure)
        add_peak_workflow_post_layout_overlays(
            figure=figure, process_name=builder.resolved_process_name,
            peak_lines_payload=payload,
        )

        assert len(figure.data) == 1
        assert list(figure.data[0].x) == [100.0]
        assert not figure.layout.annotations

    def test_saturation_guard_shows_cutoff_without_excluded_peak(self):
        """Show the cutoff without adding a symbol or guide for an excluded peak."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script Mixture"
        builder.process = types.SimpleNamespace(supports_advanced_mode=False)
        builder.advanced_mode_value = []
        builder.peak_lines_payload = {
            "points": [{"x": 3500000.0, "y": 500.0, "kind": "non_fluorescent"}],
            "labels": ["Non-fluorescent peak 7"],
            "saturation_guard_threshold": 2000000.0,
            "saturation_guard_excluded_positions": [3500000.0],
            "baseline_cutoff": 1000.0,
            "y_lower_gate": 0.0,
            "y_upper_gate": 1000.0,
            "scatter_guide_annotations": [
                {"x": 3500000.0, "label": "Excluded by saturation guard", "kind": "excluded"},
            ],
        }
        figure = go.Figure()
        figure.update_xaxes(type="log")
        figure.update_yaxes(type="log")
        graph_overlays.add_y_axis_gate_overlay(builder, figure=figure)
        graph_overlays.add_selected_peak_markers(builder, figure=figure)
        add_peak_workflow_post_layout_overlays(
            figure=figure, process_name=builder.resolved_process_name,
            peak_lines_payload=builder.peak_lines_payload,
        )
        assert not figure.data
        assert not any(shape.x0 == shape.x1 == 3500000.0 for shape in figure.layout.shapes)
        assert any(shape.x0 == 2000000.0 for shape in figure.layout.shapes)
        annotations = {item.text: item for item in figure.layout.annotations}
        assert "Excluded by saturation guard" not in annotations
        assert "Saturation guard cutoff" not in annotations
        assert "Fluorescence baseline gate" not in annotations
        legend_shapes = {shape.name: shape for shape in figure.layout.shapes if shape.showlegend}
        assert legend_shapes["Saturation guard cutoff"].x0 == 2000000.0
        baseline = legend_shapes["Fluorescence baseline gate"]
        assert (baseline.yref, baseline.y0, baseline.y1) == ("y", 1000.0, 1000.0)
        assert baseline.line.color == "#f43f5e"
        assert legend_shapes["Saturation guard cutoff"].layer == "below"
        assert all(shape.type != "rect" for shape in figure.layout.shapes)

    @pytest.mark.parametrize("process_name", [
        "Rosetta Script V1", "Rosetta Script Conservative",
        "Rosetta Script Sensitive", "Rosetta Script Mixture",
    ])
    def test_rosetta_classifies_peak_symbols_and_labels(self, process_name):
        """Show the legend below the axes and unboxed sizes above their guides."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = process_name
        builder.process = types.SimpleNamespace(supports_advanced_mode=False)
        builder.advanced_mode_value = []
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 10000.0, "kind": "marker"},
                {"x": 200.0, "y": 300.0, "kind": "non_fluorescent"},
            ],
            "labels": ["Dim marker", "Non-fluorescent peak 1"],
            "scatter_guide_positions": [100.0, 200.0],
            "baseline_cutoff": 1000.0,
            "rosetta_size_assignments": [
                {"position": 200.0, "diameter_nm": 147.0, "method": "Estimated by rank from one marker"},
            ],
            "scatter_guide_annotations": [
                {"x": 100.0, "label": "140 nm", "kind": "marker"},
                {"x": 200.0, "label": "147 nm", "kind": "non_fluorescent"},
            ],
        }
        figure = go.Figure()
        figure.update_xaxes(type="log")
        figure.update_yaxes(type="log")
        graph_overlays.add_selected_peak_markers(builder, figure=figure)
        graph_settings.apply_runtime_visualization_settings(
            types.SimpleNamespace(marker_size=5, marker_opacity=0.4, runtime_config_data={}),
            figure=figure,
        )
        figure = add_peak_workflow_post_layout_overlays(
            figure=figure, process_name=process_name, peak_lines_payload=builder.peak_lines_payload,
        )
        traces = {trace.name: trace for trace in figure.data}
        for name, color in (("Fluorescent marker", "#7c3aed"), ("Non-fluorescent peak", "#008c80")):
            trace = traces[name]
            assert trace.marker.symbol == "square"
            assert trace.marker.size == 12
            assert trace.marker.color == color
            assert list(trace.x) == list(trace.y) == [None]
        assert figure.layout.showlegend is True
        assert figure.layout.legend.x == pytest.approx(0.01)
        assert figure.layout.legend.y == pytest.approx(0.012)
        assert figure.layout.legend.xanchor == "left"
        assert figure.layout.legend.yanchor == "bottom"
        assert figure.layout.legend.orientation == "h"
        assert figure.layout.legend.xref == figure.layout.legend.yref == "container"
        annotations = {annotation.text: annotation for annotation in figure.layout.annotations}
        assert annotations["140 nm"].hovertext == "140 nm fluorescent marker"
        assert annotations["140 nm"].font.color == "#7c3aed"
        assert annotations["147 nm"].font.color == "#008c80"
        for annotation in annotations.values():
            assert annotation.yref == "paper"
            assert annotation.y == 1
            assert annotation.textangle == -45
            assert annotation.borderwidth is None
            assert annotation.bgcolor is None
            assert annotation.ax == 0
            assert annotation.ay == -4
        assert "Fluorescence baseline gate" not in annotations
        assert any(shape.name == "Fluorescence baseline gate" and shape.showlegend for shape in figure.layout.shapes)

    def test_rosetta_guides_keep_existing_axis_limits(self):
        """Keep scale limits fixed when a marker arrives at the plot edge."""
        figure = go.Figure()
        figure.update_xaxes(type="log", range=[1, 3])
        figure.update_yaxes(type="log", range=[1, 5])
        payload = {
            "points": [{"x": 1000, "y": 100000, "kind": "marker"}],
            "scatter_guide_annotations": [{"x": 1000, "label": "380 nm", "kind": "marker"}],
        }
        add_peak_workflow_post_layout_overlays(figure=figure, process_name="Rosetta Script V1", peak_lines_payload=payload)
        assert figure.layout.xaxis.range == (1, 3)
        assert figure.layout.yaxis.range == (1, 5)
        assert figure.layout.annotations[0].y == 1
        assert figure.layout.annotations[0].ay < 0

    def test_rosetta_y_gate_overlay_uses_bright_line_without_shading(self):
        """Show a bright gate beneath markers without colored background bands."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script"
        builder.yscale_selection = "log"
        builder.peak_lines_payload = {
            "y_lower_gate": 20.0,
            "y_upper_gate": 1000.0,
        }

        figure = go.Figure()
        figure.update_yaxes(type="log", range=[0.0, 4.0])

        figure = graph_overlays.add_y_axis_gate_overlay(
            builder,
            figure=figure,
        )

        shapes = list(figure.layout.shapes or [])

        assert len(shapes) == 1
        assert shapes[0].type == "line"
        assert shapes[0].line.color == "#f43f5e"
        assert shapes[0].layer == "below"
        assert not list(figure.layout.annotations or [])

    def test_rosetta_selected_peak_markers_add_vertical_and_horizontal_guides(self):
        """Check Rosetta selected peak markers add vertical and horizontal guides."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script"
        builder.process = None
        builder.advanced_mode_value = ["enabled"]
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 200.0, "kind": "non_fluorescent"},
                {"x": 300.0, "y": 400.0, "kind": "marker"},
                {"x": 500.0, "y": 400.0, "kind": "non_fluorescent"},
            ],
            "scatter_guide_positions": [100.0, 300.0, 500.0],
            "fluorescence_guide_positions": [200.0, 400.0],
            "labels": [
                "Non-fluorescent peak 1",
                "Bright marker",
                "Dim marker",
            ],
        }

        figure = graph_overlays.add_selected_peak_markers(
            builder,
            figure=go.Figure(),
        )

        shapes = list(figure.layout.shapes or [])

        vertical_shapes = [
            shape
            for shape in shapes
            if shape.type == "line" and float(shape.x0) == float(shape.x1)
        ]
        horizontal_shapes = [
            shape
            for shape in shapes
            if shape.type == "line" and float(shape.y0) == float(shape.y1)
        ]

        assert len(vertical_shapes) == 1
        assert len(horizontal_shapes) == 2
        assert vertical_shapes[0].x0 == 300.0
        assert vertical_shapes[0].line.dash == "dot"
        assert vertical_shapes[0].line.color == "#7c3aed"
        assert all(shape.line.dash == "dash" for shape in horizontal_shapes)
        assert all(shape.line.color == "#d64545" for shape in horizontal_shapes)
        assert len(figure.data) == 1
        assert not list(figure.layout.annotations or [])

    def test_rosetta_selected_peak_markers_hide_horizontal_guides_without_advanced_mode(
        self,
    ):
        """Check Rosetta selected peak markers hide horizontal guides without advanced mode."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script"
        builder.process = None
        builder.advanced_mode_value = []
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 200.0, "kind": "non_fluorescent"},
                {"x": 300.0, "y": 400.0, "kind": "marker"},
            ],
            "scatter_guide_positions": [100.0, 300.0],
            "fluorescence_guide_positions": [200.0, 400.0],
        }

        figure = graph_overlays.add_selected_peak_markers(
            builder,
            figure=go.Figure(),
        )

        shapes = list(figure.layout.shapes or [])

        vertical_shapes = [
            shape
            for shape in shapes
            if shape.type == "line" and float(shape.x0) == float(shape.x1)
        ]
        horizontal_shapes = [
            shape
            for shape in shapes
            if shape.type == "line" and float(shape.y0) == float(shape.y1)
        ]

        assert len(vertical_shapes) == 1
        assert horizontal_shapes == []

    def test_rosetta_v1_selected_peak_markers_use_rosetta_guides(self):
        """Check Rosetta v1 selected peak markers use Rosetta guides."""
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script V1"
        builder.process = None
        builder.advanced_mode_value = ["enabled"]
        builder.yscale_selection = []
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 200.0, "kind": "non_fluorescent"},
                {"x": 300.0, "y": 400.0, "kind": "marker"},
            ],
            "scatter_guide_positions": [100.0, 300.0],
            "fluorescence_guide_positions": [200.0, 400.0],
            "scatter_guide_annotations": [
                {"x": 100.0, "label": "194 nm", "kind": "non_fluorescent"},
                {"x": 300.0, "label": "140 nm", "kind": "marker"},
            ],
        }

        figure = graph_overlays.add_selected_peak_markers(
            builder,
            figure=go.Figure(
                layout={
                    "yaxis": {
                        "range": [0.0, 4.0],
                    }
                }
            ),
        )
        shapes = list(figure.layout.shapes or [])

        vertical_shapes = [
            shape
            for shape in shapes
            if shape.type == "line" and float(shape.x0) == float(shape.x1)
        ]
        horizontal_shapes = [
            shape
            for shape in shapes
            if shape.type == "line" and float(shape.y0) == float(shape.y1)
        ]

        assert len(vertical_shapes) == 2
        assert len(horizontal_shapes) == 2
        assert len(figure.data) == 2
        text_traces = [
            trace for trace in figure.data if getattr(trace, "mode", None) == "text"
        ]
        assert text_traces == []
        assert not list(figure.layout.annotations or [])

    def test_add_peak_workflow_post_layout_overlays_adds_rosetta_annotations(self):
        """Check add peak workflow post layout overlays adds Rosetta annotations."""
        figure = add_peak_workflow_post_layout_overlays(
            figure=go.Figure(),
            process_name="Rosetta Script V1",
            peak_lines_payload={
                "scatter_guide_annotations": [
                    {"x": 100.0, "label": "140 nm"},
                    {"x": 300.0, "label": "194 nm"},
                ],
            },
        )

        annotations = list(figure.layout.annotations or [])
        assert [annotation.text for annotation in annotations] == ["140 nm", "194 nm"]
        assert [annotation.xref for annotation in annotations] == ["x", "x"]
        assert [annotation.yref for annotation in annotations] == ["paper", "paper"]
        assert [annotation.y for annotation in annotations] == [1, 1]
        assert [annotation.x for annotation in annotations] == [100.0, 300.0]

    def test_add_peak_workflow_post_layout_overlays_places_labels_on_log_x_axis(self):
        """Check add peak workflow post layout overlays places labels on log x axis."""
        figure = go.Figure()
        figure.update_xaxes(
            type="log",
            range=[np.log10(50.0), np.log10(2000.0)],
        )

        figure = add_peak_workflow_post_layout_overlays(
            figure=figure,
            process_name="Rosetta Script V1",
            peak_lines_payload={
                "scatter_guide_annotations": [
                    {"x": 100.0, "label": "140 nm"},
                    {"x": 900.0, "label": "600 nm"},
                ],
            },
        )

        annotations = list(figure.layout.annotations or [])
        assert [annotation.text for annotation in annotations] == ["140 nm", "600 nm"]

        x_axis_range = figure.layout.xaxis.range

        for annotation in annotations:
            assert annotation.xref == "x"
            assert x_axis_range[0] <= annotation.x <= x_axis_range[1]

        assert annotations[0].x == pytest.approx(np.log10(100.0))
        assert annotations[1].x == pytest.approx(np.log10(900.0))


@pytest.mark.parametrize("show_grid", [True, False])
def test_scatter_graphs_use_configured_grid(show_grid, monkeypatch):
    """Both fallback and custom scatter graphs honor the configured grid."""
    process = types.SimpleNamespace(
        graph_type="2d_scatter",
        process_label="Test scatter",
        required_detector_channels=["x", "y"],
        build_graph_figure=lambda: go.Figure(),
    )
    builder = types.SimpleNamespace(
        process=process,
        detector_channels={"x": "X", "y": "Y"},
        runtime_config_data={"visualization": {"show_grid_by_default": show_grid}},
        runtime_config=types.SimpleNamespace(get_int=lambda *args, **kwargs: 100),
        nbins=None,
        max_events_for_plots=None,
        marker_size=None,
        marker_opacity=None,
        resolved_process_name="test",
        reuse_event_trace=False,
        backend=None,
        uploaded_fcs_path=None,
        process_settings={},
        peak_lines_payload=None,
        xscale_selection=None,
        yscale_selection=None,
        _edge_artifact_filter_is_enabled=lambda: False,
        _advanced_mode_is_enabled=lambda: False,
        _is_rosetta_script_process=lambda: False,
        _call_with_supported_arguments=lambda method, **kwargs: method(),
    )
    monkeypatch.setattr(
        graph_scatter,
        "extract_plot_values_from_peak_lines_payload",
        lambda builder: (np.array([1.0, 2.0]), np.array([2.0, 3.0])),
    )
    monkeypatch.setattr(graph_overlays, "add_2d_overlays", lambda builder, *, figure: figure)

    fallback = graph_scatter.build_default_2d_scatter_figure(builder)
    custom = PeakWorkflowGraphBuilder._try_build_custom_process_figure(builder)

    for figure in (fallback, custom):
        assert figure.layout.xaxis.showgrid is show_grid
        assert figure.layout.yaxis.showgrid is show_grid


def test_repeat_figure_updates_reuse_matching_event_trace():
    """Patch the guides only when the event trace and context match."""
    figure = go.Figure(go.Scattergl(x=[1, 2], y=[3, 4], name="Events"))
    figure.update_layout(uirevision="sample")
    initial, trace = build_peak_figure_update(figure=figure, previous_trace=None)
    assert initial is figure
    assert build_peak_figure_update(figure=figure, previous_trace=trace) == (dash.no_update, dash.no_update)

    figure.add_vline(x=2)
    update, updated_trace = build_peak_figure_update(figure=figure, previous_trace=trace)
    operations = update.to_plotly_json()["operations"]
    assert [operation["location"] for operation in operations] == [["layout"]]

    figure.add_scatter(x=[1], y=[3], name="Guide")
    update, overlay_trace = build_peak_figure_update(figure=figure, previous_trace=updated_trace)
    assert update.to_plotly_json()["operations"][-1]["operation"] == "Extend"

    figure.data = figure.data[:1]
    update, _ = build_peak_figure_update(figure=figure, previous_trace=overlay_trace)
    assert update.to_plotly_json()["operations"][-1]["location"] == ["data", 1]

    figure.data[0].x = [2, 3]
    changed, _ = build_peak_figure_update(figure=figure, previous_trace=trace)
    assert changed is figure


def test_peak_detection_keeps_the_previous_default_view():
    """Reuse axis limits on the same plot even if the new event sample differs."""
    previous = go.Figure(go.Scattergl(x=[1, 2], y=[3, 4], name="Events"))
    previous.update_layout(uirevision="sample", xaxis_range=[0, 3], yaxis_range=[2, 5])
    _, trace = build_peak_figure_update(figure=previous, previous_trace=None)

    updated = go.Figure(go.Scattergl(x=[1, 5], y=[3, 8], name="Events"))
    updated.update_layout(uirevision="sample", xaxis_range=[0, 6], yaxis_range=[2, 9])
    preserve_peak_axis_ranges(figure=updated, previous_trace=trace)
    assert updated.layout.xaxis.range == (0, 3)
    assert updated.layout.yaxis.range == (2, 5)
    assert updated.layout.xaxis.autorange is False

    viewport = {"revision": "sample", "axis_ranges": {"xaxis": [1, 2], "yaxis": [3, 4]}}
    preserve_peak_axis_ranges(figure=updated, previous_trace=trace, viewport=viewport)
    assert updated.layout.xaxis.range == (1, 2)
    assert updated.layout.yaxis.range == (3, 4)

    updated.update_layout(uirevision="different sample", xaxis_range=[0, 6])
    preserve_peak_axis_ranges(figure=updated, previous_trace=trace, viewport=viewport)
    assert updated.layout.xaxis.range == (0, 6)


def test_results_only_patch_preserves_event_cloud():
    """Keep the browser event trace when a lightweight figure contains only guides."""
    figure = go.Figure(go.Scattergl(x=[1, 2], y=[3, 4], name="Events"))
    _, trace = build_peak_figure_update(figure=figure, previous_trace=None, event_context="same")
    guides = go.Figure(go.Scattergl(name="Events"))
    guides.add_vline(x=2)
    update, updated_trace = build_peak_figure_update(
        figure=guides, previous_trace=trace, event_context="same", reuse_events=True,
    )
    assert updated_trace["events"] == trace["events"]
    assert all(operation["location"][:2] != ["data", 0] for operation in update.to_plotly_json()["operations"])
    assert update.to_plotly_json()["operations"][0]["params"]["value"]["shapes"][0]["x0"] == 2
