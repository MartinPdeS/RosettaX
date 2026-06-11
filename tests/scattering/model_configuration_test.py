# -*- coding: utf-8 -*-

import sys
import types

import numpy as np
import pytest


class _DashBootstrapComponentsSentinel:
    def __call__(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    def __getattr__(self, name):
        return _DashBootstrapComponentsSentinel()


class _PyMieSimStub(types.ModuleType):
    experiment = types.SimpleNamespace()


class _PyMieSimUnitsStub(types.ModuleType):
    ureg = types.SimpleNamespace()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)
sys.modules.setdefault(
    "PyMieSim",
    _PyMieSimStub("PyMieSim"),
)
sys.modules.setdefault(
    "PyMieSim.units",
    _PyMieSimUnitsStub("PyMieSim.units"),
)

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.pages.p03_scattering.sections.s03_model.optical_preview import (
    build_pymiesim_photodiode_mesh_coordinates,
)
from RosettaX.pages.p03_scattering.sections.s04_table.services import (
    ScatteringCalibrationStandardTable,
)

from RosettaX.workflow.scattering import CUSTOM_SCATTERER_PRESET_NAME, ModelConfiguration
from RosettaX.workflow.scattering.model import (
    BROAD_PARTICLE_STANDARD_PRESET_NAME,
    ROSETTA_MIX_PRESET_NAME,
    SMALL_PARTICLE_STANDARD_PRESET_NAME,
)


