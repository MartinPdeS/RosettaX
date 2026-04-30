# -*- coding: utf-8 -*-
import copy
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import numpy as np

from RosettaX.utils import directories


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeConfig:
    """
    Session-local runtime configuration container.

    Design goals
    ------------
    - Keep RuntimeConfig as the canonical source of truth for config structure,
      access, loading, and saving.
    - Avoid any hidden global mutable state.
    - Keep the public API simple and close to the previous implementation.
    - Allow cheap reconstruction from a Dash store payload on every callback.

    Notes
    -----
    RuntimeConfig is now a plain instance-backed object.
    Each callback should rebuild it from the current ``dcc.Store`` payload:

        runtime_config = RuntimeConfig.from_dict(runtime_config_store_data)

    and return ``runtime_config.to_dict()`` whenever the config was modified.
    """

    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.data, dict):
            raise TypeError(
                f"RuntimeConfig data must be a dictionary, got {type(self.data).__name__}."
            )
        self.data = copy.deepcopy(self.data)
        logger.debug("Initialized RuntimeConfig with keys=%r", list(self.data.keys()))

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "RuntimeConfig":
        """
        Build a RuntimeConfig from an in-memory dictionary payload.
        """
        if data is None:
            logger.debug("RuntimeConfig.from_dict received None. Using empty payload.")
            return cls()

        if not isinstance(data, dict):
            raise TypeError(
                f"RuntimeConfig.from_dict expected a dictionary, got {type(data).__name__}."
            )

        logger.debug("RuntimeConfig.from_dict received keys=%r", list(data.keys()))
        return cls(data=data)

    @classmethod
    def from_json_path(cls, json_path: Path | str) -> "RuntimeConfig":
        """
        Build a RuntimeConfig from a JSON file path.
        """
        resolved_json_path = Path(json_path).expanduser().resolve()
        logger.debug("RuntimeConfig.from_json_path called with path=%r", str(resolved_json_path))

        with resolved_json_path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)

        if not isinstance(payload, dict):
            raise TypeError(
                f"Runtime config JSON must contain a JSON object, got {type(payload).__name__}."
            )

        logger.debug(
            "Loaded RuntimeConfig from path=%r with keys=%r",
            str(resolved_json_path),
            list(payload.keys()),
        )
        return cls.from_dict(payload)

    @classmethod
    def from_profile_name(cls, json_filename: str) -> "RuntimeConfig":
        """
        Build a RuntimeConfig from a profile name located in ``directories.profiles``.
        """
        normalized_filename = str(json_filename).strip()
        if not normalized_filename:
            raise ValueError("Profile filename cannot be empty.")

        if not normalized_filename.endswith(".json"):
            normalized_filename = f"{normalized_filename}.json"

        json_path = Path(directories.profiles) / normalized_filename
        logger.debug("RuntimeConfig.from_profile_name resolved json_path=%r", str(json_path))
        return cls.from_json_path(json_path)

    @classmethod
    def from_default_profile(cls) -> "RuntimeConfig":
        """
        Load the startup default profile.

        The first valid JSON object found among the candidate paths becomes the
        initial runtime payload.
        """
        candidate_paths = [
            Path(directories.default_profile),
            Path(directories.profiles) / "default_profile.json",
        ]

        for json_path in candidate_paths:
            if not json_path.exists():
                logger.debug("Default profile candidate does not exist: %r", str(json_path))
                continue

            try:
                runtime_config = cls.from_json_path(json_path)
                logger.debug("Loaded startup default profile from %r", str(json_path))
                return runtime_config
            except Exception:
                logger.exception(
                    "Failed to load startup default profile from json_path=%r",
                    str(json_path),
                )

        logger.warning("No valid default profile could be loaded. Using empty RuntimeConfig.")
        return cls()

    @staticmethod
    def _split_path(path: str) -> list[str]:
        normalized_path = str(path).strip()
        if not normalized_path:
            raise ValueError("Path cannot be empty.")

        return [part for part in normalized_path.split(".") if part]

    @classmethod
    def _get_nested_value(cls, data: dict[str, Any], path: str, default: Any = None) -> Any:
        current_value: Any = data

        for path_part in cls._split_path(path):
            if not isinstance(current_value, dict):
                return default
            if path_part not in current_value:
                return default
            current_value = current_value[path_part]

        return current_value

    @classmethod
    def _set_nested_value(cls, data: dict[str, Any], path: str, value: Any) -> None:
        path_parts = cls._split_path(path)
        current_dict = data

        for path_part in path_parts[:-1]:
            next_value = current_dict.get(path_part)

            if not isinstance(next_value, dict):
                next_value = {}
                current_dict[path_part] = next_value

            current_dict = next_value

        current_dict[path_parts[-1]] = value

    def to_dict(self) -> dict[str, Any]:
        """
        Return a deep copied payload safe to place into Dash stores.
        """
        runtime_config_dict = copy.deepcopy(self.data)
        runtime_config_dict = self._make_json_safe(runtime_config_dict)

        logger.debug(
            "RuntimeConfig.to_dict returning keys=%r",
            list(runtime_config_dict.keys()),
        )
        return runtime_config_dict

    def copy(self) -> "RuntimeConfig":
        """
        Return a deep copied RuntimeConfig instance.
        """
        logger.debug("Creating RuntimeConfig copy.")
        return RuntimeConfig.from_dict(self.data)

    def get_path(self, path: str, default: Any = None) -> Any:
        """
        Retrieve a value from the configuration using a dotted path.

        Parameters
        ----------
        path : str
            Dot-separated key path, e.g. ``"ui.theme_mode"``.
        default : Any
            Value returned when the path does not exist.

        Returns
        -------
        Any
            The value at *path*, or *default* if not found.
        """
        resolved_value = self._get_nested_value(self.data, path, default=default)
        logger.debug(
            "RuntimeConfig.get_path called with path=%r default=%r resolved_value=%r",
            path,
            default,
            resolved_value,
        )
        return resolved_value

    def set_path(self, path: str, value: Any) -> None:
        """
        Set a value in the configuration using a dotted path.

        Intermediate dictionaries are created automatically when they do not
        already exist.

        Parameters
        ----------
        path : str
            Dot-separated key path, e.g. ``"ui.theme_mode"``.
        value : Any
            Value to store at *path*.
        """
        old_value = self._get_nested_value(self.data, path, default=None)
        self._set_nested_value(self.data, path, value)
        logger.debug(
            "RuntimeConfig.set_path updated path=%r from %r to %r",
            path,
            old_value,
            value,
        )

    def get_str(self, path: str, default: str = "") -> str:
        """
        Retrieve a configuration value as a stripped string.

        Parameters
        ----------
        path : str
            Dot-separated key path.
        default : str
            Fallback string when the path does not exist or the value is
            ``None``.

        Returns
        -------
        str
            The value coerced to a stripped string, or *default*.
        """
        value = self.get_path(path, default=default)
        if value is None:
            return default
        return str(value).strip()

    def get_bool(self, path: str, default: bool = False) -> bool:
        """
        Retrieve a configuration value as a boolean.

        String values such as ``"true"``, ``"yes"``, ``"1"``, ``"on"``, and
        ``"enabled"`` are interpreted as ``True``; ``"false"``, ``"no"``,
        ``"0"``, ``"off"``, and ``"disabled"`` as ``False``.

        Parameters
        ----------
        path : str
            Dot-separated key path.
        default : bool
            Fallback value when the path does not exist.

        Returns
        -------
        bool
            The resolved boolean value.
        """
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
        """
        Retrieve a configuration value as a float.

        Parameters
        ----------
        path : str
            Dot-separated key path.
        default : Optional[float]
            Fallback value when the path does not exist or the value cannot be
            coerced to a float.

        Returns
        -------
        Optional[float]
            The value coerced to ``float``, or *default*.
        """
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
        """
        Retrieve a configuration value as an integer.

        Parameters
        ----------
        path : str
            Dot-separated key path.
        default : Optional[int]
            Fallback value when the path does not exist or the value cannot be
            coerced to an integer.

        Returns
        -------
        Optional[int]
            The value coerced to ``int``, or *default*.
        """
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
        theme_mode = self.get_str("ui.theme_mode", default=default).lower()
        return theme_mode if theme_mode in {"dark", "light"} else default

    def get_show_graphs(self, default: bool = True) -> bool:
        """
        Convenience accessor for graph visibility preference.
        """
        return self.get_bool("ui.show_graphs", default=default)

    def update(self, **kwargs: Any) -> None:
        """
        Update the runtime configuration with flat keys.

        This keeps backward compatibility with older parts of the codebase that
        still expect flat key assignment.
        """
        logger.debug("RuntimeConfig.update called with kwargs=%r", kwargs)

        for key, value in kwargs.items():
            old_value = self.data.get(key, None)
            self.data[key] = value
            logger.debug(
                "Updated flat runtime key %s from %r to %r",
                key,
                old_value,
                value,
            )

    def update_paths(self, **path_value_pairs: Any) -> None:
        """
        Update the runtime configuration using dotted paths.

        Example
        -------
        runtime_config.update_paths(
            **{
                "app.theme_mode": "light",
                "app.show_graphs": True,
                "optics.wavelength_nm": 532,
            }
        )
        """
        logger.debug(
            "RuntimeConfig.update_paths called with path_value_pairs=%r",
            path_value_pairs,
        )

        for path, value in path_value_pairs.items():
            old_value = self._get_nested_value(self.data, path, default=None)
            self._set_nested_value(self.data, path, value)
            logger.debug(
                "Updated nested runtime path %s from %r to %r",
                path,
                old_value,
                value,
            )

    def with_path(self, path: str, value: Any) -> "RuntimeConfig":
        """
        Return a new RuntimeConfig with one updated nested path.
        """
        runtime_config = self.copy()
        runtime_config.set_path(path, value)
        return runtime_config

    def with_updates(self, **kwargs: Any) -> "RuntimeConfig":
        """
        Return a new RuntimeConfig with updated flat keys.
        """
        runtime_config = self.copy()
        runtime_config.update(**kwargs)
        return runtime_config

    def with_path_updates(self, **path_value_pairs: Any) -> "RuntimeConfig":
        """
        Return a new RuntimeConfig with updated dotted paths.
        """
        runtime_config = self.copy()
        runtime_config.update_paths(**path_value_pairs)
        return runtime_config

    def load_json(self, json_filename: str) -> dict[str, Any]:
        """
        Load a profile JSON file into this RuntimeConfig instance.

        This preserves the old method name for compatibility, but it now mutates
        only this instance, never any hidden global object.
        """
        normalized_filename = str(json_filename).strip()
        if not normalized_filename.endswith(".json"):
            normalized_filename = f"{normalized_filename}.json"

        json_path = Path(directories.profiles) / normalized_filename
        logger.debug("RuntimeConfig.load_json called with json_path=%r", str(json_path))

        with json_path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)

        if not isinstance(payload, dict):
            raise TypeError(
                f"Runtime config JSON must contain a JSON object, got {type(payload).__name__}."
            )

        self.data = copy.deepcopy(payload)
        logger.debug(
            "Loaded RuntimeConfig instance from JSON json_path=%r keys=%r",
            str(json_path),
            list(payload.keys()),
        )
        return self.to_dict()

    def __repr__(self) -> str:
        representation = f"RuntimeConfig({self.data!r})"
        logger.debug("RuntimeConfig.__repr__ returning %r", representation)
        return representation

    def to_json(self, *, indent: int = 2) -> str:
        """
        Serialise the configuration to a JSON string.

        Parameters
        ----------
        indent : int
            Number of spaces used for indentation.

        Returns
        -------
        str
            JSON representation of the configuration.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_json_path(self, json_path: Path | str, *, indent: int = 2) -> None:
        """
        Write the configuration to a JSON file.

        Parent directories are created automatically if they do not exist.

        Parameters
        ----------
        json_path : Path | str
            Destination file path.
        indent : int
            Number of spaces used for indentation.
        """
        resolved_json_path = Path(json_path).expanduser().resolve()
        resolved_json_path.parent.mkdir(parents=True, exist_ok=True)

        with resolved_json_path.open("w", encoding="utf-8") as file_handle:
            json.dump(self.to_dict(), file_handle, indent=indent, ensure_ascii=False)

        logger.debug(
            "RuntimeConfig.to_json_path wrote config to path=%r",
            str(resolved_json_path),
        )

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        """
        Recursively convert NumPy types and arrays to JSON-serialisable objects.

        ``np.ndarray`` → ``list``; ``np.generic`` scalars → Python native; dict
        keys are cast to ``str``; lists and tuples are traversed recursively.

        Parameters
        ----------
        value : Any
            Arbitrary value that may contain NumPy objects.

        Returns
        -------
        Any
            The value with all NumPy types replaced by JSON-safe equivalents.
        """
        if isinstance(value, np.ndarray):
            return value.tolist()

        if isinstance(value, np.generic):
            return value.item()

        if isinstance(value, dict):
            return {
                str(key): RuntimeConfig._make_json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [RuntimeConfig._make_json_safe(item) for item in value]

        return value