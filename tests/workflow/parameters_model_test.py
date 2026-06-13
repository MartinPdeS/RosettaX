# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pytest
from types import SimpleNamespace
from unittest.mock import patch, Mock
import logging

from RosettaX.pages.p03_scattering.sections.s03_model.optical_preview import build_pymiesim_photodiode_mesh_coordinates
from RosettaX.workflow.detector import (
    DetectorPresetLoader,
    resolve_detector_angular_weights,
    resolve_detector_modeling_geometry_values,
)
from RosettaX.workflow.detector.configuration import _build_blocker_bar_numerical_aperture, resolve_detector_configuration_values, resolve_detector_preset_wavelength_nm
from RosettaX.workflow.scattering.model import ModelConfiguration
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


class Test_DetectorPresetLoaderCatalog:
    def test_loader_builds_brand_options_from_preset_metadata(self):
        loader = DetectorPresetLoader()

        option_values = {
            option["value"]
            for option in loader.load_brand_options()
        }

        assert "Agilent" in option_values
        assert "BD Biosciences" in option_values
        assert "Apogee" in option_values
        assert "Beckman Coulter Life Sciences" in option_values
        assert "Cytek Biosciences" in option_values
        assert "nanoFCM" in option_values
        assert "Sony Biosciences" in option_values
        assert "Thermo Fisher Scientific" in option_values
        assert "Custom" in option_values

    def test_loader_builds_model_options_for_one_brand(self):
        loader = DetectorPresetLoader()

        bd_options = loader.load_model_options(
            "BD Biosciences",
        )

        assert bd_options == [
            {
                "label": "FACSCanto II",
                "value": "FACSCanto II",
            },
        ]

    def test_loader_builds_type_options_for_one_brand_and_model(self):
        loader = DetectorPresetLoader()

        bd_type_options = loader.load_type_options(
            brand="BD Biosciences",
            model="FACSCanto II",
        )

        assert bd_type_options == [
            {
                "label": "FSC",
                "value": "BD FACSCanto II FSC",
            },
            {
                "label": "SSC",
                "value": "BD FACSCanto II SSC",
            },
        ]

    def test_loader_resolves_custom_brand_for_generic_detector(self):
        loader = DetectorPresetLoader()

        assert loader.resolve_preset_brand("Generic detector") == "Custom"

    def test_loader_builds_trimmed_model_labels_for_apogee_brand(self):
        loader = DetectorPresetLoader()

        assert loader.load_model_options("Apogee") == [
            {
                "label": "Apogee",
                "value": "Apogee",
            },
        ]

        assert loader.load_type_options(
            brand="Apogee",
            model="Apogee",
        ) == [
            {
                "label": "Forward",
                "value": "Apogee - Forward",
            },
            {
                "label": "Side",
                "value": "Apogee - Side",
            },
        ]

    def test_loader_builds_model_options_for_cytek_brand(self):
        loader = DetectorPresetLoader()

        assert loader.load_model_options("Cytek Biosciences") == [
            {
                "label": "Aurora",
                "value": "Aurora",
            },
        ]

        assert loader.load_type_options(
            brand="Cytek Biosciences",
            model="Aurora",
        ) == [
            {
                "label": "FSC",
                "value": "Cytek Aurora FSC",
            },
            {
                "label": "SSC",
                "value": "Cytek Aurora SSC",
            },
        ]

    def test_loader_builds_model_options_for_nanofcm_brand(self):
        loader = DetectorPresetLoader()

        assert loader.load_model_options("nanoFCM") == [
            {
                "label": "NanoAnalyzer",
                "value": "NanoAnalyzer",
            },
        ]

        assert loader.load_type_options(
            brand="nanoFCM",
            model="NanoAnalyzer",
        ) == [
            {
                "label": "FSC",
                "value": "nanoFCM NanoAnalyzer FSC",
            },
            {
                "label": "SSC",
                "value": "nanoFCM NanoAnalyzer SSC",
            },
        ]

    def test_standard_scatter_presets_use_forward_zero_and_side_ninety_angles(self):
        loader = DetectorPresetLoader()
        standard_presets = {
            name: preset
            for name, preset in loader.load_presets().items()
            if preset.get("channel") in {"FSC", "SSC"}
        }

        for preset_name, preset in standard_presets.items():
            expected_phi = 0.0 if preset["channel"] == "FSC" else 90.0
            expected_gamma = 0.0
            assert preset["detector_phi_angle_degree"] == expected_phi, preset_name
            assert preset["detector_gamma_angle_degree"] == expected_gamma, preset_name

    def test_loader_normalizes_standard_scatter_angles_from_catalog_data(self, tmp_path):
        detector_catalog_path = tmp_path / "detector_definitions.json"
        detector_catalog_path.write_text(
            """
{
    "schema_version": "1.0",
    "presets": [
        {
            "name": "Example FSC",
            "manufacturer": "Example",
            "instrument": "System",
            "channel": "FSC",
            "detector_phi_angle_degree": 37.0,
            "detector_gamma_angle_degree": 12.0
        },
        {
            "name": "Example SSC",
            "manufacturer": "Example",
            "instrument": "System",
            "channel": "SSC",
            "detector_phi_angle_degree": 11.0,
            "detector_gamma_angle_degree": 22.0
        },
        {
            "name": "Apogee - Forward",
            "manufacturer": "Apogee",
            "instrument": "Ad hoc",
            "channel": "Weighted",
            "detector_phi_angle_degree": 45.0,
            "detector_gamma_angle_degree": 0.0
        }
    ]
}
            """.strip(),
            encoding="utf-8",
        )

        loader = DetectorPresetLoader(detector_catalog_path)
        presets = loader.load_presets()

        assert presets["Example FSC"]["detector_phi_angle_degree"] == 0.0
        assert presets["Example FSC"]["detector_gamma_angle_degree"] == 0.0
        assert presets["Example SSC"]["detector_phi_angle_degree"] == 90.0
        assert presets["Example SSC"]["detector_gamma_angle_degree"] == 0.0
        assert presets["Apogee - Forward"]["detector_phi_angle_degree"] == 45.0


