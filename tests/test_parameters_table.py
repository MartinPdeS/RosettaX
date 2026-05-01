# -*- coding: utf-8 -*-

import pytest
from unittest.mock import patch, Mock

from RosettaX.workflow.parameters.table import (
    MIE_MODEL_SOLID_SPHERE,
    MIE_MODEL_CORE_SHELL_SPHERE,
    COLUMN_PARTICLE_DIAMETER_NM,
    COLUMN_CORE_DIAMETER_NM,
    COLUMN_SHELL_THICKNESS_NM,
    COLUMN_OUTER_DIAMETER_NM,
    COLUMN_MEASURED_PEAK_POSITION,
    COLUMN_EXPECTED_COUPLING,
    sphere_table_columns,
    core_shell_table_columns,
    resolve_mie_model,
    get_table_columns_for_model,
    get_user_data_column_ids_for_model
)


class Test_ModelConstants:
    """Test suite for model constants."""

    def test_mie_model_constants(self):
        """Test Mie model constants are correctly defined."""
        assert MIE_MODEL_SOLID_SPHERE == "Solid Sphere"
        assert MIE_MODEL_CORE_SHELL_SPHERE == "Core/Shell Sphere"

    def test_column_constants(self):
        """Test column ID constants are correctly defined."""
        assert COLUMN_PARTICLE_DIAMETER_NM == "particle_diameter_nm"
        assert COLUMN_CORE_DIAMETER_NM == "core_diameter_nm"
        assert COLUMN_SHELL_THICKNESS_NM == "shell_thickness_nm"
        assert COLUMN_OUTER_DIAMETER_NM == "outer_diameter_nm"
        assert COLUMN_MEASURED_PEAK_POSITION == "measured_peak_position"
        assert COLUMN_EXPECTED_COUPLING == "expected_coupling"


class Test_table_columns:
    """Test suite for table column definitions."""

    def test_sphere_table_columns_structure(self):
        """Test sphere_table_columns has correct structure."""
        assert isinstance(sphere_table_columns, list)
        assert len(sphere_table_columns) == 3
        
        # Check each column has required fields
        for column in sphere_table_columns:
            assert isinstance(column, dict)
            assert "name" in column
            assert "id" in column
            assert "editable" in column
            assert isinstance(column["name"], str)
            assert isinstance(column["id"], str)
            assert isinstance(column["editable"], bool)

    def test_sphere_table_columns_content(self):
        """Test sphere_table_columns has correct content."""
        # Check specific columns exist
        column_ids = [col["id"] for col in sphere_table_columns]
        assert COLUMN_PARTICLE_DIAMETER_NM in column_ids
        assert COLUMN_MEASURED_PEAK_POSITION in column_ids
        assert COLUMN_EXPECTED_COUPLING in column_ids

        # Check editability
        for column in sphere_table_columns:
            if column["id"] == COLUMN_EXPECTED_COUPLING:
                assert column["editable"] is False
            else:
                assert column["editable"] is True

    def test_core_shell_table_columns_structure(self):
        """Test core_shell_table_columns has correct structure."""
        assert isinstance(core_shell_table_columns, list)
        assert len(core_shell_table_columns) == 5
        
        # Check each column has required fields
        for column in core_shell_table_columns:
            assert isinstance(column, dict)
            assert "name" in column
            assert "id" in column
            assert "editable" in column

    def test_core_shell_table_columns_content(self):
        """Test core_shell_table_columns has correct content."""
        column_ids = [col["id"] for col in core_shell_table_columns]
        assert COLUMN_CORE_DIAMETER_NM in column_ids
        assert COLUMN_SHELL_THICKNESS_NM in column_ids
        assert COLUMN_OUTER_DIAMETER_NM in column_ids
        assert COLUMN_MEASURED_PEAK_POSITION in column_ids
        assert COLUMN_EXPECTED_COUPLING in column_ids

        # Check which columns are editable
        editable_columns = {col["id"]: col["editable"] for col in core_shell_table_columns}
        assert editable_columns[COLUMN_CORE_DIAMETER_NM] is True
        assert editable_columns[COLUMN_SHELL_THICKNESS_NM] is True
        assert editable_columns[COLUMN_OUTER_DIAMETER_NM] is False  # Calculated field
        assert editable_columns[COLUMN_MEASURED_PEAK_POSITION] is True
        assert editable_columns[COLUMN_EXPECTED_COUPLING] is False  # Calculated field

    def test_table_columns_immutability(self):
        """Test that modifying returned columns doesn't affect originals."""
        # Modifying the returned list should not affect the original
        columns_copy = list(sphere_table_columns)
        columns_copy.append({"name": "Extra", "id": "extra", "editable": True})
        
        assert len(sphere_table_columns) == 3  # Original unchanged