class Test_ScatteringModelConfigurationScattererPresets:
    def test_build_scatterer_preset_options_includes_expected_presets(self):
        options = ModelConfiguration.build_scatterer_preset_options()

        values = {option["value"] for option in options}

        assert CUSTOM_SCATTERER_PRESET_NAME in values
        assert ROSETTA_MIX_PRESET_NAME in values
        assert SMALL_PARTICLE_STANDARD_PRESET_NAME in values
        assert BROAD_PARTICLE_STANDARD_PRESET_NAME in values

    def test_custom_scatterer_preset_preserves_current_values(self):
        result = ModelConfiguration.resolve_scatterer_preset_values(
            preset_name=CUSTOM_SCATTERER_PRESET_NAME,
            current_mie_model="Solid Sphere",
            current_medium_refractive_index_source="water",
            current_medium_refractive_index=1.335,
            current_particle_refractive_index_source="polystyrene",
            current_particle_refractive_index=1.45,
            current_core_refractive_index_source="silica",
            current_core_refractive_index=1.47,
            current_shell_refractive_index_source="phospholipid",
            current_shell_refractive_index=1.46,
            wavelength_nm=488.0,
        )

        assert result == (
            "Solid Sphere",
            "water",
            1.335,
            "polystyrene",
            1.45,
            "silica",
            1.47,
            "phospholipid",
            1.46,
        )

    def test_rosetta_mix_preset_applies_wavelength_aware_material_values(self):
        result_488 = ModelConfiguration.resolve_scatterer_preset_values(
            preset_name=ROSETTA_MIX_PRESET_NAME,
            current_mie_model="Solid Sphere",
            current_medium_refractive_index_source=None,
            current_medium_refractive_index=1.0,
            current_particle_refractive_index_source=None,
            current_particle_refractive_index=1.0,
            current_core_refractive_index_source=None,
            current_core_refractive_index=1.0,
            current_shell_refractive_index_source=None,
            current_shell_refractive_index=1.0,
            wavelength_nm=488.0,
        )

        result_700 = ModelConfiguration.resolve_scatterer_preset_values(
            preset_name=ROSETTA_MIX_PRESET_NAME,
            current_mie_model="Solid Sphere",
            current_medium_refractive_index_source=None,
            current_medium_refractive_index=1.0,
            current_particle_refractive_index_source=None,
            current_particle_refractive_index=1.0,
            current_core_refractive_index_source=None,
            current_core_refractive_index=1.0,
            current_shell_refractive_index_source=None,
            current_shell_refractive_index=1.0,
            wavelength_nm=700.0,
        )

        assert result_488[0] == "Solid Sphere"
        assert result_488[1] == "water"
        assert result_488[3] == "polystyrene"
        assert result_488[5] == "polystyrene"
        assert result_488[7] == "phospholipid"
        assert result_488[2] > result_700[2] > 1.32
        assert result_488[4] > result_700[4] > 1.58
        assert result_488[6] > result_700[6] > 1.58
        assert result_488[8] > result_700[8] > 1.45

    def test_apply_refractive_index_preset_recomputes_material_value_from_wavelength(self):
        value_488 = ModelConfiguration.apply_refractive_index_preset(
            preset_value="water",
            wavelength_nm=488.0,
            current_value=1.0,
        )

        value_700 = ModelConfiguration.apply_refractive_index_preset(
            preset_value="water",
            wavelength_nm=700.0,
            current_value=1.0,
        )

        assert value_488 == pytest.approx(1.3372, abs=1e-3)
        assert value_700 == pytest.approx(1.3308, abs=1e-3)
        assert value_488 > value_700

    def test_custom_scatterer_preset_does_not_lock_controls(self):
        assert ModelConfiguration.scatterer_preset_disables_manual_controls(
            preset_name=CUSTOM_SCATTERER_PRESET_NAME,
        ) is False

    def test_non_custom_scatterer_preset_locks_controls(self):
        assert ModelConfiguration.scatterer_preset_disables_manual_controls(
            preset_name=ROSETTA_MIX_PRESET_NAME,
        ) is True

    def test_custom_preset_does_not_override_table(self):
        assert ModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=CUSTOM_SCATTERER_PRESET_NAME,
        ) is None

    def test_rosetta_mix_preset_populates_reference_table(self):
        columns, rows = ModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=ROSETTA_MIX_PRESET_NAME,
        )

        assert [column["id"] for column in columns] == [
            "particle_diameter_nm",
            "measured_peak_position",
            "expected_coupling",
        ]
        assert [row["particle_diameter_nm"] for row in rows] == [
            '994',
            '799',
            '600',
            '400',
            '296',
            '203',
            '194',
            '150',
            '125',
            '100',
            '70',
        ]

    def test_rosetta_mix_preset_preserves_other_table_columns(self):
        columns, rows = ModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=ROSETTA_MIX_PRESET_NAME,
            current_rows=[
                {
                    "particle_diameter_nm": "999",
                    "measured_peak_position": "12.3",
                    "expected_coupling": "45.6",
                },
                {
                    "particle_diameter_nm": "888",
                    "measured_peak_position": "78.9",
                    "expected_coupling": "10.11",
                },
            ],
        )

        assert [column["id"] for column in columns] == [
            "particle_diameter_nm",
            "measured_peak_position",
            "expected_coupling",
        ]
        assert rows[0] == {
            "particle_diameter_nm": "994",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
        }
        assert rows[1] == {
            "particle_diameter_nm": "799",
            "measured_peak_position": "78.9",
            "expected_coupling": "10.11",
        }

    def test_rosetta_mix_preset_preserves_measured_peak_column_for_all_overlapping_rows(self):
        _columns, rows = ModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=ROSETTA_MIX_PRESET_NAME,
            current_rows=[
                {
                    "particle_diameter_nm": "111",
                    "measured_peak_position": "12.3",
                    "expected_coupling": "45.6",
                },
                {
                    "particle_diameter_nm": "222",
                    "measured_peak_position": "78.9",
                    "expected_coupling": "10.11",
                },
                {
                    "particle_diameter_nm": "333",
                    "measured_peak_position": "456.7",
                    "expected_coupling": "11.12",
                },
            ],
        )

        assert [
            row["measured_peak_position"]
            for row in rows[:3]
        ] == [
            "12.3",
            "78.9",
            "456.7",
        ]

    def test_optical_preview_uses_resolved_preset_sampling_when_current_sampling_is_missing(self):
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=None,
            detector_cache_numerical_aperture=None,
            blocker_bar_numerical_aperture=None,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=None,
            detector_gamma_angle_degree=None,
            detector_sampling=None,
            detector_configuration_preset="Apogee - Side",
        )

        assert len(figure.data) >= 3

    def test_optical_preview_omits_geometry_when_detector_preset_is_empty(self):
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=0.2,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=200,
            detector_configuration_preset="",
        )

        assert len(figure.data) == 8
        assert figure.layout.scene is not None
        assert figure.data[0].type == "surface"
        assert figure.data[1].type == "surface"
        assert not any(
            trace.type == "scatter3d" and getattr(trace, "mode", None) == "markers"
            for trace in figure.data
        )
        assert figure.layout.scene.xaxis.showgrid is False
        assert figure.layout.scene.xaxis.showline is False
        assert figure.layout.scene.xaxis.showbackground is False
        assert figure.layout.scene.xaxis.showspikes is False
        assert figure.layout.scene.xaxis.ticks == ""

    def test_optical_preview_incident_wave_aligns_with_default_detector_axis(self):
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=0.45,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=256,
            detector_configuration_preset="Generic detector",
        )

        incident_wave_trace = next(
            trace
            for trace in figure.data
            if trace.type == "scatter3d"
            and getattr(trace, "mode", None) == "lines"
            and getattr(getattr(trace, "line", None), "color", None) == "#d62728"
        )
        incident_wave_vector = np.asarray(
            [
                float(incident_wave_trace.x[1] - incident_wave_trace.x[0]),
                float(incident_wave_trace.y[1] - incident_wave_trace.y[0]),
                float(incident_wave_trace.z[1] - incident_wave_trace.z[0]),
            ],
            dtype=float,
        )
        incident_wave_vector = incident_wave_vector / np.linalg.norm(incident_wave_vector)

        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=0.45,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=256,
        )
        detector_axis = coordinate_array.mean(axis=0)
        detector_axis = detector_axis / np.linalg.norm(detector_axis)

        assert np.allclose(incident_wave_vector, detector_axis, atol=5e-3)


