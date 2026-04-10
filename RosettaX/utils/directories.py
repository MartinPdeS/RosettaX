#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import RosettaX

root = Path(RosettaX.__path__[0])

project = root.parents[0]

documentation = root.parents[0].joinpath("docs")

logo = documentation.joinpath("images/logo.png")

css = documentation.joinpath("source/_static/default.css")

fcs_data = root / "fcs"

profile_directory = root / "profiles"

default_profile_location = profile_directory / "default_profile.json"

calibration_directory = root / "calibrations"

fluorescence_calibration_directory = calibration_directory / "fluorescence"

scattering_calibration_directory = calibration_directory / "scattering"

asset_directory = root / "assets"


