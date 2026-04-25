# -*- coding: utf-8 -*-

from typing import Any, Protocol


class SaveAdapter(Protocol):
    """
    Protocol implemented by page specific save adapters.
    """

    def get_calibration_payload(
        self,
        *,
        page: Any,
        calibration_store_payload: Any,
        page_state_payload: Any,
    ) -> dict | None:
        """
        Return the calibration payload to save.
        """


class CalibrationStoreSaveAdapter:
    """
    Adapter for pages that keep the calibration payload directly in a
    calibration dcc.Store.
    """

    def get_calibration_payload(
        self,
        *,
        page: Any,
        calibration_store_payload: Any,
        page_state_payload: Any,
    ) -> dict | None:
        """
        Return the calibration payload from the calibration store payload.
        """
        del page
        del page_state_payload

        if isinstance(calibration_store_payload, dict):
            return calibration_store_payload

        return None


class PageStateSaveAdapter:
    """
    Adapter for pages that keep the calibration payload inside the page state.
    """

    def __init__(
        self,
        *,
        state_class: Any,
        calibration_payload_attribute: str = "calibration_payload",
    ) -> None:
        self.state_class = state_class
        self.calibration_payload_attribute = calibration_payload_attribute

    def get_calibration_payload(
        self,
        *,
        page: Any,
        calibration_store_payload: Any,
        page_state_payload: Any,
    ) -> dict | None:
        """
        Return the calibration payload from the page state payload.
        """
        del page
        del calibration_store_payload

        page_state = self.state_class.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

        calibration_payload = getattr(
            page_state,
            self.calibration_payload_attribute,
            None,
        )

        if isinstance(calibration_payload, dict):
            return calibration_payload

        return None