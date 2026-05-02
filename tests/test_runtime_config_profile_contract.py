# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pytest

from RosettaX.utils import directories
from RosettaX.utils.runtime_config import RuntimeConfig, RuntimeConfigValidationError


def collect_profile_paths() -> list[Path]:
    profile_directory = Path(directories.profiles)

    if not profile_directory.exists():
        return []

    return sorted(profile_directory.glob("*.json"))


class Test_RuntimeConfigProfileContract:
    def test_profile_directory_exists(self) -> None:
        profile_directory = Path(directories.profiles)

        assert profile_directory.exists(), (
            f"Profile directory does not exist: {profile_directory}"
        )
        assert profile_directory.is_dir(), (
            f"Profile path is not a directory: {profile_directory}"
        )

    def test_at_least_one_profile_json_file_exists(self) -> None:
        profile_paths = collect_profile_paths()

        assert profile_paths, "No profile JSON files were found."

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_contains_dictionary_payload(self, profile_path: Path) -> None:
        with profile_path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)

        assert isinstance(payload, dict), (
            f"Profile {profile_path.name} must contain a JSON object."
        )

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_matches_runtime_config_schema(self, profile_path: Path) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)

        try:
            runtime_config.validate()
        except RuntimeConfigValidationError as exception:
            raise AssertionError(
                f"Profile {profile_path.name} does not match the RuntimeConfig schema: "
                f"{exception}"
            ) from exception

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_round_trips_through_runtime_config(
        self,
        profile_path: Path,
        tmp_path: Path,
    ) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)

        output_path = tmp_path / profile_path.name
        runtime_config.to_json_path(output_path)

        reloaded_runtime_config = RuntimeConfig.from_json_path(output_path)

        assert reloaded_runtime_config.to_dict() == runtime_config.to_dict()

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_materializes_expected_top_level_sections(
        self,
        profile_path: Path,
    ) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)
        payload = runtime_config.to_dict()

        expected_top_level_sections = {
            "ui",
            "files",
            "calibration",
            "fluorescence_calibration",
            "optics",
            "particle_model",
            "scattering_calibration",
            "metadata",
            "visualization",
        }

        missing_sections = expected_top_level_sections.difference(payload)

        assert not missing_sections, (
            f"Profile {profile_path.name} is missing top level sections after "
            f"RuntimeConfig normalization: {sorted(missing_sections)}"
        )

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_has_valid_ui_values(self, profile_path: Path) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)
        payload = runtime_config.to_dict()

        assert payload["ui"]["theme_mode"] in {"dark", "light"}
        assert isinstance(payload["ui"]["show_graphs"], bool)

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_has_valid_calibration_values(self, profile_path: Path) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)
        payload = runtime_config.to_dict()

        assert isinstance(payload["calibration"]["mesf_values"], list)
        assert isinstance(payload["calibration"]["peak_count"], int)
        assert payload["calibration"]["peak_count"] >= 1

        assert payload["calibration"]["histogram_scale"] in {"linear", "log"}

        assert isinstance(payload["calibration"]["max_events_for_analysis"], int)
        assert payload["calibration"]["max_events_for_analysis"] >= 1

        assert isinstance(payload["calibration"]["n_bins_for_plots"], int)
        assert payload["calibration"]["n_bins_for_plots"] >= 1

        assert isinstance(payload["calibration"]["show_calibration_plot_by_default"], bool)

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_has_valid_optics_values(self, profile_path: Path) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)
        payload = runtime_config.to_dict()

        assert payload["optics"]["wavelength_nm"] > 0.0
        assert payload["optics"]["medium_refractive_index"] >= 1.0

        assert 0.0 <= payload["optics"]["detector_numerical_aperture"] <= 1.49
        assert 0.0 <= payload["optics"]["detector_cache_numerical_aperture"] <= 1.49

        assert isinstance(payload["optics"]["detector_sampling"], int)
        assert payload["optics"]["detector_sampling"] >= 1

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_has_valid_particle_model_values(self, profile_path: Path) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)
        payload = runtime_config.to_dict()

        assert payload["particle_model"]["mie_model"] in {
            "Solid Sphere",
            "Core/Shell Sphere",
        }

        assert payload["particle_model"]["particle_refractive_index"] >= 1.0
        assert payload["particle_model"]["core_refractive_index"] >= 1.0
        assert payload["particle_model"]["shell_refractive_index"] >= 1.0

        assert payload["particle_model"]["particle_diameter_nm"] >= 0.0
        assert payload["particle_model"]["core_diameter_nm"] >= 0.0
        assert payload["particle_model"]["shell_thickness_nm"] >= 0.0

    @pytest.mark.parametrize("profile_path", collect_profile_paths())
    def test_profile_json_file_has_valid_visualization_values(self, profile_path: Path) -> None:
        runtime_config = RuntimeConfig.from_json_path(profile_path)
        payload = runtime_config.to_dict()

        assert payload["visualization"]["default_marker_size"] >= 0.0
        assert payload["visualization"]["default_line_width"] >= 0.0
        assert payload["visualization"]["default_font_size"] >= 1.0
        assert payload["visualization"]["default_tick_size"] >= 1.0
        assert isinstance(payload["visualization"]["show_grid_by_default"], bool)

    def test_default_profile_can_be_loaded_and_validated(self) -> None:
        runtime_config = RuntimeConfig.from_default_profile()

        runtime_config.validate()

        payload = runtime_config.to_dict()

        assert payload["ui"]["theme_mode"] in {"dark", "light"}
        assert payload["optics"]["wavelength_nm"] > 0.0
        assert payload["calibration"]["peak_count"] >= 1
        assert payload["particle_model"]["mie_model"] in {
            "Solid Sphere",
            "Core/Shell Sphere",
        }


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
