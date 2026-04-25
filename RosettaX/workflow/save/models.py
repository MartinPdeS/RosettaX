# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dash


@dataclass(frozen=True)
class SaveConfig:
    """
    Static configuration for one reusable calibration save section.
    """

    calibration_kind: str
    output_directory: Path
    header_title: str = "5. Save calibration"
    button_text: str = "Save calibration"
    file_name_placeholder: str = "calibration name"
    saved_message_prefix: str = "Saved calibration"
    failure_message: str = "Failed to save calibration. See terminal logs for details."


@dataclass(frozen=True)
class SaveInputs:
    """
    Validated save inputs.
    """

    file_name: str
    calibration_payload: dict[str, Any]


@dataclass(frozen=True)
class SaveResult:
    """
    Callback result for the reusable save workflow.

    Output order
    ------------
    1. save_out
    2. sidebar_refresh_signal
    """

    save_out: Any = dash.no_update
    sidebar_refresh_signal: Any = dash.no_update

    def to_tuple(self) -> tuple[Any, Any]:
        return (
            self.save_out,
            self.sidebar_refresh_signal,
        )