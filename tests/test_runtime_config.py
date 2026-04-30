# -*- coding: utf-8 -*-

import json
from pathlib import Path

import numpy as np
import pytest

from RosettaX.utils import runtime_config as runtime_config_module
from RosettaX.utils.runtime_config import RuntimeConfig, RuntimeConfigValidationError


class Test_RuntimeConfig:
    def test_from_dict_rejects_non_dictionary_payload(self) -> None:
        with pytest.raises(TypeError, match="expected a dictionary"):
            RuntimeConfig.from_dict(["not", "a", "dictionary"])

    def test_constructor_rejects_non_dictionary_payload(self) -> None:
        with pytest.raises(TypeError, match="must be a dictionary"):
            RuntimeConfig(data=["not", "a", "dictionary"])

    def test_from_dict_deep_copies_input_payload(self) -> None:
        original_payload = {
            "ui": {
                "theme_mode": "dark",
                "show_graphs": True,
            }
        }

        runtime_config = RuntimeConfig.from_dict(original_payload)
        original_payload["ui"]["theme_mode"] = "light"

        assert runtime_config.get_path("ui.theme_mode") == "dark"

    def test_to_dict_returns_deep_copy(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "dark",
                }
            }
        )

        exported_payload = runtime_config.to_dict()
        exported_payload["ui"]["theme_mode"] = "light"

        assert runtime_config.get_path("ui.theme_mode") == "dark"

    def test_empty_config_materializes_known_schema_defaults(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        exported_payload = runtime_config.to_dict()

        assert exported_payload["ui"]["theme_mode"] == "dark"
        assert exported_payload["ui"]["show_graphs"] is True

        assert exported_payload["calibration"]["peak_count"] == 6
        assert exported_payload["calibration"]["histogram_scale"] == "log"
        assert exported_payload["calibration"]["n_bins_for_plots"] == 256

        assert exported_payload["optics"]["wavelength_nm"] == pytest.approx(488.0)
        assert exported_payload["optics"]["medium_refractive_index"] == pytest.approx(1.333)
        assert exported_payload["optics"]["detector_numerical_aperture"] == pytest.approx(0.45)

        assert exported_payload["particle_model"]["mie_model"] == "Solid Sphere"
        assert exported_payload["particle_model"]["particle_refractive_index"] == pytest.approx(1.45)

        assert exported_payload["visualization"]["default_line_width"] == pytest.approx(2.0)
        assert exported_payload["visualization"]["show_grid_by_default"] is True

    def test_unknown_paths_are_preserved_by_default(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "custom": {
                    "experimental_parameter": 42,
                },
            }
        )

        assert runtime_config.get_path("custom.experimental_parameter") == 42
        assert runtime_config.to_dict()["custom"]["experimental_parameter"] == 42

    def test_to_dict_converts_numpy_values_into_json_safe_values(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "array_value": np.asarray([1.0, 2.0, 3.0]),
                "float_value": np.float64(1.25),
                "integer_value": np.int64(5),
                "tuple_value": (1, 2, 3),
                "nested": {
                    "array_value": np.asarray([[1, 2], [3, 4]]),
                },
            }
        )

        exported_payload = runtime_config.to_dict()

        assert exported_payload["array_value"] == [1.0, 2.0, 3.0]
        assert exported_payload["float_value"] == pytest.approx(1.25)
        assert exported_payload["integer_value"] == 5
        assert exported_payload["tuple_value"] == [1, 2, 3]
        assert exported_payload["nested"]["array_value"] == [[1, 2], [3, 4]]

        json.dumps(exported_payload)

    def test_get_path_returns_nested_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "optics": {
                    "wavelength_nm": 532.0,
                }
            }
        )

        assert runtime_config.get_path("optics.wavelength_nm") == pytest.approx(532.0)

    def test_get_path_returns_schema_default_for_missing_known_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        assert runtime_config.get_path("optics.wavelength_nm") == pytest.approx(488.0)

    def test_get_path_returns_explicit_default_for_missing_unknown_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        assert runtime_config.get_path("unknown.path", default=532.0) == pytest.approx(532.0)

    def test_get_path_returns_default_when_intermediate_value_is_not_dictionary(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "custom": 488.0,
            }
        )

        assert runtime_config.get_path("custom.wavelength_nm", default=532.0) == pytest.approx(532.0)

    def test_set_path_creates_nested_dictionaries_for_unknown_path(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.set_path("custom.detector.numerical_aperture", 0.75)

        assert runtime_config.get_path("custom.detector.numerical_aperture") == pytest.approx(0.75)

    def test_set_path_replaces_non_dictionary_intermediate_value_for_unknown_path(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "custom": "invalid intermediate value",
            }
        )

        runtime_config.set_path("custom.detector.numerical_aperture", 0.75)

        assert runtime_config.get_path("custom.detector.numerical_aperture") == pytest.approx(0.75)

    def test_empty_path_raises_value_error(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(ValueError, match="Path cannot be empty"):
            runtime_config.get_path("")

        with pytest.raises(ValueError, match="Path cannot be empty"):
            runtime_config.set_path("   ", 1)

    @pytest.mark.parametrize(
        ("raw_value", "expected_value"),
        [
            (True, True),
            (False, False),
            ("true", True),
            ("yes", True),
            ("1", True),
            ("on", True),
            ("enabled", True),
            ("false", False),
            ("no", False),
            ("0", False),
            ("off", False),
            ("disabled", False),
            (1, True),
            (0, False),
        ],
    )
    def test_get_bool_coerces_expected_values(
        self,
        raw_value: object,
        expected_value: bool,
    ) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "show_graphs": raw_value,
                }
            }
        )

        assert runtime_config.get_bool("ui.show_graphs") is expected_value

    def test_get_bool_returns_default_for_uncoercible_unknown_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "custom": {
                    "flag": "maybe",
                }
            }
        )

        assert runtime_config.get_bool("custom.flag", default=True) is True

    def test_get_str_strips_whitespace(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "  dark  ",
                }
            }
        )

        assert runtime_config.get_str("ui.theme_mode") == "dark"

    def test_get_float_coerces_known_string_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "optics": {
                    "wavelength_nm": "532.5",
                }
            }
        )

        assert runtime_config.get_float("optics.wavelength_nm") == pytest.approx(532.5)
        assert runtime_config.to_dict()["optics"]["wavelength_nm"] == pytest.approx(532.5)

    def test_get_float_returns_default_for_invalid_unknown_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "custom": {
                    "wavelength_nm": "not a float",
                }
            }
        )

        assert runtime_config.get_float("custom.wavelength_nm", default=488.0) == pytest.approx(488.0)

    def test_get_int_coerces_known_integer_like_string(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "calibration": {
                    "peak_count": "8",
                }
            }
        )

        assert runtime_config.get_int("calibration.peak_count") == 8
        assert runtime_config.to_dict()["calibration"]["peak_count"] == 8

    def test_get_int_coerces_known_integer_like_float(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "calibration": {
                    "peak_count": 8.0,
                }
            }
        )

        assert runtime_config.get_int("calibration.peak_count") == 8
        assert runtime_config.to_dict()["calibration"]["peak_count"] == 8

    def test_get_int_returns_default_for_invalid_unknown_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "sampling": {
                    "event_count": "not an integer",
                }
            }
        )

        assert runtime_config.get_int("sampling.event_count", default=1000) == 1000

    @pytest.mark.parametrize(
        ("raw_theme_mode", "expected_theme_mode"),
        [
            ("dark", "dark"),
            ("light", "light"),
            ("DARK", "dark"),
            ("LIGHT", "light"),
            ("invalid", "dark"),
            ("", "dark"),
        ],
    )
    def test_get_theme_mode_returns_supported_theme_or_default(
        self,
        raw_theme_mode: str,
        expected_theme_mode: str,
    ) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": raw_theme_mode,
                }
            }
        )

        assert runtime_config.get_theme_mode(default="dark") == expected_theme_mode

    def test_get_show_graphs_uses_ui_show_graphs_path(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "show_graphs": "disabled",
                }
            }
        )

        assert runtime_config.get_show_graphs(default=True) is False

    def test_set_path_validates_known_choice(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.set_path("ui.theme_mode", "light")

        assert runtime_config.get_path("ui.theme_mode") == "light"

    def test_set_path_rejects_invalid_theme_choice(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="ui.theme_mode"):
            runtime_config.set_path("ui.theme_mode", "pink")

    def test_set_path_rejects_invalid_histogram_scale(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="calibration.histogram_scale"):
            runtime_config.set_path("calibration.histogram_scale", "sqrt")

    def test_set_path_rejects_negative_wavelength(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="optics.wavelength_nm"):
            runtime_config.set_path("optics.wavelength_nm", -488.0)

    def test_set_path_rejects_invalid_numerical_aperture_above_maximum(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="optics.detector_numerical_aperture"):
            runtime_config.set_path("optics.detector_numerical_aperture", 2.0)

    def test_set_path_rejects_non_integer_peak_count(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="calibration.peak_count"):
            runtime_config.set_path("calibration.peak_count", 4.2)

    def test_set_path_accepts_numpy_array_for_known_list_path(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.set_path("calibration.mesf_values", np.asarray([100.0, 200.0, 300.0]))

        assert runtime_config.get_path("calibration.mesf_values") == [100.0, 200.0, 300.0]

    def test_from_dict_falls_back_to_default_for_invalid_known_values(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "pink",
                },
                "optics": {
                    "wavelength_nm": "not-a-number",
                },
            }
        )

        exported_payload = runtime_config.to_dict()

        assert exported_payload["ui"]["theme_mode"] == "dark"
        assert exported_payload["optics"]["wavelength_nm"] == pytest.approx(488.0)

    def test_validate_raises_for_invalid_known_value_after_direct_data_mutation(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.data["ui"]["theme_mode"] = "pink"

        with pytest.raises(RuntimeConfigValidationError, match="ui.theme_mode"):
            runtime_config.validate()

    def test_normalized_returns_validated_copy(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "light",
                },
                "optics": {
                    "wavelength_nm": "640",
                },
            }
        )

        normalized_runtime_config = runtime_config.normalized()

        assert normalized_runtime_config.get_path("ui.theme_mode") == "light"
        assert normalized_runtime_config.get_path("optics.wavelength_nm") == pytest.approx(640.0)
        assert normalized_runtime_config.get_path("calibration.peak_count") == 6

    def test_update_preserves_backward_compatible_flat_keys(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.update(theme_mode="dark", show_graphs=True)

        assert runtime_config.get_path("theme_mode") == "dark"
        assert runtime_config.get_path("show_graphs") is True

    def test_update_paths_updates_and_validates_nested_values(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.update_paths(
            **{
                "ui.theme_mode": "light",
                "ui.show_graphs": False,
                "optics.wavelength_nm": "640",
                "calibration.peak_count": "4",
            }
        )

        assert runtime_config.get_path("ui.theme_mode") == "light"
        assert runtime_config.get_path("ui.show_graphs") is False
        assert runtime_config.get_path("optics.wavelength_nm") == pytest.approx(640.0)
        assert runtime_config.get_path("calibration.peak_count") == 4

    def test_update_paths_rejects_invalid_known_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="particle_model.mie_model"):
            runtime_config.update_paths(
                **{
                    "particle_model.mie_model": "Cylinder",
                }
            )

    def test_with_path_returns_modified_copy_without_mutating_original(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "dark",
                }
            }
        )

        updated_runtime_config = runtime_config.with_path("ui.theme_mode", "light")

        assert runtime_config.get_path("ui.theme_mode") == "dark"
        assert updated_runtime_config.get_path("ui.theme_mode") == "light"

    def test_with_path_rejects_invalid_known_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        with pytest.raises(RuntimeConfigValidationError, match="ui.theme_mode"):
            runtime_config.with_path("ui.theme_mode", "pink")

    def test_with_updates_returns_modified_copy_without_mutating_original(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "theme_mode": "dark",
            }
        )

        updated_runtime_config = runtime_config.with_updates(theme_mode="light")

        assert runtime_config.get_path("theme_mode") == "dark"
        assert updated_runtime_config.get_path("theme_mode") == "light"

    def test_with_path_updates_returns_modified_copy_without_mutating_original(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "dark",
                }
            }
        )

        updated_runtime_config = runtime_config.with_path_updates(
            **{
                "ui.theme_mode": "light",
                "ui.show_graphs": False,
            }
        )

        assert runtime_config.get_path("ui.theme_mode") == "dark"
        assert runtime_config.get_path("ui.show_graphs") is True
        assert updated_runtime_config.get_path("ui.theme_mode") == "light"
        assert updated_runtime_config.get_path("ui.show_graphs") is False

    def test_json_round_trip_preserves_normalized_payload(self, tmp_path: Path) -> None:
        json_path = tmp_path / "runtime_config.json"

        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "dark",
                    "show_graphs": True,
                },
                "optics": {
                    "wavelength_nm": "532",
                },
            }
        )

        runtime_config.to_json_path(json_path)
        loaded_runtime_config = RuntimeConfig.from_json_path(json_path)

        assert loaded_runtime_config.to_dict() == runtime_config.to_dict()

    def test_to_json_path_validates_before_writing(self, tmp_path: Path) -> None:
        runtime_config = RuntimeConfig.from_dict({})
        runtime_config.data["ui"]["theme_mode"] = "pink"

        json_path = tmp_path / "invalid_runtime_config.json"

        with pytest.raises(RuntimeConfigValidationError, match="ui.theme_mode"):
            runtime_config.to_json_path(json_path)

        assert not json_path.exists()

    def test_to_json_returns_json_safe_string(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "custom": {
                    "array": np.asarray([1, 2, 3]),
                    "float": np.float64(1.5),
                    "integer": np.int64(4),
                }
            }
        )

        json_payload = runtime_config.to_json()
        loaded_payload = json.loads(json_payload)

        assert loaded_payload["custom"]["array"] == [1, 2, 3]
        assert loaded_payload["custom"]["float"] == pytest.approx(1.5)
        assert loaded_payload["custom"]["integer"] == 4

    def test_from_json_path_rejects_non_dictionary_json(self, tmp_path: Path) -> None:
        json_path = tmp_path / "invalid_runtime_config.json"
        json_path.write_text("[1, 2, 3]", encoding="utf-8")

        with pytest.raises(TypeError, match="must contain a JSON object"):
            RuntimeConfig.from_json_path(json_path)

    def test_load_json_mutates_only_current_instance(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(runtime_config_module.directories, "profiles", tmp_path)

        profile_path = tmp_path / "test_profile.json"
        profile_path.write_text(
            json.dumps(
                {
                    "ui": {
                        "theme_mode": "light",
                    }
                }
            ),
            encoding="utf-8",
        )

        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "dark",
                }
            }
        )

        exported_payload = runtime_config.load_json("test_profile")

        assert runtime_config.get_path("ui.theme_mode") == "light"
        assert exported_payload["ui"]["theme_mode"] == "light"

    def test_from_profile_name_adds_json_extension(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(runtime_config_module.directories, "profiles", tmp_path)

        profile_path = tmp_path / "custom_profile.json"
        profile_path.write_text(
            json.dumps(
                {
                    "ui": {
                        "theme_mode": "light",
                    }
                }
            ),
            encoding="utf-8",
        )

        runtime_config = RuntimeConfig.from_profile_name("custom_profile")

        assert runtime_config.get_path("ui.theme_mode") == "light"

    def test_from_profile_name_rejects_empty_profile_name(self) -> None:
        with pytest.raises(ValueError, match="Profile filename cannot be empty"):
            RuntimeConfig.from_profile_name("   ")

    def test_from_default_profile_uses_default_profile_first(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        default_profile_path = tmp_path / "startup_default.json"
        profiles_directory = tmp_path / "profiles"
        profiles_directory.mkdir()

        default_profile_path.write_text(
            json.dumps(
                {
                    "ui": {
                        "theme_mode": "dark",
                    }
                }
            ),
            encoding="utf-8",
        )

        fallback_profile_path = profiles_directory / "default_profile.json"
        fallback_profile_path.write_text(
            json.dumps(
                {
                    "ui": {
                        "theme_mode": "light",
                    }
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(runtime_config_module.directories, "default_profile", default_profile_path)
        monkeypatch.setattr(runtime_config_module.directories, "profiles", profiles_directory)

        runtime_config = RuntimeConfig.from_default_profile()

        assert runtime_config.get_path("ui.theme_mode") == "dark"

    def test_from_default_profile_falls_back_to_profiles_default_profile(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        missing_default_profile_path = tmp_path / "missing_startup_default.json"
        profiles_directory = tmp_path / "profiles"
        profiles_directory.mkdir()

        fallback_profile_path = profiles_directory / "default_profile.json"
        fallback_profile_path.write_text(
            json.dumps(
                {
                    "ui": {
                        "theme_mode": "light",
                    }
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(runtime_config_module.directories, "default_profile", missing_default_profile_path)
        monkeypatch.setattr(runtime_config_module.directories, "profiles", profiles_directory)

        runtime_config = RuntimeConfig.from_default_profile()

        assert runtime_config.get_path("ui.theme_mode") == "light"

    def test_from_default_profile_returns_default_schema_when_no_candidate_exists(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(runtime_config_module.directories, "default_profile", tmp_path / "missing.json")
        monkeypatch.setattr(runtime_config_module.directories, "profiles", tmp_path / "missing_profiles")

        runtime_config = RuntimeConfig.from_default_profile()

        assert runtime_config.get_path("ui.theme_mode") == "dark"
        assert runtime_config.get_path("ui.show_graphs") is True
        assert runtime_config.get_path("optics.wavelength_nm") == pytest.approx(488.0)


if __name__ == "__main__":
    pytest.main(["-W error", __file__])