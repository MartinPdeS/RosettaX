# -*- coding: utf-8 -*-

from typing import Any


MIE_MODEL_OPTIONS: list[dict[str, str]] = [
    {"label": "Solid Sphere", "value": "Solid Sphere"},
    {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
]


MEDIUM_REFRACTIVE_INDEX_PRESETS: list[dict[str, Any]] = [
    {"label": "Water", "value": "water"},
    {"label": "PBS", "value": "pbs"},
]


PARTICLE_REFRACTIVE_INDEX_PRESETS: list[dict[str, Any]] = [
    {"label": "Polystyrene", "value": "polystyrene"},
    {"label": "Silica", "value": "silica"},
    {"label": "PMMA", "value": "pmma"},
    {"label": "Lipid", "value": "lipid"},
]


CORE_REFRACTIVE_INDEX_PRESETS: list[dict[str, Any]] = [
    {"label": "Soybean oil", "value": "soybean_oil"},
    {"label": "Polystyrene", "value": "polystyrene"},
    {"label": "Silica", "value": "silica"},
]


SHELL_REFRACTIVE_INDEX_PRESETS: list[dict[str, Any]] = [
    {"label": "Phospholipid", "value": "phospholipid"},
    {"label": "Waterlike", "value": "waterlike"},
]


OPTICAL_CONFIGURATION_PRESETS: dict[str, dict[str, Any]] = {
    "default_small_particle_setup": {
        "label": "Default small particle setup",
        "wavelength_nm": 700.0,
        "detector_numerical_aperture": 0.2,
        "detector_cache_numerical_aperture": 0.0,
        "detector_sampling": 600,
    },
    "higher_na_collection": {
        "label": "Higher NA collection",
        "wavelength_nm": 700.0,
        "detector_numerical_aperture": 0.4,
        "detector_cache_numerical_aperture": 0.1,
        "detector_sampling": 600,
    },
    "low_sampling_preview": {
        "label": "Low sampling preview",
        "wavelength_nm": 700.0,
        "detector_numerical_aperture": 0.2,
        "detector_cache_numerical_aperture": 0.1,
        "detector_sampling": 200,
    },
}


OPTICAL_CONFIGURATION_PRESET_OPTIONS: list[dict[str, str]] = [
    {
        "label": preset_payload["label"],
        "value": preset_name,
    }
    for preset_name, preset_payload in OPTICAL_CONFIGURATION_PRESETS.items()
]