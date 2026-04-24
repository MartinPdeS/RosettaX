# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class UploadSectionIds:
    """
    ID factory for the scattering upload section.
    """

    prefix: str

    @property
    def fcs_path_store(self) -> str:
        return f"{self.prefix}-uploaded_fcs_path_store"

    @property
    def filename_store(self) -> str:
        return f"{self.prefix}-filename_store"

    @property
    def upload(self) -> str:
        return f"{self.prefix}-upload"

    @property
    def filename(self) -> str:
        return f"{self.prefix}-upload_filename"

    @property
    def max_events_for_plots_input(self) -> str:
        return f"{self.prefix}-max-events-for-plots-input"