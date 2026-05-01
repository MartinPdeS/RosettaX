# -*- coding: utf-8 -*-

import numpy as np
import pytest
from dataclasses import FrozenInstanceError
from unittest.mock import patch, MagicMock

from RosettaX.workflow.calibration.scattering import (
    OpticalParameters,
    ParsedSphereStandardRows
)


class Test_OpticalParameters:
    """Test suite for OpticalParameters dataclass."""

    @pytest.fixture
    def valid_optical_params(self):
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
    def core_shell_optical_params(self):
        """Fixture providing core-shell sphere parameters."""
        return {
            'medium_refractive_index': 1.33,
            'particle_refractive_index': None,
            'core_refractive_index': 1.59,
            'shell_refractive_index': 1.45,
            'wavelength_nm': 488.0,
            'detector_numerical_aperture': 1.2,
            'detector_cache_numerical_aperture': 0.5,
            'blocker_bar_numerical_aperture': 0.1,
            'detector_sampling': 1000,
            'detector_phi_angle_degree': 0.0,
            'detector_gamma_angle_degree': 90.0
        }

    def test_optical_parameters_creation_with_defaults(self, valid_optical_params):
        """Test OpticalParameters creation with default values."""
        params = OpticalParameters(**valid_optical_params)
        
        assert params.medium_refractive_index == 1.33
        assert params.particle_refractive_index == 1.59
        assert params.core_refractive_index is None
        assert params.shell_refractive_index is None
        assert params.wavelength_nm == 488.0
        assert params.detector_numerical_aperture == 1.2
        assert params.detector_cache_numerical_aperture == 0.5
        assert params.blocker_bar_numerical_aperture == 0.1
        assert params.detector_sampling == 1000
        assert params.detector_phi_angle_degree == 0.0
        assert params.detector_gamma_angle_degree == 90.0
        # Test default values
        assert params.optical_power_watt == 1.0
        assert params.source_numerical_aperture == 0.1
        assert params.polarization_angle_degree == 0.0

    def test_optical_parameters_creation_with_custom_defaults(self, valid_optical_params):
        """Test OpticalParameters creation with custom default values."""
        valid_optical_params.update({
            'optical_power_watt': 2.5,
            'source_numerical_aperture': 0.2,
            'polarization_angle_degree': 45.0
        })
        
        params = OpticalParameters(**valid_optical_params)
        
        assert params.optical_power_watt == 2.5
        assert params.source_numerical_aperture == 0.2
        assert params.polarization_angle_degree == 45.0

    def test_optical_parameters_immutable(self, valid_optical_params):
        """Test that OpticalParameters instances are immutable (frozen dataclass)."""
        params = OpticalParameters(**valid_optical_params)
        
        with pytest.raises(FrozenInstanceError, match="cannot assign to field"):
            params.wavelength_nm = 532.0

    @patch('RosettaX.workflow.calibration.scattering.build_mie_parameter_payload')
    def test_to_parameter_payload_solid_sphere(self, mock_build_mie, valid_optical_params):
        """Test to_parameter_payload method for solid sphere model."""
        mock_build_mie.return_value = {'base': 'payload'}
        params = OpticalParameters(**valid_optical_params)
        
        result = params.to_parameter_payload(
            mie_model='Solid Sphere',
            particle_diameter_nm=[100.0, 200.0, 300.0]
        )
        
        # Verify build_mie_parameter_payload was called with correct arguments
        mock_build_mie.assert_called_once_with(
            mie_model='Solid Sphere',
            medium_refractive_index=1.33,
            particle_refractive_index=1.59,
            core_refractive_index=None,
            shell_refractive_index=None,
            wavelength_nm=488.0,
            detector_numerical_aperture=1.2,
            detector_cache_numerical_aperture=0.5,
            blocker_bar_numerical_aperture=0.1,
            detector_sampling=1000,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=90.0
        )
        
        # Verify result contains expected keys
        assert result['base'] == 'payload'
        assert result['optical_power_watt'] == 1.0
        assert result['source_numerical_aperture'] == 0.1
        assert result['polarization_angle_degree'] == 0.0
        assert result['particle_diameter_nm'] == [100.0, 200.0, 300.0]

    @patch('RosettaX.workflow.calibration.scattering.build_mie_parameter_payload')
    def test_to_parameter_payload_core_shell_sphere(self, mock_build_mie, core_shell_optical_params):
        """Test to_parameter_payload method for core-shell sphere model."""
        mock_build_mie.return_value = {'base': 'payload'}
        params = OpticalParameters(**core_shell_optical_params)
        
        result = params.to_parameter_payload(
            mie_model='Core/Shell Sphere',
            core_diameter_nm=[80.0, 160.0],
            shell_thickness_nm=[10.0, 20.0],
            outer_diameter_nm=[100.0, 200.0]
        )
        
        # Verify build_mie_parameter_payload was called with correct arguments  
        mock_build_mie.assert_called_once_with(
            mie_model='Core/Shell Sphere',
            medium_refractive_index=1.33,
            particle_refractive_index=None,
            core_refractive_index=1.59,
            shell_refractive_index=1.45,
            wavelength_nm=488.0,
            detector_numerical_aperture=1.2,
            detector_cache_numerical_aperture=0.5,
            blocker_bar_numerical_aperture=0.1,
            detector_sampling=1000,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=90.0
        )
        
        # Verify result contains core-shell parameters
        assert result['core_diameter_nm'] == [80.0, 160.0]
        assert result['shell_thickness_nm'] == [10.0, 20.0] 
        assert result['outer_diameter_nm'] == [100.0, 200.0]

    @patch('RosettaX.workflow.calibration.scattering.build_mie_parameter_payload')
    def test_to_parameter_payload_no_particle_parameters(self, mock_build_mie, valid_optical_params):
        """Test to_parameter_payload method with no particle size parameters."""
        mock_build_mie.return_value = {'base': 'payload'}
        params = OpticalParameters(**valid_optical_params)
        
        result = params.to_parameter_payload(mie_model='Solid Sphere')
        
        # Verify only optical parameters are included, no particle sizes
        assert 'particle_diameter_nm' not in result
        assert 'core_diameter_nm' not in result
        assert 'shell_thickness_nm' not in result
        assert 'outer_diameter_nm' not in result
        assert result['optical_power_watt'] == 1.0


