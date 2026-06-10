# -*- coding: utf-8 -*-

from .configuration import (
    CUSTOM_DETECTOR_PRESET_NAME,
    build_detector_preset_options,
    detect_detector_preset_from_uploaded_fcs,
    detect_wavelength_nm_from_detector_channel,
    resolve_detector_preset_wavelength_nm,
    resolve_runtime_detector_preset,
    resolve_detector_angular_weights,
    resolve_detector_configuration_values,
    resolve_detector_configuration_visibility_style,
    resolve_detector_modeling_geometry_values,
)
from .loader import (
    DEFAULT_DETECTOR_PRESET_PATH,
    DEFAULT_DETECTOR_PRESET_DIRECTORY,
    DetectorPresetLoader,
    get_default_detector_preset_loader,
    load_detector_configuration_brand_options,
    load_detector_configuration_model_options,
    load_detector_configuration_preset,
    load_detector_configuration_preset_catalog,
    load_detector_configuration_preset_options,
    load_detector_configuration_presets,
    resolve_detector_configuration_preset_brand,
)


__all__ = [
    "CUSTOM_DETECTOR_PRESET_NAME",
    "DEFAULT_DETECTOR_PRESET_PATH",
    "DEFAULT_DETECTOR_PRESET_DIRECTORY",
    "DetectorPresetLoader",
    "build_detector_preset_options",
    "detect_detector_preset_from_uploaded_fcs",
    "detect_wavelength_nm_from_detector_channel",
    "get_default_detector_preset_loader",
    "load_detector_configuration_brand_options",
    "load_detector_configuration_model_options",
    "load_detector_configuration_preset",
    "load_detector_configuration_preset_catalog",
    "load_detector_configuration_preset_options",
    "load_detector_configuration_presets",
    "resolve_detector_configuration_preset_brand",
    "resolve_detector_preset_wavelength_nm",
    "resolve_runtime_detector_preset",
    "resolve_detector_angular_weights",
    "resolve_detector_configuration_values",
    "resolve_detector_configuration_visibility_style",
    "resolve_detector_modeling_geometry_values",
]
