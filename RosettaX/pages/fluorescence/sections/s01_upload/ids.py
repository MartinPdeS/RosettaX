# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class UploadSectionIds:
    """
    ID factory for the fluorescence upload section.
    """

    prefix: str

    @property
    def uploaded_fcs_path_store(self) -> str:
        return f"{self.prefix}-uploaded_fcs_path_store"

    @property
    def uploaded_fcs_filename_store(self) -> str:
        return f"{self.uploaded_fcs_path_store}-filename"

    @property
    def upload(self) -> str:
        return f"{self.prefix}-upload"

    @property
    def upload_filename(self) -> str:
        return f"{self.prefix}-upload_filename"

    @property
    def upload_saved_as(self) -> str:
        return f"{self.prefix}-upload_saved_as"

    @property
    def max_events_for_plots_input(self) -> str:
        return f"{self.prefix}-max-events-for-plots-input"