# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class SaveIds:
    """
    Shared ID factory for reusable save sections.

    The generated IDs are page specific through the prefix, while the Python API
    remains identical for fluorescence and scattering save sections.
    """

    prefix: str

    @property
    def collapse(self) -> str:
        return f"{self.prefix}-save-collapse"

    @property
    def save_calibration_btn(self) -> str:
        return f"{self.prefix}-save-calibration-btn"

    @property
    def file_name(self) -> str:
        return f"{self.prefix}-file-name"

    @property
    def save_out(self) -> str:
        return f"{self.prefix}-save-out"