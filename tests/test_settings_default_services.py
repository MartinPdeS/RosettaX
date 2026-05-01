# -*- coding: utf-8 -*-

from RosettaX.pages.p05_settings.sections.s01_default import services
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.apply_calibration.scattering import EXTRACELLULAR_VESICLES_PRESET_NAME
from RosettaX.workflow.model.scattering import ROSETTA_MIX_PRESET_NAME


class Test_SettingsDefaultServicesPresetPreferences:
    def test_build_form_store_reads_saved_preset_preferences(self):
        runtime_config = RuntimeConfig.from_dict(
            {
                "particle_model": {
                    "scatterer_preset": ROSETTA_MIX_PRESET_NAME,
                },
                "calibration": {
                    "target_model_preset": EXTRACELLULAR_VESICLES_PRESET_NAME,
                },
            }
        )

        form_store = services.build_form_store_from_runtime_config(
            runtime_config,
        )

        assert form_store["default_scatterer_preset"] == ROSETTA_MIX_PRESET_NAME
        assert (
            form_store["default_apply_target_model_preset"]
            == EXTRACELLULAR_VESICLES_PRESET_NAME
        )

    def test_build_nested_profile_payload_saves_preset_preferences(self):
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "default_scatterer_preset": ROSETTA_MIX_PRESET_NAME,
                "default_apply_target_model_preset": EXTRACELLULAR_VESICLES_PRESET_NAME,
            }
        )

        assert nested_profile_payload["particle_model"]["scatterer_preset"] == ROSETTA_MIX_PRESET_NAME
        assert (
            nested_profile_payload["calibration"]["target_model_preset"]
            == EXTRACELLULAR_VESICLES_PRESET_NAME
        )