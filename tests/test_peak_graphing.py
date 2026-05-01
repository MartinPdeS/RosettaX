# -*- coding: utf-8 -*-

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import plotly.graph_objs as go

from RosettaX.workflow.peak.core.graphing import (
    is_enabled,
    scale_selection_is_log
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
        # Test idempotency
        for _ in range(5):
            assert is_enabled("enabled") is True
            assert is_enabled("disabled") is False
            assert scale_selection_is_log("log") is True
            assert scale_selection_is_log("linear") is False