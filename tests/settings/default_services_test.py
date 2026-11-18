"""Regression tests for settings default services."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


from RosettaX.pages.p05_settings.sections.s01_default import schema, services
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.apply_calibration.scattering import (
    EXTRACELLULAR_VESICLES_PRESET_NAME,
)
from RosettaX.workflow.scattering.model import ROSETTA_MIX_PRESET_NAME
from RosettaX.workflow.table.fluorescence import (
    CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
    GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME,
    ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
)


class Test_SettingsDefaultServicesPresetPreferences:
    """Regression checks for settings default services preset preferences."""

    def test_schema_exposes_manual_selection_options_for_optional_defaults(self):
        """Check schema exposes manual selection options for optional defaults."""
        assert schema.PEAK_PROCESS_OPTIONS[0] == {
            "label": "Select",
            "value": "",
        }
        assert schema.SCATTERING_PRESET_OPTIONS[0] == {
            "label": "Select",
            "value": "",
        }
        assert schema.APPLY_TARGET_PRESET_OPTIONS[0] == {
            "label": "Select",
            "value": "",
        }

    def test_build_form_store_reads_saved_preset_preferences(self):
        """Check build form store reads saved preset preferences."""
        runtime_config = RuntimeConfig.from_dict(
            {
                "calibration": {
                    "mesf_values": [5.0e2, 5.0e3, 5.0e4, 5.0e5, 5.0e6, 5.0e7],
                    "target_model_preset": EXTRACELLULAR_VESICLES_PRESET_NAME,
                },
                "particle_model": {
                    "scatterer_preset": ROSETTA_MIX_PRESET_NAME,
                },
            }
        )

        form_store = services.build_form_store_from_runtime_config(
            runtime_config,
        )

        assert (
            form_store["default_fluorescence_reference_preset"]
            == ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME
        )
        assert form_store["default_scatterer_preset"] == ROSETTA_MIX_PRESET_NAME
        assert (
            form_store["default_apply_target_model_preset"]
            == EXTRACELLULAR_VESICLES_PRESET_NAME
        )

    def test_build_form_store_preserves_manual_selection_defaults(self):
        """Check build form store preserves manual selection defaults."""
        runtime_config = RuntimeConfig.from_dict(
            {
                "calibration": {
                    "default_fluorescence_peak_process": "",
                    "target_model_preset": "",
                },
                "scattering_calibration": {
                    "default_peak_process": "",
                },
            }
        )

        form_store = services.build_form_store_from_runtime_config(
            runtime_config,
        )

        assert form_store["default_fluorescence_peak_process"] == ""
        assert form_store["default_scattering_peak_process"] == ""
        assert form_store["default_apply_target_model_preset"] == ""

    def test_build_nested_profile_payload_saves_preset_preferences(self):
        """Check build nested profile payload saves preset preferences."""
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "default_fluorescence_reference_preset": GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME,
                "mesf_values": "123, 456",
                "default_scatterer_preset": ROSETTA_MIX_PRESET_NAME,
                "default_apply_target_model_preset": EXTRACELLULAR_VESICLES_PRESET_NAME,
            }
        )

        assert nested_profile_payload["fluorescence"]["calibration"]["mesf_values"] == [
            1000.0,
            10000.0,
            100000.0,
            1000000.0,
        ]
        assert (
            nested_profile_payload["scattering"]["particle_model"]["scatterer_preset"]
            == ROSETTA_MIX_PRESET_NAME
        )
        assert (
            nested_profile_payload["apply_calibration"]["calibration"]["target_model_preset"]
            == EXTRACELLULAR_VESICLES_PRESET_NAME
        )

    def test_build_nested_profile_payload_keeps_manual_mesf_values_for_custom_preset(self):
        """Check build nested profile payload keeps manual MESF values for custom preset."""
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "default_fluorescence_reference_preset": CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
                "mesf_values": "123, 456",
            }
        )

        assert nested_profile_payload["fluorescence"]["calibration"]["mesf_values"] == [
            123.0,
            456.0,
        ]


class Test_SettingsDefaultServicesPeakTableSortOrder:
    """Regression checks for settings default services peak table sort order."""

    def test_build_form_store_reads_saved_peak_table_sort_order_preferences(self):
        """Check build form store reads saved peak table sort order preferences."""
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
        """Check build nested profile payload saves peak table sort order preferences."""
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "fluorescence_peak_table_sort_order": "descending",
                "scattering_peak_table_sort_order": "descending",
            }
        )

        assert (
            nested_profile_payload["fluorescence"]["calibration"]["peak_table_sort_order"]
            == "descending"
        )
        assert (
            nested_profile_payload["scattering"]["calibration"]["peak_table_sort_order"]
            == "descending"
        )


class Test_SettingsDefaultServicesCanonicalSharedPaths:
    """Regression checks for settings default services canonical shared paths."""

    def test_build_nested_profile_payload_saves_shared_calibration_fields_to_canonical_paths(
        self,
    ):
        """Check build nested profile payload saves shared calibration fields to canonical paths."""
        nested_profile_payload = services.build_nested_profile_payload(
            {
                "mesf_values": "100, 200, 300",
                "default_fluorescence_peak_process": "Manual 1D",
                "target_mie_relation_xscale": "log",
                "target_mie_relation_yscale": "linear",
                "n_bins": 128,
            }
        )

        assert nested_profile_payload["fluorescence"]["calibration"]["mesf_values"] == [
            100.0,
            200.0,
            300.0,
        ]
        assert (
            nested_profile_payload["fluorescence"]["calibration"]["default_fluorescence_peak_process"]
            == "Manual 1D"
        )
        assert (
            nested_profile_payload["apply_calibration"]["calibration"]["target_mie_relation_xscale"] == "log"
        )
        assert (
            nested_profile_payload["apply_calibration"]["calibration"]["target_mie_relation_yscale"]
            == "linear"
        )
        assert nested_profile_payload["apply_calibration"]["calibration"]["n_bins_for_plots"] == 128


class Test_SettingsDefaultServicesProfileNamePersistence:
    """Regression checks for settings default services profile name persistence."""

    def test_save_profile_preserves_existing_profile_name_metadata(self):
        """Check save profile preserves existing profile name metadata."""
        saved_browser_profiles = services.save_profile(
            "custom profile",
            {
                "ui": {
                    "theme_mode": "dark",
                },
            },
            {
                "profiles": {
                    "custom profile": {
                        "profile_name": "Readable Profile Name",
                        "ui": {
                            "theme_mode": "light",
                        },
                    },
                },
                "selected_profile": "custom profile",
            },
        )

        assert (
            saved_browser_profiles["profiles"]["custom profile.json"]["profile_name"]
            == "Readable Profile Name"
        )
