# -*- coding: utf-8 -*-

from typing import Any


MIE_MODEL_OPTIONS: list[dict[str, str]] = [
    {"label": "Solid Sphere", "value": "Solid Sphere"},
    {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
]


MEDIUM_REFRACTIVE_INDEX_PRESETS: list[dict[str, float]] = [
    {"label": "Water 1.333", "value": 1.333},
    {"label": "PBS 1.335", "value": 1.335},
]


PARTICLE_REFRACTIVE_INDEX_PRESETS: list[dict[str, float]] = [
    {"label": "Polystyrene 1.59", "value": 1.59},
    {"label": "Silica 1.45", "value": 1.45},
    {"label": "PMMA 1.49", "value": 1.49},
    {"label": "Lipid 1.47", "value": 1.47},
]


CORE_REFRACTIVE_INDEX_PRESETS: list[dict[str, float]] = [
    {"label": "Soybean oil 1.47", "value": 1.47},
    {"label": "Polystyrene 1.59", "value": 1.59},
    {"label": "Silica 1.45", "value": 1.45},
]


SHELL_REFRACTIVE_INDEX_PRESETS: list[dict[str, float]] = [
    {"label": "Phospholipid 1.46", "value": 1.46},
    {"label": "Waterlike 1.33", "value": 1.33},
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