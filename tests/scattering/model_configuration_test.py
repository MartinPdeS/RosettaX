"""Regression tests for scattering model configuration."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import sys
import types

import pytest


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


class _PyMieSimStub(types.ModuleType):
    """Minimal PyMieSim module used by the unit tests."""

    experiment = types.SimpleNamespace()


class _PyMieSimUnitsStub(types.ModuleType):
    """Minimal PyMieSim units module used by the unit tests."""

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

from RosettaX.pages.p03_scattering.sections.s04_table.services import (
    ScatteringCalibrationStandardTable,
)
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.scattering import (
    CUSTOM_SCATTERER_PRESET_NAME,
    ModelConfiguration,
)
from RosettaX.workflow.scattering.model import (
    BROAD_PARTICLE_STANDARD_PRESET_NAME,
    ROSETTA_MIX_PRESET_NAME,
    SMALL_PARTICLE_STANDARD_PRESET_NAME,
)


class Test_ScatteringModelConfigurationScattererPresets:
    """Regression checks for scattering model configuration scatterer presets."""

    def test_build_scatterer_preset_options_includes_expected_presets(self):
        """Check build scatterer preset options includes expected presets."""
        options = ModelConfiguration.build_scatterer_preset_options()

        values = {option["value"] for option in options}

        assert CUSTOM_SCATTERER_PRESET_NAME in values
        assert ROSETTA_MIX_PRESET_NAME in values
        assert SMALL_PARTICLE_STANDARD_PRESET_NAME in values
        assert BROAD_PARTICLE_STANDARD_PRESET_NAME in values

    def test_custom_scatterer_preset_preserves_current_values(self):
        """Check custom scatterer preset preserves current values."""
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
        """Check Rosetta mix preset applies wavelength aware material values."""
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

    def test_apply_refractive_index_preset_recomputes_material_value_from_wavelength(
        self,
    ):
        """Check apply refractive index preset recomputes material value from wavelength."""
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
        """Check custom scatterer preset does not lock controls."""
        assert (
            ModelConfiguration.scatterer_preset_disables_manual_controls(
                preset_name=CUSTOM_SCATTERER_PRESET_NAME,
            )
            is False
        )

    def test_non_custom_scatterer_preset_locks_controls(self):
        """Check non custom scatterer preset locks controls."""
        assert (
            ModelConfiguration.scatterer_preset_disables_manual_controls(
                preset_name=ROSETTA_MIX_PRESET_NAME,
            )
            is True
        )

    def test_custom_preset_does_not_override_table(self):
        """Check custom preset does not override table."""
        assert (
            ModelConfiguration.build_table_state_from_scatterer_preset(
                preset_name=CUSTOM_SCATTERER_PRESET_NAME,
            )
            is None
        )

    def test_rosetta_mix_preset_populates_reference_table(self):
        """Check Rosetta mix preset populates reference table."""
        columns, rows = ModelConfiguration.build_table_state_from_scatterer_preset(
            preset_name=ROSETTA_MIX_PRESET_NAME,
        )

        assert [column["id"] for column in columns] == [
            "measured_peak_position",
            "particle_diameter_nm",
            "particle_refractive_index",
            "medium_refractive_index",
            "expected_coupling",
            "expected_cross_section_nm2",
        ]
        assert [row["particle_diameter_nm"] for row in rows] == [
            "994",
            "799",
            "600",
            "400",
            "380",
            "296",
            "203",
            "147",
            "140",
            "125",
            "100",
            "70",
        ]

    def test_rosetta_mix_preset_preserves_other_table_columns(self):
        """Check Rosetta mix preset preserves other table columns."""
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
            "measured_peak_position",
            "particle_diameter_nm",
            "particle_refractive_index",
            "medium_refractive_index",
            "expected_coupling",
            "expected_cross_section_nm2",
        ]
        assert rows[0] == {
            "particle_diameter_nm": "994",
            "particle_refractive_index": "Polystyrene(1.59796)",
            "medium_refractive_index": "Water(1.33698)",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
            "expected_cross_section_nm2": "45.6",
        }
        assert rows[1] == {
            "particle_diameter_nm": "799",
            "particle_refractive_index": "Polystyrene(1.59796)",
            "medium_refractive_index": "Water(1.33698)",
            "measured_peak_position": "78.9",
            "expected_coupling": "10.11",
            "expected_cross_section_nm2": "10.11",
        }

    def test_rosetta_mix_preset_preserves_measured_peak_column_for_all_overlapping_rows(
        self,
    ):
        """Check Rosetta mix preset preserves measured peak column for all overlapping rows."""
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

        assert [row["measured_peak_position"] for row in rows[:3]] == [
            "12.3",
            "78.9",
            "456.7",
        ]


class Test_ScatteringCalibrationStandardTable:
    """Regression checks for scattering calibration standard table."""

    def test_runtime_config_uses_scatterer_preset_when_geometry_lists_are_empty(self):
        """Check runtime config uses scatterer preset when geometry lists are empty."""
        columns, rows = (
            ScatteringCalibrationStandardTable.build_state_from_runtime_config(
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
        )

        assert [column["id"] for column in columns] == [
            "measured_peak_position",
            "particle_diameter_nm",
            "particle_refractive_index",
            "medium_refractive_index",
            "expected_coupling",
            "expected_cross_section_nm2",
        ]
        assert [row["particle_diameter_nm"] for row in rows] == [
            "994",
            "799",
            "600",
            "400",
            "380",
            "296",
            "203",
            "147",
            "140",
            "125",
            "100",
            "70",
        ]

    def test_runtime_config_uses_scatterer_preset_over_explicit_geometry_lists(self):
        """Check runtime config uses scatterer preset over explicit geometry lists."""
        _columns, rows = (
            ScatteringCalibrationStandardTable.build_state_from_runtime_config(
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
        )

        assert [row["particle_diameter_nm"] for row in rows] == [
            "994",
            "799",
            "600",
            "400",
            "380",
            "296",
            "203",
            "147",
            "140",
            "125",
            "100",
            "70",
        ]

    def test_runtime_config_uses_explicit_geometry_lists_for_custom_preset(self):
        """Check runtime config uses explicit geometry lists for custom preset."""
        _columns, rows = (
            ScatteringCalibrationStandardTable.build_state_from_runtime_config(
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
        )

        assert [row["particle_diameter_nm"] for row in rows] == [
            "111",
            "222",
            "",
        ]

    def test_model_selection_uses_preset_geometry_when_preset_is_active(self):
        """Check model selection uses preset geometry when preset is active."""
        columns, rows = (
            ScatteringCalibrationStandardTable.build_state_for_model_selection(
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
        )

        assert [column["id"] for column in columns] == [
            "measured_peak_position",
            "particle_diameter_nm",
            "particle_refractive_index",
            "medium_refractive_index",
            "expected_coupling",
            "expected_cross_section_nm2",
        ]
        assert rows[0] == {
            "particle_diameter_nm": "994",
            "particle_refractive_index": "Polystyrene(1.59796)",
            "medium_refractive_index": "Water(1.33698)",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
            "expected_cross_section_nm2": "45.6",
        }
        assert rows[1] == {
            "particle_diameter_nm": "799",
            "particle_refractive_index": "Polystyrene(1.59796)",
            "medium_refractive_index": "Water(1.33698)",
            "measured_peak_position": "78.9",
            "expected_coupling": "10.11",
            "expected_cross_section_nm2": "10.11",
        }

    def test_model_selection_remaps_current_rows_for_custom_preset(self):
        """Check model selection remaps current rows for custom preset."""
        columns, rows = (
            ScatteringCalibrationStandardTable.build_state_for_model_selection(
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
        )

        assert [column["id"] for column in columns] == [
            "measured_peak_position",
            "core_diameter_nm",
            "shell_thickness_nm",
            "outer_diameter_nm",
            "medium_refractive_index",
            "core_refractive_index",
            "shell_refractive_index",
            "expected_coupling",
            "expected_cross_section_nm2",
        ]
        assert rows[0] == {
            "core_diameter_nm": "111",
            "shell_thickness_nm": "",
            "outer_diameter_nm": "",
            "medium_refractive_index": "",
            "core_refractive_index": "",
            "shell_refractive_index": "",
            "measured_peak_position": "12.3",
            "expected_coupling": "45.6",
            "expected_cross_section_nm2": "45.6",
        }

    def test_clear_measured_peak_positions_preserves_geometry_and_expected_coupling(
        self,
    ):
        """Check clear measured peak positions preserves geometry and expected coupling."""
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
