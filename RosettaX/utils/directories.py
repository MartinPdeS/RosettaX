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

profiles = root / "profiles"

default_profile = profiles / "default_profile.json"

calibration_directory = root / "calibrations"

fluorescence_calibration = calibration_directory / "fluorescence"

scattering_calibration = calibration_directory / "scattering"

asset_directory = root / "assets"


def list_profiles() -> list[str]:
    """
    Gets list of saved profiles from the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function returns a list of filenames.

    Returns
    -------
    list[str]
        List of profile filenames without the .json extension.
    """
    list_of_filenames = []
    for file in profiles.iterdir():
        if file.is_file() and file.suffix == ".json":
            list_of_filenames.append(file.name.replace(".json", ""))
    return list_of_filenames

def list_calibrations(calibration_type: str) -> list[str]:
    """
    Gets list of saved calibration files from the calibration directory. Each calibration file is a json file that contains the details of a fluorescence or scattering calibration. This function returns a list of filenames.

    Parameters
    ----------
    calibration_type : str
        The type of calibration to list. Must be either "fluorescence" or "scattering".

    Returns
    -------
    list[str]
        List of calibration filenames without the .json extension.
    """
    if calibration_type == "fluorescence":
        directory = fluorescence_calibration
    elif calibration_type == "scattering":
        directory = scattering_calibration
    else:
        raise ValueError(f"Invalid calibration type: {calibration_type}")

    list_of_filenames = []
    for file in directory.iterdir():
        if file.is_file() and file.suffix == ".json":
            list_of_filenames.append(file.name)
    return list_of_filenames

