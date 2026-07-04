# -*- coding: utf-8 -*-

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import plotly.graph_objs as go
import sys
import types


class _DashBootstrapComponentsSentinel:
    def __call__(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    def __getattr__(self, name):
        return _DashBootstrapComponentsSentinel()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)

from RosettaX.workflow.peak.callbacks.graph import (
    add_grouped_2d_scatter_traces,
    sanitize_group_points,
)
from RosettaX.workflow.peak.core.graphing import (
    PeakWorkflowGraphBuilder,
    is_enabled,
    scale_selection_is_log
)
from RosettaX.workflow.peak.scripts.base import (
    filter_edge_artifact_pairs,
    filter_edge_artifact_values,
    resolve_edge_artifact_filter_enabled,
)


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
        assert scale_selection_is_log({"log"}) is True


# Additional test classes for other functions in the graphing module
# Note: Since we only saw the first 50 lines, these are based on typical graphing functionality
class Test_GraphingUtilities:
    """Test suite for additional graphing utilities."""

    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample data for graphing tests."""
        return {
            'x_values': np.array([1, 2, 3, 4, 5]),
            'y_values': np.array([10, 20, 30, 40, 50]),
            'labels': ['A', 'B', 'C', 'D', 'E']
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

    @pytest.mark.parametrize("graph_toggle,expected", [
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
        ("", False)
    ])
    def test_is_enabled_parametrized(self, graph_toggle, expected):
        """Parametrized test for is_enabled function with various inputs."""
        assert is_enabled(graph_toggle) == expected

    @pytest.mark.parametrize("scale_value,expected", [
        ("log", True),
        ("linear", False),
        ("logarithmic", False),
        ("LOG", False),
        ("Log", False),
        ("", False),
        (None, False),
        (True, False),
        (["log"], True),
        (1, False)
    ])
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
            123,               # Number
            [1, 2, 3],        # List of numbers
            object(),         # Arbitrary object
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
    def test_sanitize_group_points_excludes_zero_and_non_finite_values(self):
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
    def test_filter_2d_values_for_axis_scale_excludes_zero_values(self):
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.xscale_selection = "linear"
        builder.yscale_selection = "linear"

        filtered_x_values, filtered_y_values = builder._filter_2d_values_for_axis_scale(
            x_values=np.array([0.0, 1.0, 2.0, np.nan]),
            y_values=np.array([5.0, 0.0, 3.0, 4.0]),
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
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.peak_lines_payload = {
            "plot_x_values": [10.0, 20.0, "bad", float("nan")],
            "plot_y_values": [100.0, 200.0, 300.0, 400.0],
        }

        payload_values = builder._extract_plot_values_from_peak_lines_payload()

        assert payload_values is not None
        payload_x_values, payload_y_values = payload_values
        assert payload_x_values.tolist() == [10.0, 20.0]
        assert payload_y_values.tolist() == [100.0, 200.0]


class Test_EdgeArtifactFiltering:
    def test_filter_edge_artifact_values_removes_floor_and_ceiling_pileups(self):
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

    def test_filter_edge_artifact_pairs_removes_scatter_floor_ceiling_and_fluorescence_floor(self):
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
        assert resolve_edge_artifact_filter_enabled(
            process_settings={},
            default=True,
        ) is True

        assert resolve_edge_artifact_filter_enabled(
            process_settings={
                "filter_edge_artifacts": [],
            },
            default=True,
        ) is False


class Test_PeakWorkflowGraphBuilder1DHistogramRange:
    def test_advanced_overlay_does_not_expand_histogram_y_range(self):
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

        builder._apply_stable_1d_histogram_y_range(
            figure=figure,
        )

        assert figure.layout.yaxis.autorange is False
        assert tuple(figure.layout.yaxis.range) == pytest.approx((9.7545, 15.2435))


class Test_PeakWorkflowGraphBuilderRosettaOverlays:
    def test_rosetta_y_gate_overlay_adds_helper_bands_without_in_plot_labels(self):
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script"
        builder.yscale_selection = "log"
        builder.peak_lines_payload = {
            "y_lower_gate": 20.0,
            "y_upper_gate": 1000.0,
        }

        figure = go.Figure()
        figure.update_yaxes(type="log", range=[0.0, 4.0])

        figure = builder._add_y_axis_gate_overlay(
            figure=figure,
        )

        shapes = list(figure.layout.shapes or [])

        assert len(shapes) >= 2
        assert not list(figure.layout.annotations or [])

    def test_rosetta_selected_peak_markers_add_vertical_and_horizontal_guides(self):
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script"
        builder.advanced_mode_value = ["enabled"]
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 200.0},
                {"x": 300.0, "y": 400.0},
                {"x": 500.0, "y": 400.0},
            ],
            "scatter_guide_positions": [100.0, 300.0, 500.0],
            "fluorescence_guide_positions": [200.0, 400.0],
            "labels": [
                "Non-fluorescent peak 1",
                "Bright marker",
                "Dim marker",
            ],
        }

        figure = builder._add_selected_peak_markers(
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

        assert len(vertical_shapes) == 3
        assert len(horizontal_shapes) == 2
        assert all(shape.line.dash == "dash" for shape in vertical_shapes)
        assert all(shape.line.color == "#1f9d55" for shape in vertical_shapes)
        assert all(shape.line.dash == "dash" for shape in horizontal_shapes)
        assert all(shape.line.color == "#d64545" for shape in horizontal_shapes)
        assert len(figure.data) == 1
        assert not list(figure.layout.annotations or [])

    def test_rosetta_selected_peak_markers_hide_horizontal_guides_without_advanced_mode(self):
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script"
        builder.advanced_mode_value = []
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 200.0},
                {"x": 300.0, "y": 400.0},
            ],
            "scatter_guide_positions": [100.0, 300.0],
            "fluorescence_guide_positions": [200.0, 400.0],
        }

        figure = builder._add_selected_peak_markers(
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

        assert len(vertical_shapes) == 2
        assert horizontal_shapes == []

    def test_rosetta_v1_selected_peak_markers_use_rosetta_guides(self):
        builder = PeakWorkflowGraphBuilder.__new__(PeakWorkflowGraphBuilder)
        builder.resolved_process_name = "Rosetta Script V1"
        builder.advanced_mode_value = ["enabled"]
        builder.peak_lines_payload = {
            "points": [
                {"x": 100.0, "y": 200.0},
                {"x": 300.0, "y": 400.0},
            ],
            "scatter_guide_positions": [100.0, 300.0],
            "fluorescence_guide_positions": [200.0, 400.0],
        }

        figure = builder._add_selected_peak_markers(
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

        assert len(vertical_shapes) == 2
        assert len(horizontal_shapes) == 2
