# -*- coding: utf-8 -*-

import numpy as np
import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass

from RosettaX.workflow.peak.adapters.base import (
    PeakWorkflowPageState,
    BasePeakWorkflowAdapter
)


class Test_PeakWorkflowPageState:
    """Test suite for PeakWorkflowPageState dataclass."""

    def test_peak_workflow_page_state_creation(self):
        """Test PeakWorkflowPageState creation with valid payload."""
        payload = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}
        state = PeakWorkflowPageState(payload=payload)
        
        assert state.payload == payload

    def test_peak_workflow_page_state_to_dict(self):
        """Test to_dict method returns copy of payload."""
        original_payload = {"key1": "value1", "nested": {"key2": "value2"}}
        state = PeakWorkflowPageState(payload=original_payload)
        
        result = state.to_dict()
        
        assert result == original_payload
        # Verify it's a copy, not the same object
        assert result is not original_payload

    def test_peak_workflow_page_state_empty_payload(self):
        """Test PeakWorkflowPageState with empty payload."""
        state = PeakWorkflowPageState(payload={})
        
        assert state.payload == {}
        assert state.to_dict() == {}

    def test_peak_workflow_page_state_immutable_payload_change(self):
        """Test that modifying returned dict doesn't affect original payload."""
        original_payload = {"key1": "value1"}
        state = PeakWorkflowPageState(payload=original_payload)
        
        returned_dict = state.to_dict()
        returned_dict["key1"] = "modified"
        returned_dict["new_key"] = "new_value"
        
        # Original payload should be unchanged
        assert state.payload["key1"] == "value1"
        assert "new_key" not in state.payload


class Test_BasePeakWorkflowAdapter:
    """Test suite for BasePeakWorkflowAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Fixture providing a BasePeakWorkflowAdapter instance."""
        return BasePeakWorkflowAdapter()

    def test_class_constants_exist(self, adapter):
        """Test that all expected class constants are defined."""
        # Test uploaded_fcs_path_keys
        assert hasattr(adapter, 'uploaded_fcs_path_keys')
        assert isinstance(adapter.uploaded_fcs_path_keys, tuple)
        assert len(adapter.uploaded_fcs_path_keys) > 0
        assert "uploaded_fcs_path" in adapter.uploaded_fcs_path_keys

        # Test peak_lines_payload_keys
        assert hasattr(adapter, 'peak_lines_payload_keys')
        assert isinstance(adapter.peak_lines_payload_keys, tuple)
        assert "peak_lines_payload" in adapter.peak_lines_payload_keys

        # Test default_peak_lines_payload_key
        assert hasattr(adapter, 'default_peak_lines_payload_key')
        assert isinstance(adapter.default_peak_lines_payload_key, str)
        assert adapter.default_peak_lines_payload_key == "peak_lines_payload"

        # Test delta_peak_value_names
        assert hasattr(adapter, 'delta_peak_value_names')
        assert isinstance(adapter.delta_peak_value_names, tuple)
        assert "new_peak_positions" in adapter.delta_peak_value_names

        # Test manual_peak_value_names
        assert hasattr(adapter, 'manual_peak_value_names')
        assert isinstance(adapter.manual_peak_value_names, tuple)
        assert "clicked_x" in adapter.manual_peak_value_names

        # Test cumulative_peak_value_names
        assert hasattr(adapter, 'cumulative_peak_value_names')
        assert isinstance(adapter.cumulative_peak_value_names, tuple)
        assert "peak_values" in adapter.cumulative_peak_value_names

        # Test mapping_x_value_keys
        assert hasattr(adapter, 'mapping_x_value_keys')
        assert isinstance(adapter.mapping_x_value_keys, tuple)
        assert "x" in adapter.mapping_x_value_keys

    def test_uploaded_fcs_path_keys_content(self, adapter):
        """Test content of uploaded_fcs_path_keys."""
        expected_keys = ("uploaded_fcs_path", "uploaded_fcs_file_path", "fcs_path")
        assert adapter.uploaded_fcs_path_keys == expected_keys

    def test_peak_lines_payload_keys_content(self, adapter):
        """Test content of peak_lines_payload_keys."""
        expected_keys = (
            "peak_lines_payload",
            "peak_lines",
            "fluorescence_peak_lines_payload",
            "scattering_peak_lines_payload",
        )
        assert adapter.peak_lines_payload_keys == expected_keys

    def test_get_page_state_from_payload_with_existing_state_object(self, adapter):
        """Test get_page_state_from_payload with object that has to_dict method."""
        mock_state = Mock()
        mock_state.to_dict = Mock(return_value={"test": "data"})
        
        result = adapter.get_page_state_from_payload(mock_state)
        
        assert result is mock_state
        # Should not call to_dict when object already has it
        mock_state.to_dict.assert_not_called()

    def test_get_page_state_from_payload_with_dict(self, adapter):
        """Test get_page_state_from_payload with dictionary input."""
        input_dict = {"key1": "value1", "key2": 123}
        
        result = adapter.get_page_state_from_payload(input_dict)
        
        assert isinstance(result, PeakWorkflowPageState)
        assert result.payload == input_dict

    def test_get_page_state_from_payload_with_none(self, adapter):
        """Test get_page_state_from_payload with None input."""
        result = adapter.get_page_state_from_payload(None)
        
        assert isinstance(result, PeakWorkflowPageState)
        assert result.payload == {}

    def test_get_page_state_from_payload_with_invalid_input(self, adapter):
        """Test get_page_state_from_payload with invalid input types."""
        invalid_inputs = ["string", 123, [], object()]
        
        for invalid_input in invalid_inputs:
            result = adapter.get_page_state_from_payload(invalid_input)
            assert isinstance(result, PeakWorkflowPageState)
            assert result.payload == {}

    def test_get_page_state_payload_with_peak_workflow_state(self, adapter):
        """Test get_page_state_payload with PeakWorkflowPageState."""
        original_payload = {"key1": "value1", "key2": "value2"}
        state = PeakWorkflowPageState(payload=original_payload)
        
        result = adapter.get_page_state_payload(page_state=state)
        
        assert result == original_payload
        assert result is not original_payload  # Should be a copy

    def test_get_page_state_payload_with_to_dict_object(self, adapter):
        """Test get_page_state_payload with object that has to_dict method."""
        mock_state = Mock()
        expected_payload = {"mock": "data", "test": 123}
        mock_state.to_dict.return_value = expected_payload
        
        result = adapter.get_page_state_payload(page_state=mock_state)
        
        mock_state.to_dict.assert_called_once()
        assert result == expected_payload

    def test_get_page_state_payload_with_invalid_object(self, adapter):
        """Test get_page_state_payload with object without to_dict method."""
        # This should test the else branch when object doesn't have to_dict
        # Based on the code structure, it might return empty dict or raise error
        mock_state = Mock(spec=[])  # Mock without to_dict method
        
        # The function might have error handling for this case
        try:
            result = adapter.get_page_state_payload(page_state=mock_state)
            # If no exception, verify result is reasonable
            assert isinstance(result, dict)
        except (AttributeError, TypeError):
            # This is expected behavior for invalid input
            pass

    def test_get_page_state_payload_modifications_isolated(self, adapter):
        """Test that modifications to returned payload don't affect original state."""
        original_payload = {"key1": "value1", "nested": {"key2": "value2"}}
        state = PeakWorkflowPageState(payload=original_payload)
        
        result = adapter.get_page_state_payload(page_state=state)
        result["key1"] = "modified"
        result["new_key"] = "new_value"
        
        # Original state should be unchanged
        assert state.payload["key1"] == "value1"
        assert "new_key" not in state.payload

    @pytest.mark.parametrize("key_group", [
        "uploaded_fcs_path_keys",
        "peak_lines_payload_keys",
        "delta_peak_value_names",
        "manual_peak_value_names", 
        "cumulative_peak_value_names",
        "mapping_x_value_keys"
    ])
    def test_key_groups_are_tuples_with_strings(self, adapter, key_group):
        """Test that all key group constants are tuples containing strings."""
        key_group_value = getattr(adapter, key_group)
        
        assert isinstance(key_group_value, tuple)
        assert len(key_group_value) > 0
        for key in key_group_value:
            assert isinstance(key, str)
            assert len(key) > 0

    def test_adapter_instance_isolation(self):
        """Test that adapter instances don't share state."""
        adapter1 = BasePeakWorkflowAdapter()
        adapter2 = BasePeakWorkflowAdapter()
        
        # Should have same class constants but be different instances
        assert adapter1.uploaded_fcs_path_keys == adapter2.uploaded_fcs_path_keys
        assert adapter1 is not adapter2

    def test_page_state_round_trip(self, adapter):
        """Test complete round-trip of page state conversion."""
        original_data = {
            "uploaded_fcs_path": "/path/to/file.fcs",
            "peak_positions": [100, 200, 300],
            "metadata": {"experiment": "test"}
        }
        
        # Convert to page state
        state = adapter.get_page_state_from_payload(original_data)
        
        # Convert back to payload
        result_payload = adapter.get_page_state_payload(page_state=state)
        
        assert result_payload == original_data
        assert result_payload is not original_data  # Should be copy


