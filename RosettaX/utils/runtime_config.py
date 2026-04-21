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

    without requiring every key to be hardcoded in Python.
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

    def update(self, **kwargs) -> None:
        """
        Update the runtime configuration with new values.

        Any provided key is accepted. The profile JSON defines the schema.
        """
        logger.debug("RuntimeConfig.update called with kwargs=%r", kwargs)

        for key, value in kwargs.items():
            old_value = self.Default.to_dict().get(key, None)
            setattr(self.Default, key, value)
            logger.debug(
                "Updated RuntimeConfig.Default.%s from %r to %r",
                key,
                old_value,
                value,
            )

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