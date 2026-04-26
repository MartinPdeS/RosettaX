# -*- coding: utf-8 -*-

import json
from pathlib import Path

import numpy as np
import pytest

from RosettaX.utils import runtime_config as runtime_config_module
from RosettaX.utils.runtime_config import RuntimeConfig


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

        assert exported_payload == {
            "array_value": [1.0, 2.0, 3.0],
            "float_value": 1.25,
            "integer_value": 5,
            "tuple_value": [1, 2, 3],
            "nested": {
                "array_value": [[1, 2], [3, 4]],
            },
        }

        json.dumps(exported_payload)

    def test_get_path_returns_nested_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "optics": {
                    "wavelength_nm": 488.0,
                }
            }
        )

        assert runtime_config.get_path("optics.wavelength_nm") == 488.0

    def test_get_path_returns_default_for_missing_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        assert runtime_config.get_path("optics.wavelength_nm", default=532.0) == 532.0

    def test_get_path_returns_default_when_intermediate_value_is_not_dictionary(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "optics": 488.0,
            }
        )

        assert runtime_config.get_path("optics.wavelength_nm", default=532.0) == 532.0

    def test_set_path_creates_nested_dictionaries(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.set_path("optics.detector.numerical_aperture", 0.75)

        assert runtime_config.to_dict() == {
            "optics": {
                "detector": {
                    "numerical_aperture": 0.75,
                }
            }
        }

    def test_set_path_replaces_non_dictionary_intermediate_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "optics": "invalid intermediate value",
            }
        )

        runtime_config.set_path("optics.detector.numerical_aperture", 0.75)

        assert runtime_config.get_path("optics.detector.numerical_aperture") == 0.75

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

    def test_get_str_strips_whitespace(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "  dark  ",
                }
            }
        )

        assert runtime_config.get_str("ui.theme_mode") == "dark"

    def test_get_float_returns_default_for_invalid_value(self) -> None:
        runtime_config = RuntimeConfig.from_dict(
            {
                "optics": {
                    "wavelength_nm": "not a float",
                }
            }
        )

        assert runtime_config.get_float("optics.wavelength_nm", default=488.0) == 488.0

    def test_get_int_returns_default_for_invalid_value(self) -> None:
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

    def test_update_preserves_backward_compatible_flat_keys(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.update(theme_mode="dark", show_graphs=True)

        assert runtime_config.to_dict() == {
            "theme_mode": "dark",
            "show_graphs": True,
        }

    def test_update_paths_updates_nested_values(self) -> None:
        runtime_config = RuntimeConfig.from_dict({})

        runtime_config.update_paths(
            **{
                "ui.theme_mode": "light",
                "ui.show_graphs": False,
            }
        )

        assert runtime_config.get_path("ui.theme_mode") == "light"
        assert runtime_config.get_path("ui.show_graphs") is False

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
        assert runtime_config.get_path("ui.show_graphs") is None
        assert updated_runtime_config.get_path("ui.theme_mode") == "light"
        assert updated_runtime_config.get_path("ui.show_graphs") is False

    def test_json_round_trip_preserves_payload(self, tmp_path: Path) -> None:
        json_path = tmp_path / "runtime_config.json"

        runtime_config = RuntimeConfig.from_dict(
            {
                "ui": {
                    "theme_mode": "dark",
                    "show_graphs": True,
                },
                "optics": {
                    "wavelength_nm": 488.0,
                },
            }
        )

        runtime_config.to_json_path(json_path)
        loaded_runtime_config = RuntimeConfig.from_json_path(json_path)

        assert loaded_runtime_config.to_dict() == runtime_config.to_dict()

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

    def test_from_default_profile_returns_empty_config_when_no_candidate_exists(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(runtime_config_module.directories, "default_profile", tmp_path / "missing.json")
        monkeypatch.setattr(runtime_config_module.directories, "profiles", tmp_path / "missing_profiles")

        runtime_config = RuntimeConfig.from_default_profile()

        assert runtime_config.to_dict() == {}


if __name__ == "__main__":
    pytest.main(["-W error", __file__])