# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional

from RosettaX.workflow.parameters.refractive_index import (
    resolve_refractive_index_source_value,
)


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

    medium_refractive_index_source: Optional[str] = None
    particle_refractive_index_source: Optional[str] = None
    core_refractive_index_source: Optional[str] = None
    shell_refractive_index_source: Optional[str] = None
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
            medium_refractive_index_source="water",
            particle_refractive_index=1.59,
            particle_refractive_index_source="polystyrene",
            particle_diameter_min_nm=50.0,
            particle_diameter_max_nm=2000.0,
            particle_diameter_count=500,
            core_refractive_index=1.59,
            core_refractive_index_source="polystyrene",
            shell_refractive_index=1.59,
            shell_refractive_index_source="polystyrene",
            shell_thickness_nm=5.0,
            core_diameter_min_nm=50.0,
            core_diameter_max_nm=2000.0,
            core_diameter_count=500,
            description=(
                "Solid sphere model for polystyrene calibration beads in aqueous medium. "
                "Uses wavelength-resolved Sellmeier values for polystyrene and water."
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


def resolve_scattering_target_model_preset(
    preset_name: Any,
    *,
    wavelength_nm: Any = None,
) -> ScatteringTargetModelPreset:
    """
    Resolve one target model preset, optionally applying refractive-index sources
    at the provided wavelength.
    """
    preset = get_scattering_target_model_preset(
        preset_name,
    )

    if wavelength_nm in (None, ""):
        return preset

    return ScatteringTargetModelPreset(
        name=preset.name,
        mie_model=preset.mie_model,
        medium_refractive_index=resolve_refractive_index_source_value(
            preset.medium_refractive_index_source,
            wavelength_nm=wavelength_nm,
            fallback_value=preset.medium_refractive_index,
        ),
        medium_refractive_index_source=preset.medium_refractive_index_source,
        particle_refractive_index=resolve_refractive_index_source_value(
            preset.particle_refractive_index_source,
            wavelength_nm=wavelength_nm,
            fallback_value=preset.particle_refractive_index,
        ),
        particle_refractive_index_source=preset.particle_refractive_index_source,
        particle_diameter_min_nm=preset.particle_diameter_min_nm,
        particle_diameter_max_nm=preset.particle_diameter_max_nm,
        particle_diameter_count=preset.particle_diameter_count,
        core_refractive_index=resolve_refractive_index_source_value(
            preset.core_refractive_index_source,
            wavelength_nm=wavelength_nm,
            fallback_value=preset.core_refractive_index,
        ),
        core_refractive_index_source=preset.core_refractive_index_source,
        shell_refractive_index=resolve_refractive_index_source_value(
            preset.shell_refractive_index_source,
            wavelength_nm=wavelength_nm,
            fallback_value=preset.shell_refractive_index,
        ),
        shell_refractive_index_source=preset.shell_refractive_index_source,
        shell_thickness_nm=preset.shell_thickness_nm,
        core_diameter_min_nm=preset.core_diameter_min_nm,
        core_diameter_max_nm=preset.core_diameter_max_nm,
        core_diameter_count=preset.core_diameter_count,
        description=preset.description,
    )
