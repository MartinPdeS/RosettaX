# -*- coding: utf-8 -*-

"""Compatibility shim for shared scattering model helpers."""

from RosettaX.scattering.model import BROAD_PARTICLE_STANDARD_PRESET_NAME
from RosettaX.scattering.model import CUSTOM_SCATTERER_PRESET_NAME
from RosettaX.scattering.model import ROSETTA_MIX_PRESET_NAME
from RosettaX.scattering.model import SMALL_PARTICLE_STANDARD_PRESET_NAME
from RosettaX.scattering.model import ScatteringCalibrationScattererPreset
from RosettaX.scattering.model import ScatteringModelConfiguration
from RosettaX.scattering.model import ScatteringModelDefaults
from RosettaX.scattering.model import build_scattering_calibration_scatterer_preset_options
from RosettaX.scattering.model import build_scattering_calibration_scatterer_presets
from RosettaX.scattering.model import get_scattering_calibration_scatterer_preset


__all__ = [
    "BROAD_PARTICLE_STANDARD_PRESET_NAME",
    "CUSTOM_SCATTERER_PRESET_NAME",
    "ROSETTA_MIX_PRESET_NAME",
    "SMALL_PARTICLE_STANDARD_PRESET_NAME",
    "ScatteringCalibrationScattererPreset",
    "ScatteringModelConfiguration",
    "ScatteringModelDefaults",
    "build_scattering_calibration_scatterer_preset_options",
    "build_scattering_calibration_scatterer_presets",
    "get_scattering_calibration_scatterer_preset",
]