class Test_ScattererPresetDefaults:
    def test_scatterer_preset_options_start_with_no_preset(self):
        assert ModelConfiguration.build_scatterer_preset_options()[0] == {
            "label": "No preset",
            "value": "",
        }

    def test_resolve_runtime_scatterer_preset_keeps_empty_value(self):
        assert ModelConfiguration.resolve_runtime_scatterer_preset("") == ""

    def test_no_preset_does_not_disable_manual_controls(self):
        assert (
            ModelConfiguration.scatterer_preset_disables_manual_controls(
                preset_name="",
            )
            is False
        )


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
    @patch('RosettaX.workflow.parameters.model.BackEnd.compute_modeled_coupling_from_diameters')
    def test_compute_model_for_rows_weighted_detector_preset_passes_angular_weights(self, mock_compute_coupling, mock_table, valid_optical_parameters,
                                                                                     valid_solid_sphere_rows, mock_logger):
        mock_table.normalize_table_rows.return_value = [dict(row) for row in valid_solid_sphere_rows]
        valid_optical_parameters['detector_sampling'] = 1000
        mock_compute_coupling.return_value = SimpleNamespace(
            expected_coupling_values=np.asarray([1.0, 2.0, 3.0], dtype=float)
        )

        compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
            detector_configuration_preset='Apogee - Side',
            logger=mock_logger,
            **valid_optical_parameters
        )

        detector_angular_weights = mock_compute_coupling.call_args.kwargs['detector_angular_weights']
        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=1.2,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=45.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=1000,
        )
        apogee_side_preset = DetectorPresetLoader().load_preset('Apogee - Side')
        blocker_bar_numerical_aperture = _build_blocker_bar_numerical_aperture(
            preset=apogee_side_preset,
            coordinate_array=coordinate_array,
        )
        expected_visible_mask = (
            (coordinate_array[:, 0] > coordinate_array[:, 2])
            & (
                blocker_bar_numerical_aperture
                >= float(apogee_side_preset['blocker_bar_numerical_aperture'])
            )
        )

        assert detector_angular_weights.shape == (1000,)
        assert np.allclose(detector_angular_weights[~expected_visible_mask], 0.0)
        assert np.allclose(detector_angular_weights[expected_visible_mask], 1.0)

    @patch('RosettaX.workflow.parameters.model.table')
    @patch('RosettaX.workflow.parameters.model.BackEnd.compute_modeled_coupling_from_diameters')
    def test_compute_model_for_rows_treats_missing_generic_detector_geometry_as_zero(
        self,
        mock_compute_coupling,
        mock_table,
        valid_optical_parameters,
        valid_solid_sphere_rows,
        mock_logger,
    ):
        mock_table.normalize_table_rows.return_value = [dict(row) for row in valid_solid_sphere_rows]
        mock_compute_coupling.return_value = SimpleNamespace(
            expected_coupling_values=np.asarray([1.0, 2.0, 3.0], dtype=float)
        )
        valid_optical_parameters['detector_configuration_preset'] = 'Generic detector'
        valid_optical_parameters['detector_cache_numerical_aperture'] = None
        valid_optical_parameters['blocker_bar_numerical_aperture'] = None

        result = compute_model_for_rows(
            mie_model=SOLID_SPHERE_MODEL_NAME,
            current_rows=valid_solid_sphere_rows,
            logger=mock_logger,
            **valid_optical_parameters
        )

        assert [row['expected_coupling'] for row in result] == ['1', '2', '3']
        assert mock_compute_coupling.call_args.kwargs['detector_cache_numerical_aperture'] == 0.0
        assert mock_compute_coupling.call_args.kwargs['detector_angular_weights'] is None

    def test_resolve_detector_angular_weights_apogee_half_lens_split_presets(self):
        apogee_side_preset = DetectorPresetLoader().load_preset('Apogee - Side')
        apogee_forward_preset = DetectorPresetLoader().load_preset('Apogee - Forward')
        side_weights = resolve_detector_angular_weights(
            preset_name='Apogee - Side',
            detector_sampling=1000,
        )
        forward_weights = resolve_detector_angular_weights(
            preset_name='Apogee - Forward',
            detector_sampling=1000,
        )

        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=1.2,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=45.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=1000,
        )
        split_metric = coordinate_array[:, 0] - coordinate_array[:, 2]
        side_blocker_bar_numerical_aperture = _build_blocker_bar_numerical_aperture(
            preset=apogee_side_preset,
            coordinate_array=coordinate_array,
        )
        forward_blocker_bar_numerical_aperture = _build_blocker_bar_numerical_aperture(
            preset=apogee_forward_preset,
            coordinate_array=coordinate_array,
        )

        side_visible_mask = (
            (split_metric > 0.0)
            & (
                side_blocker_bar_numerical_aperture
                >= float(apogee_side_preset['blocker_bar_numerical_aperture'])
            )
        )
        forward_visible_mask = (
            (split_metric < 0.0)
            & (
                forward_blocker_bar_numerical_aperture
                >= float(apogee_forward_preset['blocker_bar_numerical_aperture'])
            )
        )

        assert np.allclose(side_weights[side_visible_mask], 1.0)
        assert np.allclose(side_weights[~side_visible_mask], 0.0)
        assert np.allclose(forward_weights[forward_visible_mask], 1.0)
        assert np.allclose(forward_weights[~forward_visible_mask], 0.0)
        assert int(np.count_nonzero(side_weights)) == int(np.count_nonzero(side_visible_mask))
        assert int(np.count_nonzero(forward_weights)) == int(np.count_nonzero(forward_visible_mask))
        assert np.allclose(side_weights[split_metric < 0.0], 0.0)
        assert np.allclose(forward_weights[split_metric > 0.0], 0.0)

    def test_detector_preset_loader_normalizes_apogee_split_definition(self):
        loader = DetectorPresetLoader()

        apogee_side_preset = loader.load_preset('Apogee - Side')
        preset_path = Path(apogee_side_preset['_path'])

        assert apogee_side_preset['detector_angular_weighting'] == {
            'mode': 'split',
            'metric': 'x-minus-z',
            'keep': 'positive',
        }
        assert apogee_side_preset['alias'] == ['apogee']
        assert preset_path.name == 'detector_definitions.json'
        assert preset_path.parent.name == 'assets'

    @patch('RosettaX.workflow.detector.configuration._DETECTOR_PRESET_LOADER.load_preset')
    def test_resolve_detector_angular_weights_applies_cache_and_blocker_geometry(self, mock_load_preset):
        mock_load_preset.return_value = {
            'name': 'Masked detector',
            'detector_numerical_aperture': 1.2,
            'detector_cache_numerical_aperture': 0.3,
            'blocker_bar_numerical_aperture': 0.5,
            'detector_phi_angle_degree': 0.0,
            'detector_gamma_angle_degree': 0.0,
            'medium_refractive_index': 1.333,
        }

        detector_angular_weights = resolve_detector_angular_weights(
            preset_name='Masked detector',
            detector_sampling=1000,
        )

        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=1.2,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=1000,
        )
        cache_numerical_aperture = 1.333 * np.sqrt(
            coordinate_array[:, 1] ** 2 + coordinate_array[:, 2] ** 2
        )
        blocker_bar_numerical_aperture = _build_blocker_bar_numerical_aperture(
            preset=mock_load_preset.return_value,
            coordinate_array=coordinate_array,
        )
        visible_mask = (
            (cache_numerical_aperture >= 0.3)
            & (blocker_bar_numerical_aperture >= 0.5)
        )

        assert np.any(
            (cache_numerical_aperture >= 0.5)
            & (blocker_bar_numerical_aperture < 0.5)
        )

        assert np.allclose(detector_angular_weights[~visible_mask], 0.0)
        assert np.allclose(detector_angular_weights[visible_mask], 1.0)

    @patch('RosettaX.workflow.detector.configuration._DETECTOR_PRESET_LOADER.load_preset')
    def test_resolve_detector_modeling_geometry_values_zeroes_scalar_geometry_for_weighted_presets(self, mock_load_preset):
        mock_load_preset.return_value = {
            'name': 'Masked detector',
            'detector_cache_numerical_aperture': 0.3,
            'blocker_bar_numerical_aperture': 0.5,
        }

        resolved_detector_cache_numerical_aperture, resolved_blocker_bar_numerical_aperture = (
            resolve_detector_modeling_geometry_values(
                preset_name='Masked detector',
                current_detector_cache_numerical_aperture=0.3,
                current_blocker_bar_numerical_aperture=0.5,
            )
        )

        assert resolved_detector_cache_numerical_aperture == 0.0
        assert resolved_blocker_bar_numerical_aperture == 0.0

    def test_resolve_detector_angular_weights_generic_detector_applies_blocker_bar_geometry(self):
        detector_angular_weights = resolve_detector_angular_weights(
            preset_name='Generic detector',
            detector_sampling=1000,
            current_detector_numerical_aperture=1.2,
            current_detector_cache_numerical_aperture=0.0,
            current_blocker_bar_numerical_aperture=0.1,
            current_detector_phi_angle_degree=45.0,
            current_detector_gamma_angle_degree=0.0,
            current_medium_refractive_index=1.333,
        )

        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=1.2,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=45.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=1000,
        )
        blocker_bar_numerical_aperture = _build_blocker_bar_numerical_aperture(
            preset={
                'detector_numerical_aperture': 1.2,
                'detector_cache_numerical_aperture': 0.0,
                'blocker_bar_numerical_aperture': 0.1,
                'detector_phi_angle_degree': 45.0,
                'detector_gamma_angle_degree': 0.0,
                'medium_refractive_index': 1.333,
            },
            coordinate_array=coordinate_array,
        )

        visible_mask = blocker_bar_numerical_aperture >= 0.1

        assert detector_angular_weights.shape == (1000,)
        assert np.allclose(detector_angular_weights[visible_mask], 1.0)
        assert np.allclose(detector_angular_weights[~visible_mask], 0.0)

    def test_resolve_detector_modeling_geometry_values_zeroes_scalar_geometry_for_generic_detector_blocker_bar(self):
        resolved_detector_cache_numerical_aperture, resolved_blocker_bar_numerical_aperture = (
            resolve_detector_modeling_geometry_values(
                preset_name='Generic detector',
                current_detector_cache_numerical_aperture=0.0,
                current_blocker_bar_numerical_aperture=0.1,
            )
        )

        assert resolved_detector_cache_numerical_aperture == 0.0
        assert resolved_blocker_bar_numerical_aperture == 0.0

    def test_resolve_detector_configuration_values_preserves_generic_detector_cache_geometry(self):
        resolved_values = resolve_detector_configuration_values(
            preset_name='Generic detector',
            current_detector_numerical_aperture=1.2,
            current_detector_cache_numerical_aperture=0.3,
            current_blocker_bar_numerical_aperture=0.1,
            current_detector_sampling=1000,
            current_detector_phi_angle_degree=45.0,
            current_detector_gamma_angle_degree=0.0,
        )

        assert resolved_values == (1.2, 0.3, 0.1, 1000, 45.0, 0.0)

    def test_resolve_detector_preset_wavelength_uses_preset_value(self):
        assert resolve_detector_preset_wavelength_nm(
            preset_name='BD FACSCanto II SSC',
            current_wavelength_nm=700.0,
        ) == 488.0

    def test_resolve_detector_preset_wavelength_keeps_generic_detector_editable(self):
        assert resolve_detector_preset_wavelength_nm(
            preset_name='Generic detector',
            current_wavelength_nm=561.0,
        ) == 561.0

    def test_resolve_detector_preset_wavelength_keeps_backward_compatible_keyword(self):
        assert resolve_detector_preset_wavelength_nm(
            preset_name='Generic detector',
            fallback_wavelength_nm=640.0,
        ) == 640.0

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


