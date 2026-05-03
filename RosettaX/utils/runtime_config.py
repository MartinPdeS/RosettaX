# -*- coding: utf-8 -*-
import copy
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Optional

import numpy as np

from RosettaX.utils import directories

logger = logging.getLogger(__name__)


_MISSING = object()


@dataclass(frozen=True, slots=True)
class RuntimeConfigField:
    """
    Typed definition for one known RuntimeConfig path.

    Parameters
    ----------
    expected_type:
        Python type or tuple of Python types accepted after coercion.

    default:
        Default value used when the path is absent.

    choices:
        Optional finite set of accepted values.

    minimum:
        Optional lower bound for numeric values.

    maximum:
        Optional upper bound for numeric values.

    allow_none:
        Whether None is accepted as a valid value.

    description:
        Human readable description used for debugging and future documentation.
    """

    expected_type: type | tuple[type, ...]
    default: Any = None
    choices: tuple[Any, ...] | None = None
    minimum: float | None = None
    maximum: float | None = None
    allow_none: bool = False
    description: str = ""


class RuntimeConfigValidationError(ValueError):
    """
    Error raised when a known RuntimeConfig path receives an invalid value.
    """


@dataclass(slots=True)
class RuntimeConfig:
    """
    Session-local runtime configuration container.

    Design goals
    ------------
    - Keep RuntimeConfig as the canonical source of truth for config structure,
      access, loading, and saving.
    - Avoid any hidden global mutable state.
    - Keep the public API close to the previous implementation.
    - Allow cheap reconstruction from a Dash store payload on every callback.
    - Add typed validation for known paths while preserving unknown paths for
      backward compatibility.

    Notes
    -----
    RuntimeConfig is an instance-backed object.

    Each callback should rebuild it from the current ``dcc.Store`` payload:

        runtime_config = RuntimeConfig.from_dict(runtime_config_store_data)

    and return ``runtime_config.to_dict()`` whenever the config was modified.
    """

    data: dict[str, Any] = field(default_factory=dict)
    validate_known_paths_on_init: bool = True
    preserve_unknown_paths: bool = True

    LEGACY_PATH_ALIASES: ClassVar[dict[str, str]] = {
        "fluorescence_calibration.mesf_values": "calibration.mesf_values",
        "fluorescence_calibration.peak_count": "calibration.peak_count",
        "fluorescence_calibration.default_peak_process": "calibration.default_fluorescence_peak_process",
        "fluorescence.calibration.mesf_values": "calibration.mesf_values",
        "fluorescence.calibration.peak_count": "calibration.peak_count",
        "fluorescence.calibration.default_fluorescence_peak_process": "calibration.default_fluorescence_peak_process",
        "fluorescence.calibration.peak_table_sort_order": "fluorescence_calibration.peak_table_sort_order",
        "fluorescence.files.fcs_file_path": "files.fluorescence_fcs_file_path",
        "scattering.optics.medium_refractive_index": "optics.medium_refractive_index",
        "scattering.optics.wavelength_nm": "optics.wavelength_nm",
        "scattering.optics.detector_numerical_aperture": "optics.detector_numerical_aperture",
        "scattering.optics.detector_cache_numerical_aperture": "optics.detector_cache_numerical_aperture",
        "scattering.optics.detector_sampling": "optics.detector_sampling",
        "scattering.particle_model.scatterer_preset": "particle_model.scatterer_preset",
        "scattering.particle_model.core_refractive_index": "particle_model.core_refractive_index",
        "scattering.particle_model.shell_refractive_index": "particle_model.shell_refractive_index",
        "scattering.particle_model.particle_refractive_index": "particle_model.particle_refractive_index",
        "scattering.particle_model.shell_thickness_nm": "particle_model.shell_thickness_nm",
        "scattering.particle_model.core_diameter_nm": "particle_model.core_diameter_nm",
        "scattering.particle_model.particle_diameter_nm": "particle_model.particle_diameter_nm",
        "scattering.particle_model.mie_model": "particle_model.mie_model",
        "scattering.calibration.default_peak_process": "scattering_calibration.default_peak_process",
        "scattering.calibration.peak_table_sort_order": "scattering_calibration.peak_table_sort_order",
        "scattering.calibration.default_gating_channel": "calibration.default_gating_channel",
        "scattering.calibration.default_gating_threshold": "calibration.default_gating_threshold",
        "scattering.files.fcs_file_path": "files.scattering_fcs_file_path",
        "apply_calibration.calibration.target_model_preset": "calibration.target_model_preset",
        "apply_calibration.calibration.target_mie_relation_xscale": "calibration.target_mie_relation_xscale",
        "apply_calibration.calibration.target_mie_relation_yscale": "calibration.target_mie_relation_yscale",
        "apply_calibration.calibration.histogram_xscale": "calibration.histogram_xscale",
        "apply_calibration.calibration.histogram_yscale": "calibration.histogram_yscale",
        "apply_calibration.calibration.max_events_for_analysis": "calibration.max_events_for_analysis",
        "apply_calibration.calibration.default_output_suffix": "calibration.default_output_suffix",
        "apply_calibration.calibration.n_bins_for_plots": "calibration.n_bins_for_plots",
        "apply_calibration.calibration.show_calibration_plot_by_default": "calibration.show_calibration_plot_by_default",
        "apply_calibration.calibration.histogram_scale": "calibration.histogram_scale",
        "apply_calibration.metadata.operator_name": "metadata.operator_name",
        "apply_calibration.metadata.instrument_name": "metadata.instrument_name",
        "apply_calibration.visualization.graph_height": "visualization.graph_height",
        "apply_calibration.visualization.default_marker_size": "visualization.default_marker_size",
        "apply_calibration.visualization.default_line_width": "visualization.default_line_width",
        "apply_calibration.visualization.default_font_size": "visualization.default_font_size",
        "apply_calibration.visualization.default_tick_size": "visualization.default_tick_size",
        "apply_calibration.visualization.show_grid_by_default": "visualization.show_grid_by_default",
        "misc.ui.theme_mode": "ui.theme_mode",
        "misc.ui.show_graphs": "ui.show_graphs",
        "scattering_calibration.default_gating_channel": "calibration.default_gating_channel",
        "scattering_calibration.default_gating_threshold": "calibration.default_gating_threshold",
        "scattering_calibration.target_mie_relation_xscale": "calibration.target_mie_relation_xscale",
        "scattering_calibration.target_mie_relation_yscale": "calibration.target_mie_relation_yscale",
        # Older profiles stored the scattering peak process under calibration.
        "calibration.default_scattering_peak_process": "scattering_calibration.default_peak_process",
        "visualization.n_bins": "calibration.n_bins_for_plots",
        "visualization.n_bins_for_plots": "calibration.n_bins_for_plots",
        "visualization.show_calibration": "calibration.show_calibration_plot_by_default",
    }

    SCHEMA: ClassVar[dict[str, RuntimeConfigField]] = {
        # ---------------------------------------------------------------------
        # UI
        # ---------------------------------------------------------------------
        "ui.theme_mode": RuntimeConfigField(
            expected_type=str,
            default="dark",
            choices=("dark", "light"),
            description="Application theme mode.",
        ),
        "ui.show_graphs": RuntimeConfigField(
            expected_type=bool,
            default=True,
            description="Whether graphs are shown by default.",
        ),
        # ---------------------------------------------------------------------
        # Files
        # ---------------------------------------------------------------------
        "files.fluorescence_fcs_file_path": RuntimeConfigField(
            expected_type=str,
            default="",
            description="Default fluorescence FCS file path.",
        ),
        "files.scattering_fcs_file_path": RuntimeConfigField(
            expected_type=str,
            default="",
            description="Default scattering FCS file path.",
        ),
        # ---------------------------------------------------------------------
        # Calibration
        # ---------------------------------------------------------------------
        "calibration.mesf_values": RuntimeConfigField(
            expected_type=list,
            default=[],
            description="Default MESF reference values.",
        ),
        "calibration.peak_count": RuntimeConfigField(
            expected_type=int,
            default=6,
            minimum=1,
            description="Default expected number of calibration peaks.",
        ),
        "calibration.default_fluorescence_peak_process": RuntimeConfigField(
            expected_type=str,
            default="Automatic 1D",
            description="Preferred fluorescence peak detection process.",
        ),
        "calibration.histogram_scale": RuntimeConfigField(
            expected_type=str,
            default="log",
            choices=("linear", "log"),
            description="Default histogram count axis scale.",
        ),
        "calibration.histogram_xscale": RuntimeConfigField(
            expected_type=str,
            default="linear",
            choices=("linear", "log"),
            description="Default histogram x axis scale.",
        ),
        "calibration.histogram_yscale": RuntimeConfigField(
            expected_type=str,
            default="log",
            choices=("linear", "log"),
            description="Default histogram y axis scale.",
        ),
        "calibration.default_gating_channel": RuntimeConfigField(
            expected_type=str,
            default="",
            description="Default gating channel.",
        ),
        "calibration.default_gating_threshold": RuntimeConfigField(
            expected_type=float,
            default=0.0,
            description="Default gating threshold.",
        ),
        "calibration.max_events_for_analysis": RuntimeConfigField(
            expected_type=int,
            default=100000,
            minimum=1,
            description="Maximum number of events used for analysis.",
        ),
        "calibration.n_bins_for_plots": RuntimeConfigField(
            expected_type=int,
            default=256,
            minimum=1,
            description="Default number of histogram bins.",
        ),
        "calibration.default_output_suffix": RuntimeConfigField(
            expected_type=str,
            default="_calibrated",
            description="Default suffix used for calibrated output files.",
        ),
        "calibration.show_calibration_plot_by_default": RuntimeConfigField(
            expected_type=bool,
            default=True,
            description="Whether calibration plots are visible by default.",
        ),
        "calibration.target_model_preset": RuntimeConfigField(
            expected_type=str,
            default="Custom",
            description="Default target model preset for the apply calibration page.",
        ),
        "calibration.target_mie_relation_xscale": RuntimeConfigField(
            expected_type=str,
            default="linear",
            choices=("linear", "log"),
            description="Default target Mie relation x axis scale.",
        ),
        "calibration.target_mie_relation_yscale": RuntimeConfigField(
            expected_type=str,
            default="log",
            choices=("linear", "log"),
            description="Default target Mie relation y axis scale.",
        ),
        # ---------------------------------------------------------------------
        # Fluorescence calibration
        # ---------------------------------------------------------------------
        "fluorescence_calibration.peak_table_sort_order": RuntimeConfigField(
            expected_type=str,
            default="ascending",
            choices=("ascending", "descending"),
            description="Preferred fluorescence peak table ordering.",
        ),
        # ---------------------------------------------------------------------
        # Scattering calibration
        # ---------------------------------------------------------------------
        "scattering_calibration.peak_table_sort_order": RuntimeConfigField(
            expected_type=str,
            default="ascending",
            choices=("ascending", "descending"),
            description="Preferred scattering peak table ordering.",
        ),
        "scattering_calibration.default_peak_process": RuntimeConfigField(
            expected_type=str,
            default="Automatic 1D",
            description="Preferred scattering peak detection process.",
        ),
        # ---------------------------------------------------------------------
        # Optics
        # ---------------------------------------------------------------------
        "optics.wavelength_nm": RuntimeConfigField(
            expected_type=float,
            default=488.0,
            minimum=0.0,
            description="Optical wavelength in nanometers.",
        ),
        "optics.medium_refractive_index": RuntimeConfigField(
            expected_type=float,
            default=1.333,
            minimum=1.0,
            description="Medium refractive index.",
        ),
        "optics.detector_numerical_aperture": RuntimeConfigField(
            expected_type=float,
            default=0.45,
            minimum=0.0,
            maximum=1.49,
            description="Detector numerical aperture.",
        ),
        "optics.detector_cache_numerical_aperture": RuntimeConfigField(
            expected_type=float,
            default=0.45,
            minimum=0.0,
            maximum=1.49,
            description="Numerical aperture used for detector cache.",
        ),
        "optics.detector_sampling": RuntimeConfigField(
            expected_type=int,
            default=1000,
            minimum=1,
            description="Detector angular or numerical sampling.",
        ),
        # ---------------------------------------------------------------------
        # Particle model
        # ---------------------------------------------------------------------
        "particle_model.mie_model": RuntimeConfigField(
            expected_type=str,
            default="Solid Sphere",
            choices=("Solid Sphere", "Core/Shell Sphere"),
            description="Scattering particle model.",
        ),
        "particle_model.scatterer_preset": RuntimeConfigField(
            expected_type=str,
            default="Custom",
            description="Default scatterer preset for the scattering calibration page.",
        ),
        "particle_model.particle_refractive_index": RuntimeConfigField(
            expected_type=float,
            default=1.45,
            minimum=1.0,
            description="Homogeneous particle refractive index.",
        ),
        "particle_model.core_refractive_index": RuntimeConfigField(
            expected_type=float,
            default=1.45,
            minimum=1.0,
            description="Core refractive index for core shell particles.",
        ),
        "particle_model.shell_refractive_index": RuntimeConfigField(
            expected_type=float,
            default=1.40,
            minimum=1.0,
            description="Shell refractive index for core shell particles.",
        ),
        "particle_model.particle_diameter_nm": RuntimeConfigField(
            expected_type=list,
            default=[],
            description="Default particle diameter list in nanometers.",
        ),
        "particle_model.core_diameter_nm": RuntimeConfigField(
            expected_type=list,
            default=[],
            description="Default core diameter list in nanometers.",
        ),
        "particle_model.shell_thickness_nm": RuntimeConfigField(
            expected_type=list,
            default=[],
            description="Default shell thickness list in nanometers.",
        ),
        # ---------------------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------------------
        "metadata.operator_name": RuntimeConfigField(
            expected_type=str,
            default="",
            description="Default operator name stored in generated outputs.",
        ),
        "metadata.instrument_name": RuntimeConfigField(
            expected_type=str,
            default="",
            description="Default instrument name stored in generated outputs.",
        ),
        # ---------------------------------------------------------------------
        # Visualization
        # ---------------------------------------------------------------------
        "visualization.graph_height": RuntimeConfigField(
            expected_type=str,
            default="850px",
            description="Default graph height CSS value.",
        ),
        "visualization.default_marker_size": RuntimeConfigField(
            expected_type=float,
            default=7.0,
            minimum=0.0,
            description="Default marker size.",
        ),
        "visualization.default_line_width": RuntimeConfigField(
            expected_type=float,
            default=2.0,
            minimum=0.0,
            description="Default line width.",
        ),
        "visualization.default_font_size": RuntimeConfigField(
            expected_type=float,
            default=14.0,
            minimum=1.0,
            description="Default font size.",
        ),
        "visualization.default_tick_size": RuntimeConfigField(
            expected_type=float,
            default=12.0,
            minimum=1.0,
            description="Default tick size.",
        ),
        "visualization.show_grid_by_default": RuntimeConfigField(
            expected_type=bool,
            default=True,
            description="Whether plot grid lines are shown by default.",
        ),
    }

    def __post_init__(self) -> None:
        if not isinstance(self.data, dict):
            raise TypeError(
                f"RuntimeConfig data must be a dictionary, got {type(self.data).__name__}."
            )

        self.data = copy.deepcopy(self.data)

        if self.validate_known_paths_on_init:
            self.data = self._normalized_payload(
                payload=self.data,
                preserve_unknown_paths=self.preserve_unknown_paths,
                raise_on_invalid=False,
            )

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
        logger.debug(
            "RuntimeConfig.from_json_path called with path=%r", str(resolved_json_path)
        )

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
        logger.debug(
            "RuntimeConfig.from_profile_name resolved json_path=%r", str(json_path)
        )
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
                logger.debug(
                    "Default profile candidate does not exist: %r", str(json_path)
                )
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

        logger.warning(
            "No valid default profile could be loaded. Using empty RuntimeConfig."
        )
        return cls()

    @staticmethod
    def _split_path(path: str) -> list[str]:
        normalized_path = str(path).strip()
        if not normalized_path:
            raise ValueError("Path cannot be empty.")

        return [path_part for path_part in normalized_path.split(".") if path_part]

    @classmethod
    def _get_nested_value(
        cls,
        data: dict[str, Any],
        path: str,
        default: Any = _MISSING,
    ) -> Any:
        current_value: Any = data

        for path_part in cls._split_path(path):
            if not isinstance(current_value, dict):
                return None if default is _MISSING else default
            if path_part not in current_value:
                return None if default is _MISSING else default
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

    @classmethod
    def _delete_nested_path(cls, data: dict[str, Any], path: str) -> None:
        path_parts = cls._split_path(path)
        current_value: Any = data
        parent_stack: list[tuple[dict[str, Any], str]] = []

        for path_part in path_parts[:-1]:
            if not isinstance(current_value, dict):
                return

            next_value = current_value.get(path_part)

            if not isinstance(next_value, dict):
                return

            parent_stack.append((current_value, path_part))
            current_value = next_value

        if not isinstance(current_value, dict):
            return

        removed_value = current_value.pop(path_parts[-1], _MISSING)

        if removed_value is _MISSING:
            return

        for parent_dict, parent_key in reversed(parent_stack):
            child_value = parent_dict.get(parent_key)

            if isinstance(child_value, dict) and not child_value:
                parent_dict.pop(parent_key, None)
                continue

            break

    @classmethod
    def _has_nested_path(cls, data: dict[str, Any], path: str) -> bool:
        current_value: Any = data

        for path_part in cls._split_path(path):
            if not isinstance(current_value, dict):
                return False
            if path_part not in current_value:
                return False
            current_value = current_value[path_part]

        return True

    @classmethod
    def _apply_legacy_aliases(cls, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_payload = copy.deepcopy(payload)

        for source_path, target_path in cls.LEGACY_PATH_ALIASES.items():
            if not cls._has_nested_path(normalized_payload, source_path):
                continue

            if cls._has_nested_path(normalized_payload, target_path):
                cls._delete_nested_path(normalized_payload, source_path)
                continue

            source_value = cls._get_nested_value(normalized_payload, source_path)
            cls._set_nested_value(
                normalized_payload,
                target_path,
                copy.deepcopy(source_value),
            )
            cls._delete_nested_path(normalized_payload, source_path)

        return normalized_payload

    @classmethod
    def _preprocess_known_value(
        cls,
        *,
        path: str,
        value: Any,
        config_field: RuntimeConfigField,
    ) -> Any:
        if value is None and not config_field.allow_none:
            return copy.deepcopy(config_field.default)

        if config_field.expected_type is list and isinstance(
            value,
            (int, float, np.integer, np.floating),
        ):
            return [float(value)]

        return value

    @classmethod
    def _normalized_payload(
        cls,
        payload: dict[str, Any],
        *,
        preserve_unknown_paths: bool,
        raise_on_invalid: bool,
    ) -> dict[str, Any]:
        payload = cls._apply_legacy_aliases(payload)

        if preserve_unknown_paths:
            normalized_payload = copy.deepcopy(payload)
        else:
            normalized_payload = {}

        for path, config_field in cls.SCHEMA.items():
            if cls._has_nested_path(payload, path):
                raw_value = cls._get_nested_value(payload, path)
            else:
                raw_value = config_field.default

            raw_value = cls._preprocess_known_value(
                path=path,
                value=raw_value,
                config_field=config_field,
            )

            try:
                coerced_value = cls._coerce_value(
                    path=path,
                    value=raw_value,
                    config_field=config_field,
                )
            except RuntimeConfigValidationError:
                if raise_on_invalid:
                    raise

                logger.warning(
                    "Invalid RuntimeConfig value at path=%r value=%r. Falling back to default=%r.",
                    path,
                    raw_value,
                    config_field.default,
                )
                coerced_value = copy.deepcopy(config_field.default)

            cls._set_nested_value(normalized_payload, path, coerced_value)

        return normalized_payload

    @classmethod
    def _coerce_value(
        cls,
        *,
        path: str,
        value: Any,
        config_field: RuntimeConfigField,
    ) -> Any:
        if value is None:
            if config_field.allow_none:
                return None

            raise RuntimeConfigValidationError(
                f"RuntimeConfig path {path!r} does not allow None."
            )

        if config_field.expected_type is bool:
            coerced_value = cls._coerce_bool(path=path, value=value)

        elif config_field.expected_type is int:
            coerced_value = cls._coerce_int(path=path, value=value)

        elif config_field.expected_type is float:
            coerced_value = cls._coerce_float(path=path, value=value)

        elif config_field.expected_type is str:
            coerced_value = cls._coerce_str(value=value)

        elif config_field.expected_type is list:
            coerced_value = cls._coerce_list(path=path, value=value)

        else:
            if not isinstance(value, config_field.expected_type):
                expected_type_name = cls._format_expected_type_name(
                    config_field.expected_type
                )
                raise RuntimeConfigValidationError(
                    f"RuntimeConfig path {path!r} expected {expected_type_name}, "
                    f"got {type(value).__name__}."
                )
            coerced_value = value

        if (
            config_field.choices is not None
            and coerced_value not in config_field.choices
        ):
            raise RuntimeConfigValidationError(
                f"RuntimeConfig path {path!r} expected one of {config_field.choices!r}, "
                f"got {coerced_value!r}."
            )

        if config_field.minimum is not None and isinstance(coerced_value, (int, float)):
            if coerced_value < config_field.minimum:
                raise RuntimeConfigValidationError(
                    f"RuntimeConfig path {path!r} must be >= {config_field.minimum}, "
                    f"got {coerced_value!r}."
                )

        if config_field.maximum is not None and isinstance(coerced_value, (int, float)):
            if coerced_value > config_field.maximum:
                raise RuntimeConfigValidationError(
                    f"RuntimeConfig path {path!r} must be <= {config_field.maximum}, "
                    f"got {coerced_value!r}."
                )

        return coerced_value

    @staticmethod
    def _coerce_bool(*, path: str, value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized_value = value.strip().lower()

            if normalized_value in {"true", "yes", "1", "on", "enabled"}:
                return True

            if normalized_value in {"false", "no", "0", "off", "disabled"}:
                return False

        if isinstance(value, (int, np.integer)):
            if int(value) in {0, 1}:
                return bool(value)

        raise RuntimeConfigValidationError(
            f"RuntimeConfig path {path!r} expected a boolean-compatible value, got {value!r}."
        )

    @staticmethod
    def _coerce_int(*, path: str, value: Any) -> int:
        if isinstance(value, bool):
            raise RuntimeConfigValidationError(
                f"RuntimeConfig path {path!r} expected int, got bool."
            )

        if isinstance(value, (int, np.integer)):
            return int(value)

        if isinstance(value, (float, np.floating)):
            float_value = float(value)

            if float_value.is_integer():
                return int(float_value)

            raise RuntimeConfigValidationError(
                f"RuntimeConfig path {path!r} expected integer value, got float={value!r}."
            )

        if isinstance(value, str):
            normalized_value = value.strip()

            try:
                float_value = float(normalized_value)
            except ValueError as exception:
                raise RuntimeConfigValidationError(
                    f"RuntimeConfig path {path!r} expected integer-compatible string, "
                    f"got {value!r}."
                ) from exception

            if float_value.is_integer():
                return int(float_value)

        raise RuntimeConfigValidationError(
            f"RuntimeConfig path {path!r} expected int-compatible value, got {value!r}."
        )

    @staticmethod
    def _coerce_float(*, path: str, value: Any) -> float:
        if isinstance(value, bool):
            raise RuntimeConfigValidationError(
                f"RuntimeConfig path {path!r} expected float, got bool."
            )

        if isinstance(value, (int, float, np.integer, np.floating)):
            return float(value)

        if isinstance(value, str):
            normalized_value = value.strip()

            try:
                return float(normalized_value)
            except ValueError as exception:
                raise RuntimeConfigValidationError(
                    f"RuntimeConfig path {path!r} expected float-compatible string, "
                    f"got {value!r}."
                ) from exception

        raise RuntimeConfigValidationError(
            f"RuntimeConfig path {path!r} expected float-compatible value, got {value!r}."
        )

    @staticmethod
    def _coerce_str(*, value: Any) -> str:
        return str(value).strip()

    @staticmethod
    def _coerce_list(*, path: str, value: Any) -> list[Any]:
        if isinstance(value, list):
            return copy.deepcopy(value)

        if isinstance(value, tuple):
            return list(value)

        if isinstance(value, np.ndarray):
            return value.tolist()

        raise RuntimeConfigValidationError(
            f"RuntimeConfig path {path!r} expected list-compatible value, got {value!r}."
        )

    @staticmethod
    def _format_expected_type_name(expected_type: type | tuple[type, ...]) -> str:
        if isinstance(expected_type, tuple):
            return " or ".join(item.__name__ for item in expected_type)

        return expected_type.__name__

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
        return self.__class__.from_dict(self.data)

    def validate(self) -> None:
        """
        Validate all known paths strictly.

        Unknown paths are allowed when ``preserve_unknown_paths`` is True. This
        method is useful in tests and before saving user-created profiles.
        """
        self._normalized_payload(
            payload=self.data,
            preserve_unknown_paths=self.preserve_unknown_paths,
            raise_on_invalid=True,
        )

    def normalized(self) -> "RuntimeConfig":
        """
        Return a normalized copy with all known defaults materialized.
        """
        normalized_payload = self._normalized_payload(
            payload=self.data,
            preserve_unknown_paths=self.preserve_unknown_paths,
            raise_on_invalid=True,
        )
        return self.__class__.from_dict(normalized_payload)

    def get_path(self, path: str, default: Any = _MISSING) -> Any:
        if default is _MISSING and path in self.__class__.SCHEMA:
            default = self.__class__.SCHEMA[path].default

        resolved_value = self._get_nested_value(self.data, path, default=default)

        logger.debug(
            "RuntimeConfig.get_path called with path=%r default=%r resolved_value=%r",
            path,
            None if default is _MISSING else default,
            resolved_value,
        )
        return resolved_value

    def set_path(self, path: str, value: Any) -> None:
        if path in self.__class__.SCHEMA:
            value = self._coerce_value(
                path=path,
                value=value,
                config_field=self.__class__.SCHEMA[path],
            )

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

        try:
            return self._coerce_bool(path=path, value=value)
        except RuntimeConfigValidationError:
            logger.debug(
                "RuntimeConfig.get_bool could not coerce value=%r at path=%r. Returning default=%r",
                value,
                path,
                default,
            )
            return default

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
            return self._coerce_float(path=path, value=value)
        except RuntimeConfigValidationError:
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
            return self._coerce_int(path=path, value=value)
        except RuntimeConfigValidationError:
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
                "ui.theme_mode": "light",
                "ui.show_graphs": True,
                "optics.wavelength_nm": 532,
            }
        )
        """
        logger.debug(
            "RuntimeConfig.update_paths called with path_value_pairs=%r",
            path_value_pairs,
        )

        for path, value in path_value_pairs.items():
            self.set_path(path=path, value=value)

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
        if not normalized_filename:
            raise ValueError("Profile filename cannot be empty.")

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

        self.data = self._normalized_payload(
            payload=payload,
            preserve_unknown_paths=self.preserve_unknown_paths,
            raise_on_invalid=False,
        )

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

        self.validate()

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