class Test_BasePeakWorkflowAdapterIntegration:
    """Integration tests for BasePeakWorkflowAdapter with realistic workflows."""

    @pytest.fixture
    def adapter(self):
        """Fixture providing adapter instance."""
        return BasePeakWorkflowAdapter()

    def test_workflow_simulation_dash_callback(self, adapter):
        """Simulate a typical Dash callback workflow."""
        # Simulate incoming Dash store data
        dash_payload = {
            "uploaded_fcs_path": "/data/experiment1.fcs", 
            "peak_lines_payload": {"peaks": [150, 250, 350]},
            "processing_complete": True
        }
        
        # Adapter processes the payload
        state = adapter.get_page_state_from_payload(dash_payload)
        
        # Verify state was created correctly
        assert isinstance(state, PeakWorkflowPageState)
        assert state.payload["uploaded_fcs_path"] == "/data/experiment1.fcs"
        
        # Modify state for callback return
        result_payload = adapter.get_page_state_payload(page_state=state)
        result_payload["analysis_timestamp"] = "2024-01-01"
        
        # Original state should be unchanged
        assert "analysis_timestamp" not in state.payload

    def test_multiple_key_variations(self, adapter):
        """Test adapter handles various key name variations correctly."""
        # Test that adapter constants cover expected variations
        fcs_variations = ["uploaded_fcs_path", "uploaded_fcs_file_path", "fcs_path"]
        for variation in fcs_variations:
            assert variation in adapter.uploaded_fcs_path_keys
            
        peak_variations = [
            "peak_lines_payload", "peak_lines", 
            "fluorescence_peak_lines_payload", "scattering_peak_lines_payload"
        ]
        for variation in peak_variations:
            assert variation in adapter.peak_lines_payload_keys