class Test_build_pymiesim_photodiode_mesh_coordinates:
    def test_returns_requested_sampling_on_unit_sphere(self):
        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=0.45,
            medium_refractive_index=1.334,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=256,
        )

        assert coordinate_array.shape == (256, 3)
        assert np.allclose(np.linalg.norm(coordinate_array, axis=1), 1.0)

    def test_uses_rosettax_detector_frame_with_default_axis_on_x(self):
        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=0.45,
            medium_refractive_index=1.334,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=512,
        )

        mean_axis = coordinate_array.mean(axis=0)
        mean_axis = mean_axis / np.linalg.norm(mean_axis)

        assert mean_axis[0] > 0.99
        assert abs(mean_axis[1]) < 5e-4
        assert abs(mean_axis[2]) < 5e-4

    def test_applies_phi_offset_in_xz_plane(self):
        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=0.45,
            medium_refractive_index=1.334,
            detector_phi_angle_degree=45.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=512,
        )

        mean_axis = coordinate_array.mean(axis=0)
        mean_axis = mean_axis / np.linalg.norm(mean_axis)

        expected_axis = np.asarray(
            [
                np.sqrt(0.5),
                0.0,
                np.sqrt(0.5),
            ],
            dtype=float,
        )

        assert np.allclose(mean_axis, expected_axis, atol=3e-3)