class Test_ScatteringCalibrationStandardTable:
    def test_runtime_config_uses_scatterer_preset_when_geometry_lists_are_empty(self):
        columns, rows = ScatteringCalibrationStandardTable.build_state_from_runtime_config(
            runtime_config=RuntimeConfig.from_dict(
                {
                    "particle_model": {
                        "scatterer_preset": ROSETTA_MIX_PRESET_NAME,
                        "mie_model": "Solid Sphere",
                        "particle_diameter_nm": [],
                        "core_diameter_nm": [],
                        "shell_thickness_nm": [],
                    }
                }
            ),
        )

        assert [column["id"] for column in columns] == [
            "particle_diameter_nm",
            "measured_peak_position",
            "expected_coupling",
        ]
        assert [row["particle_diameter_nm"] for row in rows] == [
            "994",
            "799",
            "600",
            "400",
            "296",
            "203",
            "194",
            "150",
            "125",
            "100",
            "70",
        ]

    def test_runtime_config_uses_scatterer_preset_over_explicit_geometry_lists(self):
        _columns, rows = ScatteringCalibrationStandardTable.build_state_from_runtime_config(
            runtime_config=RuntimeConfig.from_dict(
                {
                    "particle_model": {
                        "scatterer_preset": ROSETTA_MIX_PRESET_NAME,
                        "mie_model": "Solid Sphere",
                        "particle_diameter_nm": [111.0, 222.0],
                        "core_diameter_nm": [],
                        "shell_thickness_nm": [],
                    }
                }
            ),
        )

        assert [row["particle_diameter_nm"] for row in rows] == [
            "994",
            "799",
            "600",
            "400",
            "296",
            "203",
            "194",
            "150",
            "125",
            "100",
            "70",
        ]

    def test_runtime_config_uses_explicit_geometry_lists_for_custom_preset(self):
        _columns, rows = ScatteringCalibrationStandardTable.build_state_from_runtime_config(
            runtime_config=RuntimeConfig.from_dict(
                {
                    "particle_model": {
                        "scatterer_preset": CUSTOM_SCATTERER_PRESET_NAME,
                        "mie_model": "Solid Sphere",
                        "particle_diameter_nm": [111.0, 222.0],
                        "core_diameter_nm": [],
                        "shell_thickness_nm": [],
                    }
                }
            ),
        )

        assert [row["particle_diameter_nm"] for row in rows] == [
            "111",
            "222",
            "",
        ]

    def test_model_selection_uses_preset_geometry_when_preset_is_active(self):
        columns, rows = ScatteringCalibrationStandardTable.build_state_for_model_selection(
            mie_model="Solid Sphere",
            scatterer_preset=ROSETTA_MIX_PRESET_NAME,
            current_rows=[
                {
                    "particle_diameter_nm": "111",
                    "measured_peak_position": "12.3",
                    "expected_coupling": "45.6",
                },
                {
                    "particle_diameter_nm": "222",
                    "measured_peak_position": "78.9",
                    "expected_coupling": "10.11",
                },
            ],
        )

        assert [column["id"] for column in columns] == [
            "particle_diameter_nm",
            "measured_peak_position",
            "expected_coupling",
        ]
        assert rows[0] == {
            "particle_diameter_nm": "994",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
        }
        assert rows[1] == {
            "particle_diameter_nm": "799",
            "measured_peak_position": "78.9",
            "expected_coupling": "10.11",
        }

    def test_model_selection_remaps_current_rows_for_custom_preset(self):
        columns, rows = ScatteringCalibrationStandardTable.build_state_for_model_selection(
            mie_model="Core/Shell Sphere",
            scatterer_preset=CUSTOM_SCATTERER_PRESET_NAME,
            current_rows=[
                {
                    "particle_diameter_nm": "111",
                    "measured_peak_position": "12.3",
                    "expected_coupling": "45.6",
                },
            ],
        )

        assert [column["id"] for column in columns] == [
            "core_diameter_nm",
            "shell_thickness_nm",
            "outer_diameter_nm",
            "measured_peak_position",
            "expected_coupling",
        ]
        assert rows[0] == {
            "core_diameter_nm": "111",
            "shell_thickness_nm": "",
            "outer_diameter_nm": "",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
        }

    def test_clear_measured_peak_positions_preserves_geometry_and_expected_coupling(self):
        rows = ScatteringCalibrationStandardTable.clear_measured_peak_positions(
            rows=[
                {
                    "particle_diameter_nm": "111",
                    "measured_peak_position": "12.3",
                    "expected_coupling": "45.6",
                },
                {
                    "particle_diameter_nm": "222",
                    "measured_peak_position": "78.9",
                    "expected_coupling": "10.11",
                },
            ],
        )

        assert rows == [
            {
                "particle_diameter_nm": "111",
                "measured_peak_position": "",
                "expected_coupling": "45.6",
            },
            {
                "particle_diameter_nm": "222",
                "measured_peak_position": "",
                "expected_coupling": "10.11",
            },
        ]
