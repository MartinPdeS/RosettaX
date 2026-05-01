# -*- coding: utf-8 -*-

import numpy as np
import pytest
from types import SimpleNamespace
from unittest.mock import patch, Mock
import logging

from RosettaX.workflow.parameters.model import (
    SOLID_SPHERE_MODEL_NAME,
    CORE_SHELL_SPHERE_MODEL_NAME,
    compute_model_for_rows
)


class Test_ModelConstants:
    """Test suite for model constants."""

    def test_solid_sphere_model_name(self):
        """Test solid sphere model name constant."""
        assert SOLID_SPHERE_MODEL_NAME == "Solid Sphere"

    def test_core_shell_sphere_model_name(self):
        """Test core-shell sphere model name constant."""
        assert CORE_SHELL_SPHERE_MODEL_NAME == "Core/Shell Sphere"


class Test_compute_model_for_rows:
    """Test suite for compute_model_for_rows function."""

    @pytest.fixture
    def valid_optical_parameters(self):
        """Fixture providing valid optical parameters."""
        return {
            'medium_refractive_index': 1.33,
            'particle_refractive_index': 1.59,
            'core_refractive_index': None,
            'shell_refractive_index': None,
            'wavelength_nm': 488.0,
            'detector_numerical_aperture': 1.2,
            'detector_cache_numerical_aperture': 0.5,
            'blocker_bar_numerical_aperture': 0.1,
            'detector_sampling': 1000,
            'detector_phi_angle_degree': 0.0,
            'detector_gamma_angle_degree': 90.0
        }

    @pytest.fixture
    def valid_solid_sphere_rows(self):
        """Fixture providing valid solid sphere rows."""
        return [
            {'particle_diameter_nm': 100.0, 'expected_coupling': ''},
            {'particle_diameter_nm': 200.0, 'expected_coupling': ''},
            {'particle_diameter_nm': 300.0, 'expected_coupling': ''}
        ]

    @pytest.fixture
    def valid_core_shell_rows(self):
        """Fixture providing valid core-shell sphere rows."""
        return [
            {'core_diameter_nm': 80.0, 'shell_thickness_nm': 10.0, 'expected_coupling': ''},
            {'core_diameter_nm': 160.0, 'shell_thickness_nm': 20.0, 'expected_coupling': ''},
            {'core_diameter_nm': 240.0, 'shell_thickness_nm': 30.0, 'expected_coupling': ''}
        ]

    @pytest.fixture
    def mock_logger(self):
        """Fixture providing a mock logger."""
        return Mock(spec=logging.Logger)

    @patch('RosettaX.workflow.parameters.model.table')
    @patch('RosettaX.workflow.parameters.model.BackEnd.compute_modeled_coupling_from_diameters')
    def test_compute_model_for_rows_solid_sphere_success(self, mock_compute_coupling, mock_table, valid_optical_parameters, 
                                                        valid_solid_sphere_rows, mock_logger):
        """Test compute_model_for_rows with valid solid sphere parameters."""
        mock_table.normalize_table_rows.return_value = [dict(row) for row in valid_solid_sphere_rows]
        mock_compute_coupling.return_value = SimpleNamespace(
            expected_coupling_values=np.asarray([1234.5, 2468.0, 3701.5], dtype=float)
        )

        result = compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
            logger=mock_logger,
            **valid_optical_parameters
        )

        mock_table.normalize_table_rows.assert_called_once_with(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
        )
        mock_compute_coupling.assert_called_once()
        
        assert len(result) == 3
        assert result[0]['expected_coupling'] == '1234.5'
        assert result[1]['expected_coupling'] == '2468'
        assert result[2]['expected_coupling'] == '3701.5'

    @patch('RosettaX.workflow.parameters.model.table')
    @patch('RosettaX.workflow.parameters.model.BackEnd.compute_modeled_coupling_from_core_shell_dimensions')
    def test_compute_model_for_rows_core_shell_sphere_success(self, mock_compute_coupling, mock_table, valid_optical_parameters, 
                                                             valid_core_shell_rows, mock_logger):
        """Test compute_model_for_rows with valid core-shell sphere parameters."""
        valid_optical_parameters.update({
            'particle_refractive_index': None,
            'core_refractive_index': 1.59,
            'shell_refractive_index': 1.45
        })

        mock_table.normalize_table_rows.return_value = [
            {
                'core_diameter_nm': row['core_diameter_nm'],
                'shell_thickness_nm': row['shell_thickness_nm'],
                'outer_diameter_nm': row['core_diameter_nm'] + (2 * row['shell_thickness_nm']),
                'expected_coupling': row['expected_coupling'],
            }
            for row in valid_core_shell_rows
        ]
        mock_compute_coupling.return_value = SimpleNamespace(
            expected_coupling_values=np.asarray([987.6, 1975.2, 2962.8], dtype=float)
        )

        result = compute_model_for_rows(
            mie_model=CORE_SHELL_SPHERE_MODEL_NAME,
            current_rows=valid_core_shell_rows,
            logger=mock_logger,
            **valid_optical_parameters
        )

        mock_table.normalize_table_rows.assert_called_once_with(
            mie_model=CORE_SHELL_SPHERE_MODEL_NAME,
            current_rows=valid_core_shell_rows,
        )
        mock_compute_coupling.assert_called_once()
        
        assert len(result) == 3
        assert result[0]['expected_coupling'] == '987.6'
        assert result[1]['expected_coupling'] == '1975.2'
        assert result[2]['expected_coupling'] == '2962.8'

    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_empty_rows(self, mock_table, valid_optical_parameters, mock_logger):
        """Test compute_model_for_rows with empty rows."""
        mock_table.normalize_table_rows_as_solid_sphere.return_value = []
        mock_table.compute_solid_sphere_model_for_normalized_rows.return_value = []

        result = compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=[],
            logger=mock_logger,
            **valid_optical_parameters
        )

        assert result == []

    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_none_rows(self, mock_table, valid_optical_parameters, mock_logger):
        """Test compute_model_for_rows with None rows."""
        mock_table.normalize_table_rows_as_solid_sphere.return_value = []
        mock_table.compute_solid_sphere_model_for_normalized_rows.return_value = []

        result = compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=None,
            logger=mock_logger,
            **valid_optical_parameters
        )

        assert result == []

    def test_compute_model_for_rows_invalid_mie_model(self, valid_optical_parameters, 
                                                     valid_solid_sphere_rows, mock_logger):
        """Unknown model names fall back to the solid sphere branch."""
        with patch('RosettaX.workflow.parameters.model.table.normalize_table_rows', return_value=[dict(row) for row in valid_solid_sphere_rows]) as mock_normalize, patch(
            'RosettaX.workflow.parameters.model.BackEnd.compute_modeled_coupling_from_diameters',
            return_value=SimpleNamespace(expected_coupling_values=np.asarray([1.0, 2.0, 3.0], dtype=float)),
        ):
            result = compute_model_for_rows(
                mie_model="Invalid Model",
                current_rows=valid_solid_sphere_rows,
                logger=mock_logger,
                **valid_optical_parameters
            )

        mock_normalize.assert_called_once_with(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
        )
        assert [row['expected_coupling'] for row in result] == ['1', '2', '3']

    @patch('RosettaX.workflow.parameters.model.as_required_float')
    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_parameter_validation(self, mock_table, mock_as_required_float,
                                                        valid_optical_parameters, valid_solid_sphere_rows, mock_logger):
        """Test that compute_model_for_rows validates parameters using casting functions."""
        # Mock the casting functions
        mock_as_required_float.side_effect = lambda x, name: float(x) if x is not None else None
        
        mock_table.normalize_table_rows.return_value = valid_solid_sphere_rows

        compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
            logger=mock_logger,
            **valid_optical_parameters
        )

        # Verify that casting functions are called for validation
        assert mock_as_required_float.call_count > 0

    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_rows_with_invalid_data(self, mock_table, valid_optical_parameters, mock_logger):
        """Test compute_model_for_rows with rows containing invalid data."""
        invalid_rows = [
            {'particle_diameter_nm': 'invalid', 'expected_coupling': ''},
            {'particle_diameter_nm': '', 'expected_coupling': ''},
            {'particle_diameter_nm': -100.0, 'expected_coupling': ''}  # Negative diameter
        ]

        mock_table.normalize_table_rows.return_value = [
            {'particle_diameter_nm': '', 'expected_coupling': ''},  # Invalid row cleared
            {'particle_diameter_nm': '', 'expected_coupling': ''},  # Invalid row cleared
            {'particle_diameter_nm': '', 'expected_coupling': ''}   # Invalid row cleared
        ]

        result = compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=invalid_rows,
            logger=mock_logger,
            **valid_optical_parameters
        )

        # Should return rows but with cleared expected_coupling for invalid entries
        assert len(result) == 3
        for row in result:
            assert row['expected_coupling'] == ''

    @pytest.mark.parametrize("missing_param", [
        'medium_refractive_index',
        'wavelength_nm',
        'detector_numerical_aperture',
        'detector_sampling'
    ])
    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_missing_required_parameters(self, mock_table, missing_param, 
                                                              valid_optical_parameters, 
                                                              valid_solid_sphere_rows, mock_logger):
        """Test compute_model_for_rows with missing required parameters."""
        # Remove a required parameter
        del valid_optical_parameters[missing_param]

        with pytest.raises(TypeError, match="missing.*required"):
            compute_model_for_rows(
                mie_model=SOLID_SPHERE_MODEL_NAME,
                current_rows=valid_solid_sphere_rows,
                logger=mock_logger,
                **valid_optical_parameters
            )

    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_logging(self, mock_table, valid_optical_parameters, 
                                          valid_solid_sphere_rows, mock_logger):
        """Test that compute_model_for_rows performs appropriate logging."""
        mock_table.normalize_table_rows.return_value = valid_solid_sphere_rows

        compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
            logger=mock_logger,
            **valid_optical_parameters
        )

        # Verify logger was used
        assert mock_logger.debug.called or mock_logger.info.called or mock_logger.warning.called

    @patch('RosettaX.workflow.parameters.model.table')
    def test_compute_model_for_rows_parameter_types(self, mock_table, mock_logger):
        """Test compute_model_for_rows handles different parameter types correctly."""
        # Test with string representations of numeric values (common in web forms)
        string_parameters = {
            'medium_refractive_index': '1.33',
            'particle_refractive_index': '1.59',
            'core_refractive_index': None,
            'shell_refractive_index': None,
            'wavelength_nm': '488.0',
            'detector_numerical_aperture': '1.2',
            'detector_cache_numerical_aperture': '0.5',
            'blocker_bar_numerical_aperture': '0.1',
            'detector_sampling': '1000',
            'detector_phi_angle_degree': '0.0',
            'detector_gamma_angle_degree': '90.0'
        }

        mock_table.normalize_table_rows.return_value = []

        # Should not raise type errors due to internal casting
        result = compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=[],
            logger=mock_logger,
            **string_parameters
        )

        assert result == []