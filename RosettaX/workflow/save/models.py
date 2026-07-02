# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

import dash


@dataclass(frozen=True)
class SaveConfig:
    """
    Static configuration for one reusable calibration save section.
    """

    calibration_kind: str
    header_title: str = "5. Save calibration"
    button_text: str = "Save calibration"
    file_name_placeholder: str = "file name"
    output_channel_name_label: str = "Applied output channel name"
    output_channel_name_placeholder: str = "e.g. FITC (MESF)"
    require_output_channel_name: bool = False
    saved_message_prefix: str = "Prepared calibration download"
    failure_message: str = "Failed to prepare calibration download. See terminal logs for details."


@dataclass(frozen=True)
class SaveInputs:
    """
    Validated save inputs.
    """

    file_name: str
    output_channel_name: str
    calibration_payload: dict[str, Any]


@dataclass(frozen=True)
class SaveResult:
    """
    Callback result for the reusable save workflow.

    Output order
    ------------
    1. save_out
    2. download_data
    """

    save_out: Any = dash.no_update
    download_data: Any = dash.no_update

    def to_tuple(self) -> tuple[Any, Any]:
        """
        Return outputs as a tuple in Dash callback output order.

        Order
        -----
        1. save_out
        2. download_data

        Returns
        -------
        tuple[Any, Any]
            Two-element tuple matching the Dash callback output order.
        """
        return (
            self.save_out,
            self.download_data,
        )
