# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any


CUSTOM_PRESET_NAME = "Custom"
EXTRACELLULAR_VESICLES_PRESET_NAME = "Extracellular Vesicles"
POLYSTYRENE_BEADS_PRESET_NAME = "Polystyrene Beads"
SILICA_BEADS_PRESET_NAME = "Silica Beads"


@dataclass(frozen=True)
class ScatteringTargetModelPreset:
    """
    Preset values for the scattering target model controls.

    The preset stores both solid sphere and core shell defaults so the Dash UI
    can switch model types without losing a complete preset state.
    """

    name: str
    mie_model: str
    medium_refractive_index: float

    particle_refractive_index: float
    particle_diameter_min_nm: float
    particle_diameter_max_nm: float
    particle_diameter_count: int

    core_refractive_index: float
    shell_refractive_index: float
    shell_thickness_nm: float
    core_diameter_min_nm: float
    core_diameter_max_nm: float
    core_diameter_count: int

    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the preset into a plain dictionary.
        """
        return asdict(
            self,
        )


def build_scattering_target_model_presets() -> dict[str, ScatteringTargetModelPreset]:
    """
    Build available scattering target model presets.

    The extracellular vesicle preset assumes the core shell model because it
    provides an explicit membrane shell thickness and lets the fitted diameter
    axis represent the vesicle core diameter.
    """
    return {
        CUSTOM_PRESET_NAME: ScatteringTargetModelPreset(
            name=CUSTOM_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.39,
            particle_diameter_min_nm=30.0,
            particle_diameter_max_nm=1000.0,
            particle_diameter_count=500,
            core_refractive_index=1.37,
            shell_refractive_index=1.46,
            shell_thickness_nm=5.0,
            core_diameter_min_nm=30.0,
            core_diameter_max_nm=1000.0,
            core_diameter_count=500,
            description="Manual target model configuration.",
        ),
        EXTRACELLULAR_VESICLES_PRESET_NAME: ScatteringTargetModelPreset(
            name=EXTRACELLULAR_VESICLES_PRESET_NAME,
            mie_model="Core/Shell Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.38,
            particle_diameter_min_nm=30.0,
            particle_diameter_max_nm=1000.0,
            particle_diameter_count=500,
            core_refractive_index=1.37,
            shell_refractive_index=1.46,
            shell_thickness_nm=5.0,
            core_diameter_min_nm=30.0,
            core_diameter_max_nm=1000.0,
            core_diameter_count=500,
            description=(
                "Core shell approximation for extracellular vesicles. "
                "The diameter axis is core diameter and the shell thickness is constant."
            ),
        ),
        POLYSTYRENE_BEADS_PRESET_NAME: ScatteringTargetModelPreset(
            name=POLYSTYRENE_BEADS_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.59,
            particle_diameter_min_nm=50.0,
            particle_diameter_max_nm=2000.0,
            particle_diameter_count=500,
            core_refractive_index=1.59,
            shell_refractive_index=1.59,
            shell_thickness_nm=5.0,
            core_diameter_min_nm=50.0,
            core_diameter_max_nm=2000.0,
            core_diameter_count=500,
            description=(
                "Solid sphere model for polystyrene calibration beads in aqueous medium. "
                "Uses n=1.59 (polystyrene at 488 nm) and n=1.333 (water)."
            ),
        ),
        SILICA_BEADS_PRESET_NAME: ScatteringTargetModelPreset(
            name=SILICA_BEADS_PRESET_NAME,
            mie_model="Solid Sphere",
            medium_refractive_index=1.333,
            particle_refractive_index=1.43,
            particle_diameter_min_nm=50.0,
            particle_diameter_max_nm=2000.0,
            particle_diameter_count=500,
            core_refractive_index=1.43,
            shell_refractive_index=1.43,
            shell_thickness_nm=5.0,
            core_diameter_min_nm=50.0,
            core_diameter_max_nm=2000.0,
            core_diameter_count=500,
            description=(
                "Solid sphere model for amorphous silica calibration beads in aqueous medium. "
                "Uses n=1.43 (fused silica at 488 nm) and n=1.333 (water)."
            ),
        ),
    }


def build_scattering_target_model_preset_options(
    *,
    include_empty_option: bool = False,
    empty_label: str = "Select",
) -> list[dict[str, str]]:
    """
    Build Dash dropdown options for target model presets.
    """
    presets = build_scattering_target_model_presets()

    options = [
        {
            "label": preset.name,
            "value": preset.name,
        }
        for preset in presets.values()
    ]

    if include_empty_option:
        return [
            {
                "label": empty_label,
                "value": "",
            },
            *options,
        ]

    return options


def get_scattering_target_model_preset(
    preset_name: Any,
) -> ScatteringTargetModelPreset:
    """
    Resolve a preset by name.

    Unknown names fall back to the Custom preset.
    """
    presets = build_scattering_target_model_presets()

    preset_name_string = str(
        preset_name or CUSTOM_PRESET_NAME,
    ).strip()

    return presets.get(
        preset_name_string,
        presets[CUSTOM_PRESET_NAME],
    )