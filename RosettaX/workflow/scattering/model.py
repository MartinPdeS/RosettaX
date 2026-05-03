# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional, Sequence

import plotly.graph_objs as go

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.parameters import particle_presets
from RosettaX.workflow.parameters import services as parameter_services
from RosettaX.workflow.parameters import table as parameters_table


CUSTOM_SCATTERER_PRESET_NAME = "Custom"
ROSETTA_MIX_PRESET_NAME = "Rosetta Mix"
SMALL_PARTICLE_STANDARD_PRESET_NAME = "Small particle standard"
BROAD_PARTICLE_STANDARD_PRESET_NAME = "Broad particle standard"


@dataclass(frozen=True)
class ScatteringCalibrationScattererPreset:
    """
    Preset values for scattering calibration standards.
    """

    name: str
    mie_model: str
    medium_refractive_index: float
    particle_refractive_index: float
    core_refractive_index: float
    shell_refractive_index: float
    particle_diameters_nm: tuple[float, ...] = ()
    core_diameters_nm: tuple[float, ...] = ()
    shell_thicknesses_nm: tuple[float, ...] = ()
    description: str = ""


def build_scattering_calibration_scatterer_presets() -> dict[str, ScatteringCalibrationScattererPreset]:
    """
    Build presets used when creating scattering calibration standards.
    """
    return {
        CUSTOM_SCATTERER_PRESET_NAME: ScatteringCalibrationScattererPreset(
            name=CUSTOM_SCATTERER_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.59,
            core_refractive_index=1.47,
            shell_refractive_index=1.46,
            description="Manual scatterer and calibration-standard table configuration.",
        ),
        ROSETTA_MIX_PRESET_NAME: ScatteringCalibrationScattererPreset(
            name=ROSETTA_MIX_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.59,
            core_refractive_index=1.47,
            shell_refractive_index=1.46,
            particle_diameters_nm=(994.0, 799.0, 600.0, 400.0, 296.0, 203.0, 194.0, 150.0, 125.0, 100.0, 70.0),
            description="Six-bead Rosetta mix spanning 70 nm to 500 nm.",
        ),
        SMALL_PARTICLE_STANDARD_PRESET_NAME: ScatteringCalibrationScattererPreset(
            name=SMALL_PARTICLE_STANDARD_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.45,
            core_refractive_index=1.45,
            shell_refractive_index=1.45,
            particle_diameters_nm=(80.0, 100.0, 125.0, 150.0, 200.0, 240.0),
            description="Compact small-particle calibration standard.",
        ),
        BROAD_PARTICLE_STANDARD_PRESET_NAME: ScatteringCalibrationScattererPreset(
            name=BROAD_PARTICLE_STANDARD_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.59,
            core_refractive_index=1.59,
            shell_refractive_index=1.59,
            particle_diameters_nm=(100.0, 200.0, 300.0, 400.0, 600.0, 800.0),
            description="Broad dynamic-range bead standard.",
        ),
    }


def build_scattering_calibration_scatterer_preset_options() -> list[dict[str, str]]:
    """
    Build Dash dropdown options for calibration scatterer presets.
    """
    return [
        {
            "label": preset.name,
            "value": preset.name,
        }
        for preset in build_scattering_calibration_scatterer_presets().values()
    ]


def get_scattering_calibration_scatterer_preset(
    preset_name: Any,
) -> ScatteringCalibrationScattererPreset:
    """
    Resolve one calibration scatterer preset by name.
    """
    presets = build_scattering_calibration_scatterer_presets()

    preset_name_string = str(
        preset_name or CUSTOM_SCATTERER_PRESET_NAME,
    ).strip()

    return presets.get(
        preset_name_string,
        presets[CUSTOM_SCATTERER_PRESET_NAME],
    )


