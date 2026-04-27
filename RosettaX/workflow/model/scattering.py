# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional, Sequence

import plotly.graph_objs as go

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.parameters import particle_presets
from RosettaX.workflow.parameters import services as parameter_services


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