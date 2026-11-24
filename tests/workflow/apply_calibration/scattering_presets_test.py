"""Regression tests for apply calibration scattering presets."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


from RosettaX.workflow.apply_calibration.scattering.presets import (
    CUSTOM_PRESET_NAME,
    POLYSTYRENE_BEADS_PRESET_NAME,
    get_scattering_target_model_preset,
    resolve_scattering_target_model_preset,
)
from RosettaX.workflow.parameters.refractive_index import (
    calculate_sellmeier_refractive_index,
)


class Test_ApplyCalibrationScatteringPresets:
    """Regression checks for apply calibration scattering presets."""

    def test_resolve_scattering_target_model_preset_uses_sellmeier_sources_for_polystyrene(
        self,
    ) -> None:
        """Check resolve scattering target model preset uses sellmeier sources for polystyrene."""
        resolved_preset = resolve_scattering_target_model_preset(
            POLYSTYRENE_BEADS_PRESET_NAME,
            wavelength_nm=405.0,
        )

        assert resolved_preset.medium_refractive_index == calculate_sellmeier_refractive_index(
            "water",
            wavelength_nm=405.0,
        )
        assert resolved_preset.particle_refractive_index == calculate_sellmeier_refractive_index(
            "polystyrene",
            wavelength_nm=405.0,
        )
        assert resolved_preset.core_refractive_index == calculate_sellmeier_refractive_index(
            "polystyrene",
            wavelength_nm=405.0,
        )
        assert resolved_preset.shell_refractive_index == calculate_sellmeier_refractive_index(
            "polystyrene",
            wavelength_nm=405.0,
        )

    def test_resolve_scattering_target_model_preset_preserves_fixed_values_without_wavelength(
        self,
    ) -> None:
        """Check resolve scattering target model preset preserves fixed values without wavelength."""
        fixed_preset = get_scattering_target_model_preset(
            POLYSTYRENE_BEADS_PRESET_NAME,
        )
        resolved_preset = resolve_scattering_target_model_preset(
            POLYSTYRENE_BEADS_PRESET_NAME,
        )

        assert resolved_preset == fixed_preset

    def test_resolve_scattering_target_model_preset_keeps_custom_preset_manual_defaults(
        self,
    ) -> None:
        """Check resolve scattering target model preset keeps custom preset manual defaults."""
        resolved_preset = resolve_scattering_target_model_preset(
            CUSTOM_PRESET_NAME,
            wavelength_nm=405.0,
        )

        assert resolved_preset.medium_refractive_index == 1.333
        assert resolved_preset.particle_refractive_index == 1.39
