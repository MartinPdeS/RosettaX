# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash

from RosettaX.peak_workflow.core import detectors


logger = logging.getLogger(__name__)


def register_detector_dropdown_callbacks(
    *,
    ids: Any,
    adapter: Any,
    page_state_store_id: str,
) -> None:
    """
    Register detector dropdown callbacks for the peak workflow.

    Parameters
    ----------
    ids
        Peak section ID factory.
    adapter
        Page specific peak workflow adapter.
    page_state_store_id
        Dash store ID containing the page state.
    """

    @dash.callback(
        dash.Output(
            ids.process_detector_dropdown_pattern(),
            "options",
        ),
        dash.Output(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.Input(page_state_store_id, "data"),
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        prevent_initial_call=False,
    )
    def populate_detector_dropdowns(
        page_state_payload: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        current_detector_values: list[Any],
    ) -> tuple[list[list[dict[str, Any]]], list[Any]]:
        page_state = adapter.get_page_state_from_payload(
            page_state_payload,
        )

        uploaded_fcs_path = adapter.get_uploaded_fcs_path(
            page_state=page_state,
        )

        return detectors.populate_peak_script_detector_dropdowns(
            uploaded_fcs_path=uploaded_fcs_path,
            detector_dropdown_ids=detector_dropdown_ids,
            current_detector_values=current_detector_values,
            logger=logger,
        )