from dataclasses import dataclass
from pathlib import Path
from typing import Optional, ClassVar, Any
import json
import logging

from RosettaX.utils import directories

logger = logging.getLogger(__name__)


class _RuntimeDefaultNamespace:
    """
    Dynamic attribute container backed by a dictionary.

    This object lets the rest of the code keep using:

        runtime_config.Default.some_key

    for flat keys, while RuntimeConfig also provides nested path based accessors
    for structured profiles.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "_data", {})

    def load_dict(self, data: dict[str, Any]) -> None:
        object.__setattr__(self, "_data", dict(data))

    def update_dict(self, data: dict[str, Any]) -> None:
        self._data.update(data)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self._data[name] = value

    def __contains__(self, name: str) -> bool:
        return name in self._data

    def __repr__(self) -> str:
        return f"_RuntimeDefaultNamespace({self._data!r})"


@dataclass
class RuntimeConfig:
    _instance: ClassVar[Optional["RuntimeConfig"]] = None
    _initialized: ClassVar[bool] = False

    Default: ClassVar[_RuntimeDefaultNamespace] = _RuntimeDefaultNamespace()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("Created new RuntimeConfig singleton instance.")
        else:
            logger.debug("Reusing existing RuntimeConfig singleton instance.")

        return cls._instance

    def __init__(self, *args, **kwargs):
        if self.__class__._initialized:
            logger.debug("RuntimeConfig already initialized. Skipping __init__.")
            return

        self.__class__._initialized = True
        logger.debug("Initializing RuntimeConfig singleton.")

        self._load_default_profile_on_startup()

    def _load_default_profile_on_startup(self) -> None:
        """
        Load the startup defaults from the default profile file.

        The JSON profile is the source of truth for all default fields.
        """
        candidate_paths = [
            Path(directories.default_profile),
            Path(directories.profiles) / "default_profile.json",
        ]

        for json_path in candidate_paths:
            if not json_path.exists():
                continue

            try:
                with json_path.open("r", encoding="utf-8") as file_handle:
                    data = json.load(file_handle)

                if not isinstance(data, dict):
                    raise TypeError(
                        f"Default profile must contain a JSON object, got {type(data).__name__}."
                    )

                self.Default.load_dict(data)
                logger.debug(
                    "Loaded startup default profile from json_path=%r with keys=%r",
                    str(json_path),
                    list(data.keys()),
                )
                return

            except Exception:
                logger.exception(
                    "Failed to load startup default profile from json_path=%r",
                    str(json_path),
                )

        logger.warning(
            "No valid default profile could be loaded. RuntimeConfig.Default is empty."
        )
        self.Default.load_dict({})

    @staticmethod
    def _split_path(path: str) -> list[str]:
        normalized_path = str(path).strip()
        if not normalized_path:
            raise ValueError("Path cannot be empty.")
        return [part for part in normalized_path.split(".") if part]

    @staticmethod
    def _get_nested_value(data: dict[str, Any], path: str, default: Any = None) -> Any:
        current_value: Any = data

        for path_part in RuntimeConfig._split_path(path):
            if not isinstance(current_value, dict):
                return default

            if path_part not in current_value:
                return default

            current_value = current_value[path_part]

        return current_value

    @staticmethod
    def _set_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
        path_parts = RuntimeConfig._split_path(path)

        current_dict = data
        for path_part in path_parts[:-1]:
            next_value = current_dict.get(path_part)

            if not isinstance(next_value, dict):
                next_value = {}
                current_dict[path_part] = next_value

            current_dict = next_value

        current_dict[path_parts[-1]] = value

    def get_path(self, path: str, default: Any = None) -> Any:
        runtime_config_dict = self.Default.to_dict()
        resolved_value = self._get_nested_value(runtime_config_dict, path, default=default)

        logger.debug(
            "RuntimeConfig.get_path called with path=%r default=%r resolved_value=%r",
            path,
            default,
            resolved_value,
        )
        return resolved_value

    def set_path(self, path: str, value: Any) -> None:
        runtime_config_dict = self.Default.to_dict()
        old_value = self._get_nested_value(runtime_config_dict, path, default=None)

        self._set_nested_value(runtime_config_dict, path, value)
        self.Default.load_dict(runtime_config_dict)

        logger.debug(
            "RuntimeConfig.set_path updated path=%r from %r to %r",
            path,
            old_value,
            value,
        )

    def get_str(self, path: str, default: str = "") -> str:
        value = self.get_path(path, default=default)
        if value is None:
            return default
        return str(value).strip()

    def get_bool(self, path: str, default: bool = False) -> bool:
        value = self.get_path(path, default=default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_value in {"true", "yes", "1", "on", "enabled"}:
                return True
            if normalized_value in {"false", "no", "0", "off", "disabled"}:
                return False

        return bool(value)

    def get_float(self, path: str, default: Optional[float] = None) -> Optional[float]:
        value = self.get_path(path, default=default)

        if value is None:
            return default

        try:
            return float(value)
        except (TypeError, ValueError):
            logger.debug(
                "RuntimeConfig.get_float could not coerce value=%r at path=%r. Returning default=%r",
                value,
                path,
                default,
            )
            return default

    def get_int(self, path: str, default: Optional[int] = None) -> Optional[int]:
        value = self.get_path(path, default=default)

        if value is None:
            return default

        try:
            return int(value)
        except (TypeError, ValueError):
            logger.debug(
                "RuntimeConfig.get_int could not coerce value=%r at path=%r. Returning default=%r",
                value,
                path,
                default,
            )
            return default

    def get_theme_mode(self, default: str = "dark") -> str:
        """
        Convenience accessor for the application theme.
        """
        theme_mode = self.get_str("app.theme_mode", default=default).lower()
        return theme_mode if theme_mode in {"dark", "light"} else default

    def get_show_graphs(self, default: bool = True) -> bool:
        """
        Convenience accessor for graph visibility preference.
        """
        return self.get_bool("app.show_graphs", default=default)

    def update(self, **kwargs) -> None:
        """
        Update the runtime configuration with flat keys.

        This keeps backward compatibility with older parts of the codebase.
        """
        logger.debug("RuntimeConfig.update called with kwargs=%r", kwargs)

        runtime_config_dict = self.Default.to_dict()

        for key, value in kwargs.items():
            old_value = runtime_config_dict.get(key, None)
            runtime_config_dict[key] = value
            logger.debug(
                "Updated flat runtime key %s from %r to %r",
                key,
                old_value,
                value,
            )

        self.Default.load_dict(runtime_config_dict)

    def update_paths(self, **path_value_pairs) -> None:
        """
        Update the runtime configuration using dotted paths.

        Example:
            runtime_config.update_paths(
                **{
                    "app.theme_mode": "light",
                    "app.show_graphs": True,
                    "optics.wavelength_nm": 532,
                }
            )
        """
        logger.debug("RuntimeConfig.update_paths called with path_value_pairs=%r", path_value_pairs)

        runtime_config_dict = self.Default.to_dict()

        for path, value in path_value_pairs.items():
            old_value = self._get_nested_value(runtime_config_dict, path, default=None)
            self._set_nested_value(runtime_config_dict, path, value)
            logger.debug(
                "Updated nested runtime path %s from %r to %r",
                path,
                old_value,
                value,
            )

        self.Default.load_dict(runtime_config_dict)

    @classmethod
    def get_instance(cls) -> "RuntimeConfig":
        logger.debug("RuntimeConfig.get_instance called.")
        return cls()

    def load_json(self, json_filename: str) -> dict[str, Any]:
        """
        Load a profile JSON file into the runtime configuration.
        """
        normalized_filename = str(json_filename).strip()
        if not normalized_filename.endswith(".json"):
            normalized_filename = f"{normalized_filename}.json"

        json_path = Path(directories.profiles) / normalized_filename
        logger.debug("RuntimeConfig.load_json called with json_path=%r", str(json_path))

        try:
            with json_path.open("r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)

            if not isinstance(data, dict):
                raise TypeError(
                    f"Runtime config JSON must contain a JSON object, got {type(data).__name__}."
                )

            self.Default.load_dict(data)

            logger.debug(
                "Loaded RuntimeConfig.Default from JSON json_path=%r keys=%r",
                str(json_path),
                list(data.keys()),
            )
            return data

        except Exception:
            logger.exception("Failed to load JSON config from json_path=%r", str(json_path))
            return {}

    def __repr__(self) -> str:
        representation = f"RuntimeConfig({self.Default.to_dict()!r})"
        logger.debug("RuntimeConfig.__repr__ returning %r", representation)
        return representation

    def to_dict(self) -> dict[str, Any]:
        runtime_config_dict = self.Default.to_dict()
        logger.debug("RuntimeConfig.to_dict returning %r", runtime_config_dict)
        return runtime_config_dict