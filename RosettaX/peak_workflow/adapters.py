# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash

from RosettaX.peak_workflow.state import build_empty_peak_lines_payload


logger = logging.getLogger(__name__)


class PeakWorkflowAdapter:
    """
    Base adapter for page specific peak workflow integration.

    Subclasses connect the shared peak workflow to a specific page state and
    calibration table schema.

    The shared callback layer owns orchestration. The adapter owns page specific
    state extraction and table writing.
    """

    page_kind: str = ""

    def get_page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> Any:
        """
        Parse the page state from Dash store data.
        """
        raise NotImplementedError

    def get_uploaded_fcs_path(
        self,
        *,
        page_state: Any,
    ) -> Optional[str]:
        """
        Return the uploaded FCS path from the page state.
        """
        raise NotImplementedError

    def get_peak_lines_payload(
        self,
        *,
        page_state: Any,
    ) -> dict[str, Any]:
        """
        Return the peak line payload from the page state.
        """
        raise NotImplementedError

    def update_peak_lines_payload(
        self,
        *,
        page_state: Any,
        peak_lines_payload: Any,
    ) -> Any:
        """
        Return an updated page state with a new peak line payload.
        """
        raise NotImplementedError

    def clear_peak_lines_payload(
        self,
        *,
        page_state: Any,
    ) -> Any:
        """
        Return an updated page state with an empty peak line payload.
        """
        return self.update_peak_lines_payload(
            page_state=page_state,
            peak_lines_payload=build_empty_peak_lines_payload(),
        )

    def get_backend(
        self,
        *,
        page: Any,
        uploaded_fcs_path: Any,
    ) -> Any:
        """
        Return the backend used for graphing and peak actions.

        Pages can override this to return an adapter backend.
        """
        del uploaded_fcs_path

        return getattr(
            page,
            "backend",
            None,
        )

    def apply_peak_process_result_to_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        result: Any,
        context: dict[str, Any],
        logger: logging.Logger,
    ) -> Optional[list[dict[str, Any]]]:
        """
        Apply a peak process result to the page calibration table.

        Subclasses must implement this because scattering and fluorescence use
        different table schemas.
        """
        raise NotImplementedError

    def build_no_table_update_result(self) -> Any:
        """
        Return Dash no update for table data.
        """
        return dash.no_update