@dataclass(frozen=True)
class ScatteringModelDefaults:
    """
    Default values for scattering model and optical configuration controls.
    """

    mie_model: str
    wavelength_nm: float
    detector_numerical_aperture: float
    detector_cache_numerical_aperture: float
    blocker_bar_numerical_aperture: float
    detector_sampling: int
    detector_phi_angle_degree: float
    detector_gamma_angle_degree: float
    medium_refractive_index: float
    particle_refractive_index: float
    core_refractive_index: float
    shell_refractive_index: float

    @classmethod
    def from_runtime_config(
        cls,
        runtime_config: RuntimeConfig,
    ) -> "ScatteringModelDefaults":
        """
        Build scattering defaults from a runtime configuration.
        """
        return cls(
            mie_model=runtime_config.get_str(
                "particle_model.mie_model",
                default="Solid Sphere",
            ),
            wavelength_nm=runtime_config.get_float(
                "optics.wavelength_nm",
                default=700.0,
            ),
            detector_numerical_aperture=runtime_config.get_float(
                "optics.detector_numerical_aperture",
                default=0.2,
            ),
            detector_cache_numerical_aperture=runtime_config.get_float(
                "optics.detector_cache_numerical_aperture",
                default=0.0,
            ),
            blocker_bar_numerical_aperture=runtime_config.get_float(
                "optics.blocker_bar_numerical_aperture",
                default=0.0,
            ),
            detector_sampling=runtime_config.get_int(
                "optics.detector_sampling",
                default=600,
            ),
            detector_phi_angle_degree=runtime_config.get_float(
                "optics.detector_phi_angle_degree",
                default=0.0,
            ),
            detector_gamma_angle_degree=runtime_config.get_float(
                "optics.detector_gamma_angle_degree",
                default=0.0,
            ),
            medium_refractive_index=runtime_config.get_float(
                "optics.medium_refractive_index",
                default=1.333,
            ),
            particle_refractive_index=runtime_config.get_float(
                "particle_model.particle_refractive_index",
                default=1.59,
            ),
            core_refractive_index=runtime_config.get_float(
                "particle_model.core_refractive_index",
                default=1.47,
            ),
            shell_refractive_index=runtime_config.get_float(
                "particle_model.shell_refractive_index",
                default=1.46,
            ),
        )

    @classmethod
    def from_default_profile(cls) -> "ScatteringModelDefaults":
        """
        Build scattering defaults from the default runtime profile.
        """
        return cls.from_runtime_config(
            RuntimeConfig.from_default_profile(),
        )

    def to_callback_values(self) -> tuple[Any, ...]:
        """
        Return values in the callback output order used by the scattering page.
        """
        return (
            self.mie_model,
            self.medium_refractive_index,
            self.particle_refractive_index,
            self.core_refractive_index,
            self.shell_refractive_index,
            self.wavelength_nm,
            self.detector_numerical_aperture,
            self.detector_cache_numerical_aperture,
            self.blocker_bar_numerical_aperture,
            self.detector_sampling,
            self.detector_phi_angle_degree,
            self.detector_gamma_angle_degree,
        )


