# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class UploadIds:
    """
    Shared ID factory for reusable upload sections.

    The generated IDs are page specific through the prefix, while the Python API
    remains identical for fluorescence and scattering upload sections.
    """

    prefix: str

    @property
    def uploaded_fcs_path_store(self) -> str:
        return f"{self.prefix}-uploaded_fcs_path_store"

    @property
    def uploaded_fcs_filename_store(self) -> str:
        return f"{self.prefix}-uploaded_fcs_filename_store"

    @property
    def upload(self) -> str:
        return f"{self.prefix}-upload"

    @property
    def upload_filename(self) -> str:
        return f"{self.prefix}-upload_filename"

    @property
    def max_events_for_plots_input(self) -> str:
        return f"{self.prefix}-max-events-for-plots-input"

    @property
    def fcs_path_store(self) -> str:
        """
        Backward compatible alias.
        """
        return self.uploaded_fcs_path_store

    @property
    def filename_store(self) -> str:
        """
        Backward compatible alias.
        """
        return self.uploaded_fcs_filename_store

    @property
    def filename(self) -> str:
        """
        Backward compatible alias.
        """
        return self.upload_filename