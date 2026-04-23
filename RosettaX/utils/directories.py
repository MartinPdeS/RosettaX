#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import logging
import os
import platform
import subprocess

import RosettaX

logger = logging.getLogger(__name__)




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


def open_directory(path: Path) -> None:
    resolved_path = Path(path).resolve()

    logger.debug("Opening directory at path=%r", str(resolved_path))

    if not resolved_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {resolved_path}")

    system_name = platform.system()

    if system_name == "Darwin":
        subprocess.run(["open", str(resolved_path)], check=True)
        return

    if system_name == "Windows":
        os.startfile(str(resolved_path))
        return

    if system_name == "Linux":
        subprocess.run(["xdg-open", str(resolved_path)], check=True)
        return

    raise RuntimeError(f"Unsupported operating system: {system_name}")