class Test_resolve_mie_model:
    """Test suite for resolve_mie_model function."""

    def test_resolve_mie_model_solid_sphere(self):
        """Test resolve_mie_model with solid sphere input."""
        result = resolve_mie_model(MIE_MODEL_SOLID_SPHERE)
        assert result == MIE_MODEL_SOLID_SPHERE

    def test_resolve_mie_model_core_shell_sphere(self):
        """Test resolve_mie_model with core-shell sphere input."""
        result = resolve_mie_model(MIE_MODEL_CORE_SHELL_SPHERE)
        assert result == MIE_MODEL_CORE_SHELL_SPHERE

    def test_resolve_mie_model_none(self):
        """Test resolve_mie_model with None input falls back to solid sphere."""
        result = resolve_mie_model(None)
        assert result == MIE_MODEL_SOLID_SPHERE

    def test_resolve_mie_model_empty_string(self):
        """Test resolve_mie_model with empty string falls back to solid sphere."""
        result = resolve_mie_model("")
        assert result == MIE_MODEL_SOLID_SPHERE
        
        result = resolve_mie_model("   ")
        assert result == MIE_MODEL_SOLID_SPHERE

    def test_resolve_mie_model_unknown_string(self):
        """Test resolve_mie_model with unknown string falls back to solid sphere."""
        result = resolve_mie_model("Unknown Model")
        assert result == MIE_MODEL_SOLID_SPHERE
        
        result = resolve_mie_model("random text")
        assert result == MIE_MODEL_SOLID_SPHERE

    def test_resolve_mie_model_numeric_input(self):
        """Test resolve_mie_model with numeric input."""
        result = resolve_mie_model(123)
        assert result == MIE_MODEL_SOLID_SPHERE
        
        result = resolve_mie_model(0)
        assert result == MIE_MODEL_SOLID_SPHERE

    def test_resolve_mie_model_case_sensitive(self):
        """Test resolve_mie_model is case sensitive."""
        result = resolve_mie_model("core/shell sphere")
        assert result == MIE_MODEL_SOLID_SPHERE  # Case doesn't match
        
        result = resolve_mie_model("CORE/SHELL SPHERE")
        assert result == MIE_MODEL_SOLID_SPHERE  # Case doesn't match

    def test_resolve_mie_model_whitespace_handling(self):
        """Test resolve_mie_model handles whitespace correctly."""
        result = resolve_mie_model(f"  {MIE_MODEL_CORE_SHELL_SPHERE}  ")
        assert result == MIE_MODEL_CORE_SHELL_SPHERE

    @pytest.mark.parametrize("input_value,expected", [
        (MIE_MODEL_SOLID_SPHERE, MIE_MODEL_SOLID_SPHERE),
        (MIE_MODEL_CORE_SHELL_SPHERE, MIE_MODEL_CORE_SHELL_SPHERE),
        (None, MIE_MODEL_SOLID_SPHERE),
        ("", MIE_MODEL_SOLID_SPHERE),
        ("  ", MIE_MODEL_SOLID_SPHERE),
        ("invalid", MIE_MODEL_SOLID_SPHERE),
        (123, MIE_MODEL_SOLID_SPHERE),
        ([], MIE_MODEL_SOLID_SPHERE),
    ])
    def test_resolve_mie_model_parametrized(self, input_value, expected):
        """Parametrized test for resolve_mie_model with various inputs."""
        result = resolve_mie_model(input_value)
        assert result == expected


class Test_get_table_columns_for_model:
    """Test suite for get_table_columns_for_model function."""

    def test_get_table_columns_for_solid_sphere(self):
        """Test get_table_columns_for_model with solid sphere model."""
        result = get_table_columns_for_model(MIE_MODEL_SOLID_SPHERE)
        
        assert isinstance(result, list)
        assert len(result) == len(sphere_table_columns)
        
        # Verify columns are returned and are copies
        for i, column in enumerate(result):
            assert column == sphere_table_columns[i]
            assert column is not sphere_table_columns[i]  # Should be copies

    def test_get_table_columns_for_core_shell(self):
        """Test get_table_columns_for_model with core-shell sphere model."""
        result = get_table_columns_for_model(MIE_MODEL_CORE_SHELL_SPHERE)
        
        assert isinstance(result, list)
        assert len(result) == len(core_shell_table_columns)
        
        # Verify columns are returned and are copies
        for i, column in enumerate(result):
            assert column == core_shell_table_columns[i]
            assert column is not core_shell_table_columns[i]  # Should be copies

    def test_get_table_columns_for_unknown_model(self):
        """Test get_table_columns_for_model with unknown model falls back to solid sphere."""
        result = get_table_columns_for_model("Unknown Model")
        
        assert len(result) == len(sphere_table_columns)

    def test_get_table_columns_for_model_none(self):
        """Test get_table_columns_for_model with None input."""
        result = get_table_columns_for_model(None)
        
        assert len(result) == len(sphere_table_columns)

    def test_get_table_columns_modifications_isolated(self):
        """Test that modifications to returned columns don't affect originals."""
        result = get_table_columns_for_model(MIE_MODEL_SOLID_SPHERE)
        
        # Modify the returned columns
        result[0]["name"] = "Modified Name"
        result[0]["extra_field"] = "extra_value"
        
        # Original should be unchanged
        original_name = sphere_table_columns[0]["name"]
        assert original_name != "Modified Name"
        assert "extra_field" not in sphere_table_columns[0]


