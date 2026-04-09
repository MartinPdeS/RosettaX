#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import RosettaX

root = Path(RosettaX.__path__[0])

project = root.parents[0]

documentation = root.parents[0].joinpath("docs")

logo = documentation.joinpath("images/logo.png")

css = documentation.joinpath("source/_static/default.css")

data = root / "data"

fcs_data = data / "fcs"

calibration_data = data / "calibration"
