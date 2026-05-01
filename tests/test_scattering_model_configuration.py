# -*- coding: utf-8 -*-

from RosettaX.workflow.model.scattering import (
    BROAD_PARTICLE_STANDARD_PRESET_NAME,
    CUSTOM_SCATTERER_PRESET_NAME,
    ROSETTA_MIX_PRESET_NAME,
    SMALL_PARTICLE_STANDARD_PRESET_NAME,
    ScatteringModelConfiguration,
)


class Test_ScatteringModelConfigurationScattererPresets:
    def test_build_scatterer_preset_options_includes_expected_presets(self):
        options = ScatteringModelConfiguration.build_scatterer_preset_options()

        values = {option["value"] for option in options}

        assert CUSTOM_SCATTERER_PRESET_NAME in values
        assert ROSETTA_MIX_PRESET_NAME in values
        assert SMALL_PARTICLE_STANDARD_PRESET_NAME in values
        assert BROAD_PARTICLE_STANDARD_PRESET_NAME in values

    def test_custom_scatterer_preset_preserves_current_values(self):
        result = ScatteringModelConfiguration.resolve_scatterer_preset_values(
            preset_name=CUSTOM_SCATTERER_PRESET_NAME,
            current_mie_model="Solid Sphere",
            current_medium_refractive_index=1.335,
            current_particle_refractive_index=1.45,
            current_core_refractive_index=1.47,
            current_shell_refractive_index=1.46,
        )

        assert result == (
            "Solid Sphere",
            1.335,
            1.45,
            1.47,
            1.46,
        )

    def test_rosetta_mix_preset_applies_expected_values(self):
        result = ScatteringModelConfiguration.resolve_scatterer_preset_values(
            preset_name=ROSETTA_MIX_PRESET_NAME,
            current_mie_model="Solid Sphere",
            current_medium_refractive_index=1.0,
            current_particle_refractive_index=1.0,
            current_core_refractive_index=1.0,
            current_shell_refractive_index=1.0,
        )

        assert result == (
            "Solid Sphere",
            1.333,
            1.59,
            1.47,
            1.46,
        )

    def test_custom_scatterer_preset_does_not_lock_controls(self):
        assert ScatteringModelConfiguration.scatterer_preset_disables_manual_controls(
            preset_name=CUSTOM_SCATTERER_PRESET_NAME,
        ) is False

    def test_non_custom_scatterer_preset_locks_controls(self):
        assert ScatteringModelConfiguration.scatterer_preset_disables_manual_controls(
            preset_name=ROSETTA_MIX_PRESET_NAME,
        ) is True

    def test_custom_preset_does_not_override_table(self):
        assert ScatteringModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=CUSTOM_SCATTERER_PRESET_NAME,
        ) is None

    def test_rosetta_mix_preset_populates_reference_table(self):
        columns, rows = ScatteringModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=ROSETTA_MIX_PRESET_NAME,
        )

        assert [column["id"] for column in columns] == [
            "particle_diameter_nm",
            "measured_peak_position",
            "expected_coupling",
        ]
        assert [row["particle_diameter_nm"] for row in rows] == [
            "70",
            "100",
            "150",
            "200",
            "300",
            "500",
        ]

    def test_rosetta_mix_preset_preserves_other_table_columns(self):
        columns, rows = ScatteringModelConfiguration.build_table_state_from_scatterer_preset(
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
            "particle_diameter_nm": "70",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
        }
        assert rows[1] == {
            "particle_diameter_nm": "100",
            "measured_peak_position": "78.9",
            "expected_coupling": "10.11",
        }
