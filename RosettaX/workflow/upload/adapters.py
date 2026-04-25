# -*- coding: utf-8 -*-

from typing import Any, Protocol

from RosettaX.pages.fluorescence.state import FluorescencePageState
from RosettaX.pages.fluorescence.state import build_empty_peak_lines_payload


class UploadAdapter(Protocol):
    """
    Protocol implemented by page specific upload adapters.
    """

    def page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> Any:
        """
        Build a page state object from a Dash store payload.
        """

    def get_uploaded_fcs_path(
        self,
        page_state: Any,
    ) -> str | None:
        """
        Return the current uploaded FCS path.
        """

    def get_uploaded_filename(
        self,
        page_state: Any,
    ) -> str | None:
        """
        Return the current uploaded filename.
        """

    def update_page_state_after_upload(
        self,
        *,
        current_page_state: Any,
        uploaded_fcs_path: str | None,
        uploaded_filename: str | None,
    ) -> Any:
        """
        Return the updated page state after upload.
        """


class FluorescenceUploadAdapter:
    """
    Adapter between the reusable upload workflow and FluorescencePageState.
    """

    def page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> FluorescencePageState:
        """
        Build FluorescencePageState from a Dash store payload.
        """
        return FluorescencePageState.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

    def get_uploaded_fcs_path(
        self,
        page_state: FluorescencePageState,
    ) -> str | None:
        """
        Return the current uploaded FCS path.
        """
        return page_state.uploaded_fcs_path

    def get_uploaded_filename(
        self,
        page_state: FluorescencePageState,
    ) -> str | None:
        """
        Return the current uploaded filename.
        """
        return page_state.uploaded_filename

    def update_page_state_after_upload(
        self,
        *,
        current_page_state: FluorescencePageState,
        uploaded_fcs_path: str | None,
        uploaded_filename: str | None,
    ) -> FluorescencePageState:
        """
        Update fluorescence page state after a new upload.
        """
        return current_page_state.update(
            uploaded_fcs_path=uploaded_fcs_path,
            uploaded_filename=uploaded_filename,
            peak_lines_payload=build_empty_peak_lines_payload(),
            fluorescence_peak_lines=[],
            fluorescence_histogram_payload=None,
            fluorescence_source_channel=None,
            status_message="",
        )


class ScatteringUploadAdapter:
    """
    Generic adapter for a scattering page state class.

    This adapter only updates fields that actually exist on the page state.
    """

    def __init__(
        self,
        *,
        state_class: Any,
        empty_peak_lines_payload_builder: Any = None,
    ) -> None:
        self.state_class = state_class
        self.empty_peak_lines_payload_builder = empty_peak_lines_payload_builder

    def page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> Any:
        """
        Build the scattering page state from a Dash store payload.
        """
        return self.state_class.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

    def get_uploaded_fcs_path(
        self,
        page_state: Any,
    ) -> str | None:
        """
        Return the current uploaded FCS path.
        """
        return page_state.uploaded_fcs_path

    def get_uploaded_filename(
        self,
        page_state: Any,
    ) -> str | None:
        """
        Return the current uploaded filename.
        """
        return page_state.uploaded_filename

    def update_page_state_after_upload(
        self,
        *,
        current_page_state: Any,
        uploaded_fcs_path: str | None,
        uploaded_filename: str | None,
    ) -> Any:
        """
        Update scattering page state after a new upload.
        """
        requested_updates = {
            "uploaded_fcs_path": uploaded_fcs_path,
            "uploaded_filename": uploaded_filename,
            "status_message": "",
        }

        if self.empty_peak_lines_payload_builder is not None:
            requested_updates["peak_lines_payload"] = self.empty_peak_lines_payload_builder()

        existing_fields = set(
            current_page_state.to_dict().keys()
        )

        safe_updates = {
            key: value
            for key, value in requested_updates.items()
            if key in existing_fields
        }

        return current_page_state.update(
            **safe_updates,
        )