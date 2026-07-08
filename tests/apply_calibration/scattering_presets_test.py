# -*- coding: utf-8 -*-

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
    def test_resolve_scattering_target_model_preset_uses_sellmeier_sources_for_polystyrene(
        self,
    ) -> None:
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
        resolved_preset = resolve_scattering_target_model_preset(
            CUSTOM_PRESET_NAME,
            wavelength_nm=405.0,
        )

        assert resolved_preset.medium_refractive_index == 1.333
        assert resolved_preset.particle_refractive_index == 1.39