class ScatteringModelConfiguration:
    """
    Reusable scattering model configuration helpers.

    This class contains logic that can be shared by the scattering calibration
    page and by the apply calibration page when building target particle models.
    """

    custom_detector_preset_name = parameter_services.CUSTOM_DETECTOR_PRESET_NAME
    custom_scatterer_preset_name = CUSTOM_SCATTERER_PRESET_NAME

    mie_model_options = particle_presets.MIE_MODEL_OPTIONS
    medium_refractive_index_presets = particle_presets.MEDIUM_REFRACTIVE_INDEX_PRESETS
    particle_refractive_index_presets = particle_presets.PARTICLE_REFRACTIVE_INDEX_PRESETS
    core_refractive_index_presets = particle_presets.CORE_REFRACTIVE_INDEX_PRESETS
    shell_refractive_index_presets = particle_presets.SHELL_REFRACTIVE_INDEX_PRESETS

    @staticmethod
    def build_defaults_from_runtime_config(
        runtime_config_data: Any,
    ) -> ScatteringModelDefaults:
        """
        Build scattering defaults from raw runtime store data.
        """
        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        return ScatteringModelDefaults.from_runtime_config(
            runtime_config,
        )

    @staticmethod
    def build_default_profile_defaults() -> ScatteringModelDefaults:
        """
        Build scattering defaults from the default runtime profile.
        """
        return ScatteringModelDefaults.from_default_profile()

    @staticmethod
    def resolve_mie_model(
        mie_model: Any,
    ) -> str:
        """
        Normalize the selected Mie model.
        """
        return parameter_services.resolve_mie_model(
            mie_model,
        )

    @staticmethod
    def build_detector_preset_options() -> list[dict[str, Any]]:
        """
        Build detector preset dropdown options.
        """
        return parameter_services.build_detector_preset_options()

    @staticmethod
    def build_scatterer_preset_options() -> list[dict[str, Any]]:
        """
        Build scatterer preset dropdown options.
        """
        return build_scattering_calibration_scatterer_preset_options()

    @staticmethod
    def resolve_runtime_scatterer_preset(
        preset_name: Any,
    ) -> str:
        """
        Resolve a persisted scatterer preset name to a known preset.
        """
        return get_scattering_calibration_scatterer_preset(
            preset_name,
        ).name

    @staticmethod
    def resolve_scatterer_preset_values(
        *,
        preset_name: Any,
        current_mie_model: Any,
        current_medium_refractive_index: Any,
        current_particle_refractive_index: Any,
        current_core_refractive_index: Any,
        current_shell_refractive_index: Any,
    ) -> tuple[Any, Any, Any, Any, Any]:
        """
        Resolve the page control values from the selected scatterer preset.

        Selecting the custom preset preserves the current manual values.
        """
        preset_name_string = str(
            preset_name or CUSTOM_SCATTERER_PRESET_NAME,
        ).strip()

        if preset_name_string == CUSTOM_SCATTERER_PRESET_NAME:
            return (
                current_mie_model,
                current_medium_refractive_index,
                current_particle_refractive_index,
                current_core_refractive_index,
                current_shell_refractive_index,
            )

        preset = get_scattering_calibration_scatterer_preset(
            preset_name_string,
        )

        return (
            preset.mie_model,
            preset.medium_refractive_index,
            preset.particle_refractive_index,
            preset.core_refractive_index,
            preset.shell_refractive_index,
        )

    @staticmethod
    def scatterer_preset_disables_manual_controls(
        *,
        preset_name: Any,
    ) -> bool:
        """
        Return whether scatterer preset selection should lock manual controls.
        """
        return str(
            preset_name or CUSTOM_SCATTERER_PRESET_NAME,
        ).strip() != CUSTOM_SCATTERER_PRESET_NAME

    @staticmethod
    def build_table_state_from_scatterer_preset(
        *,
        preset_name: Any,
        current_rows: Optional[list[dict[str, Any]]] = None,
    ) -> Optional[tuple[list[dict[str, Any]], list[dict[str, str]]]]:
        """
        Build calibration table columns and rows from a scatterer preset.

        The custom preset returns ``None`` so user-edited rows are preserved.
        """
        preset = get_scattering_calibration_scatterer_preset(
            preset_name,
        )

        if preset.name == CUSTOM_SCATTERER_PRESET_NAME:
            return None

        columns = parameters_table.get_table_columns_for_model(
            preset.mie_model,
        )

        rows = parameters_table.populate_table_from_runtime_defaults(
            mie_model=preset.mie_model,
            runtime_particle_diameters_nm=preset.particle_diameters_nm,
            runtime_core_diameters_nm=preset.core_diameters_nm,
            runtime_shell_thicknesses_nm=preset.shell_thicknesses_nm,
        )

        if current_rows is not None:
            preserved_rows = parameters_table.remap_table_rows_to_model(
                mie_model=preset.mie_model,
                current_rows=current_rows,
            )

            geometry_column_ids = (
                [
                    parameters_table.COLUMN_CORE_DIAMETER_NM,
                    parameters_table.COLUMN_SHELL_THICKNESS_NM,
                    parameters_table.COLUMN_OUTER_DIAMETER_NM,
                ]
                if preset.mie_model == parameters_table.MIE_MODEL_CORE_SHELL_SPHERE
                else [
                    parameters_table.COLUMN_PARTICLE_DIAMETER_NM,
                ]
            )

            merged_rows: list[dict[str, str]] = []

            for row_index, preset_row in enumerate(rows):
                merged_row = dict(
                    preserved_rows[row_index]
                    if row_index < len(preserved_rows)
                    else parameters_table.build_empty_row_for_model(
                        preset.mie_model,
                    )
                )

                for column_id in geometry_column_ids:
                    if column_id in preset_row:
                        merged_row[column_id] = preset_row[column_id]

                merged_rows.append(
                    merged_row,
                )

            rows = merged_rows

        return columns, rows

    @staticmethod
    def resolve_detector_configuration_visibility_style(
        *,
        preset_name: Any,
    ) -> dict[str, str]:
        """
        Return the custom detector configuration container style.
        """
        return parameter_services.resolve_detector_configuration_visibility_style(
            preset_name=preset_name,
        )

    @staticmethod
    def resolve_detector_configuration_values(
        *,
        preset_name: Any,
        current_detector_numerical_aperture: Any,
        current_detector_cache_numerical_aperture: Any,
        current_blocker_bar_numerical_aperture: Any,
        current_detector_sampling: Any,
        current_detector_phi_angle_degree: Any,
        current_detector_gamma_angle_degree: Any,
    ) -> tuple[Any, Any, Any, Any, Any, Any]:
        """
        Resolve detector configuration values from a preset or current controls.
        """
        return parameter_services.resolve_detector_configuration_values(
            preset_name=preset_name,
            current_detector_numerical_aperture=current_detector_numerical_aperture,
            current_detector_cache_numerical_aperture=current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
            current_detector_sampling=current_detector_sampling,
            current_detector_phi_angle_degree=current_detector_phi_angle_degree,
            current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
        )

    @staticmethod
    def apply_refractive_index_preset(
        *,
        preset_value: Any,
        current_value: Any,
    ) -> Any:
        """
        Apply a refractive index preset while preserving the current value when
        the preset is empty.
        """
        if preset_value is None:
            return current_value

        return float(
            preset_value,
        )

    @staticmethod
    def build_optical_configuration_preview_figure(
        *,
        detector_numerical_aperture: Any,
        blocker_bar_numerical_aperture: Any,
        medium_refractive_index: Any,
        detector_phi_angle_degree: Any,
        detector_gamma_angle_degree: Any,
    ) -> go.Figure:
        """
        Build the optical configuration preview figure.
        """
        return parameter_services.build_optical_configuration_preview_figure(
            detector_numerical_aperture=detector_numerical_aperture,
            blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
            medium_refractive_index=medium_refractive_index,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
        )

    @staticmethod
    def build_visibility_styles_for_mie_model(
        *,
        mie_model: Any,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """
        Build display styles for solid sphere and core shell control blocks.
        """
        resolved_mie_model = ScatteringModelConfiguration.resolve_mie_model(
            mie_model,
        )

        if resolved_mie_model == "Core/Shell Sphere":
            return {
                "display": "none",
            }, {
                "display": "block",
            }

        return {
            "display": "block",
        }, {
            "display": "none",
        }


def as_dropdown_options(
    options: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return a plain list of Dash dropdown options.
    """
    return [
        dict(option)
        for option in options
    ]