class Test_get_user_data_column_ids_for_model:
    """Test suite for get_user_data_column_ids_for_model function."""

    @patch('RosettaX.workflow.parameters.table.table_services.get_column_ids')
    def test_get_user_data_column_ids_for_solid_sphere(self, mock_get_column_ids):
        """Test get_user_data_column_ids_for_model with solid sphere model."""
        mock_get_column_ids.return_value = ["particle_diameter_nm", "measured_peak_position", "expected_coupling"]
        
        result = get_user_data_column_ids_for_model(MIE_MODEL_SOLID_SPHERE)
        
        assert result == ["particle_diameter_nm", "measured_peak_position", "expected_coupling"]
        mock_get_column_ids.assert_called_once()
        
        # Verify the correct columns were passed to the service
        call_args = mock_get_column_ids.call_args[1]
        columns = call_args['columns']
        assert len(columns) == len(sphere_table_columns)

    @patch('RosettaX.workflow.parameters.table.table_services.get_column_ids')
    def test_get_user_data_column_ids_for_core_shell(self, mock_get_column_ids):
        """Test get_user_data_column_ids_for_model with core-shell sphere model."""
        expected_ids = [
            "core_diameter_nm", "shell_thickness_nm", "outer_diameter_nm", 
            "measured_peak_position", "expected_coupling"
        ]
        mock_get_column_ids.return_value = expected_ids
        
        result = get_user_data_column_ids_for_model(MIE_MODEL_CORE_SHELL_SPHERE)
        
        assert result == expected_ids
        mock_get_column_ids.assert_called_once()
        
        # Verify the correct columns were passed to the service
        call_args = mock_get_column_ids.call_args[1]
        columns = call_args['columns']
        assert len(columns) == len(core_shell_table_columns)

    @patch('RosettaX.workflow.parameters.table.table_services.get_column_ids')
    def test_get_user_data_column_ids_for_unknown_model(self, mock_get_column_ids):
        """Test get_user_data_column_ids_for_model with unknown model."""
        mock_get_column_ids.return_value = ["particle_diameter_nm", "measured_peak_position", "expected_coupling"]
        
        result = get_user_data_column_ids_for_model("Unknown Model")
        
        # Should fall back to solid sphere
        assert len(result) == 3  # Solid sphere has 3 columns
        mock_get_column_ids.assert_called_once()


class Test_table_integration:
    """Integration tests for table functions working together."""

    def test_model_resolution_and_columns_consistency(self):
        """Test that model resolution and column retrieval are consistent."""
        # Test solid sphere consistency
        resolved_model = resolve_mie_model("some unknown model")
        columns = get_table_columns_for_model(resolved_model)
        
        assert resolved_model == MIE_MODEL_SOLID_SPHERE
        assert len(columns) == 3
        
        # Test core-shell consistency
        resolved_model = resolve_mie_model(MIE_MODEL_CORE_SHELL_SPHERE)
        columns = get_table_columns_for_model(resolved_model)
        
        assert resolved_model == MIE_MODEL_CORE_SHELL_SPHERE
        assert len(columns) == 5

    def test_all_columns_have_required_structure(self):
        """Test that all columns from both models have required structure."""
        models = [MIE_MODEL_SOLID_SPHERE, MIE_MODEL_CORE_SHELL_SPHERE]
        
        for model in models:
            columns = get_table_columns_for_model(model)
            
            for column in columns:
                # Every column should have these fields
                assert "name" in column
                assert "id" in column  
                assert "editable" in column
                
                # Field types should be correct
                assert isinstance(column["name"], str)
                assert isinstance(column["id"], str)
                assert isinstance(column["editable"], bool)
                
                # Names and IDs should not be empty
                assert len(column["name"]) > 0
                assert len(column["id"]) > 0

    @patch('RosettaX.workflow.parameters.table.table_services.get_column_ids')
    def test_column_ids_extraction_consistency(self, mock_get_column_ids):
        """Test that column ID extraction is consistent with column definitions."""
        mock_get_column_ids.return_value = ["id1", "id2", "id3"]
        
        # Test with both models
        for model in [MIE_MODEL_SOLID_SPHERE, MIE_MODEL_CORE_SHELL_SPHERE]:
            column_ids = get_user_data_column_ids_for_model(model)
            
            # Should return the mocked IDs
            assert column_ids == ["id1", "id2", "id3"]
            
        # Service should have been called twice
        assert mock_get_column_ids.call_count == 2