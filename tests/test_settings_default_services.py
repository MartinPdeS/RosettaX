# -*- coding: utf-8 -*-

from RosettaX.pages.p05_settings.sections.s01_default import services
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.apply_calibration.scattering import (
    EXTRACELLULAR_VESICLES_PRESET_NAME,
)
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

        assert (
            nested_profile_payload["particle_model"]["scatterer_preset"]
            == ROSETTA_MIX_PRESET_NAME
        )
        assert (
            nested_profile_payload["calibration"]["target_model_preset"]
            == EXTRACELLULAR_VESICLES_PRESET_NAME
        )


class Test_SettingsDefaultServicesPeakTableSortOrder:
    def test_build_form_store_reads_saved_peak_table_sort_order_preferences(self):
        runtime_config = RuntimeConfig.from_dict(
            {
                "fluorescence_calibration": {
                    "peak_table_sort_order": "descending",
                },
                "scattering_calibration": {
                    "peak_table_sort_order": "descending",
                },
            }
        )

        form_store = services.build_form_store_from_runtime_config(
            runtime_config,
        )

        assert form_store["fluorescence_peak_table_sort_order"] == "descending"
        assert form_store["scattering_peak_table_sort_order"] == "descending"

    def test_build_nested_profile_payload_saves_peak_table_sort_order_preferences(self):
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "fluorescence_peak_table_sort_order": "descending",
                "scattering_peak_table_sort_order": "descending",
            }
        )

        assert (
            nested_profile_payload["fluorescence_calibration"]["peak_table_sort_order"]
            == "descending"
        )
        assert (
            nested_profile_payload["scattering_calibration"]["peak_table_sort_order"]
            == "descending"
        )


class Test_SettingsDefaultServicesCanonicalSharedPaths:
    def test_build_nested_profile_payload_saves_shared_calibration_fields_to_canonical_paths(self):
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "mesf_values": "100, 200, 300",
                "peak_count": 5,
                "default_fluorescence_peak_process": "manual_1d",
                "default_gating_channel": "SSC-A",
                "default_gating_threshold": 123.4,
                "target_mie_relation_xscale": "log",
                "target_mie_relation_yscale": "linear",
                "n_bins": 128,
                "show_calibration": "no",
            }
        )

        assert nested_profile_payload["calibration"]["mesf_values"] == [100.0, 200.0, 300.0]
        assert nested_profile_payload["calibration"]["peak_count"] == 5
        assert (
            nested_profile_payload["calibration"]["default_fluorescence_peak_process"]
            == "manual_1d"
        )
        assert nested_profile_payload["calibration"]["default_gating_channel"] == "SSC-A"
        assert nested_profile_payload["calibration"]["default_gating_threshold"] == 123.4
        assert nested_profile_payload["calibration"]["target_mie_relation_xscale"] == "log"
        assert nested_profile_payload["calibration"]["target_mie_relation_yscale"] == "linear"
        assert nested_profile_payload["calibration"]["n_bins_for_plots"] == 128
        assert nested_profile_payload["calibration"]["show_calibration_plot_by_default"] is False
