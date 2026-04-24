# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class SaveSectionIds:
    """
    ID factory for the scattering save section.
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