class Test_ParsedSphereStandardRows:
    """Test suite for ParsedSphereStandardRows dataclass."""

    @pytest.fixture
    def valid_sphere_data(self):
        """Fixture providing valid sphere standard data."""
        return {
            'row_indices': [0, 1, 2],
            'particle_diameters_nm': np.array([100.0, 200.0, 300.0]),
            'measured_peak_positions': np.array([1500.0, 3000.0, 4500.0])
        }

    def test_parsed_sphere_standard_rows_creation(self, valid_sphere_data):
        """Test ParsedSphereStandardRows creation."""
        rows = ParsedSphereStandardRows(**valid_sphere_data)
        
        assert rows.row_indices == [0, 1, 2]
        np.testing.assert_array_equal(rows.particle_diameters_nm, np.array([100.0, 200.0, 300.0]))
        np.testing.assert_array_equal(rows.measured_peak_positions, np.array([1500.0, 3000.0, 4500.0]))

    def test_row_count_property(self, valid_sphere_data):
        """Test row_count property returns correct count."""
        rows = ParsedSphereStandardRows(**valid_sphere_data)
        
        assert rows.row_count == 3

    def test_row_count_property_empty_data(self):
        """Test row_count property with empty data."""
        rows = ParsedSphereStandardRows(
            row_indices=[],
            particle_diameters_nm=np.array([]),
            measured_peak_positions=np.array([])
        )
        
        assert rows.row_count == 0

    def test_parsed_sphere_standard_rows_immutable(self, valid_sphere_data):
        """Test that ParsedSphereStandardRows instances are immutable."""
        rows = ParsedSphereStandardRows(**valid_sphere_data)
        
        with pytest.raises(FrozenInstanceError, match="cannot assign to field"):
            rows.row_indices = [5, 6, 7]

    def test_numpy_array_handling(self):
        """Test proper handling of numpy arrays."""
        diameters = np.array([50.0, 100.0, 150.0, 200.0])
        positions = np.array([750.0, 1500.0, 2250.0, 3000.0])
        
        rows = ParsedSphereStandardRows(
            row_indices=[10, 11, 12, 13],
            particle_diameters_nm=diameters,
            measured_peak_positions=positions
        )
        
        assert rows.row_count == 4
        np.testing.assert_array_equal(rows.particle_diameters_nm, diameters)
        np.testing.assert_array_equal(rows.measured_peak_positions, positions)

    def test_mismatched_array_lengths(self):
        """Test behavior with mismatched array lengths - should still create object."""
        # Note: The dataclass doesn't enforce length matching in its definition
        rows = ParsedSphereStandardRows(
            row_indices=[0, 1],  # 2 elements
            particle_diameters_nm=np.array([100.0, 200.0, 300.0]),  # 3 elements
            measured_peak_positions=np.array([1500.0, 3000.0])  # 2 elements
        )
        
        # Object should still be created (validation might happen elsewhere)
        assert rows.row_count == 2  # Based on row_indices
        assert len(rows.particle_diameters_nm) == 3
        assert len(rows.measured_peak_positions) == 2