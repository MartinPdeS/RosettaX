# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class UploadConfig:
    """
    Static configuration for one reusable FCS upload section.
    """

    section_title: str
    card_title: str
    upload_link_text: str
    description: str
    initial_runtime_config_path: str
    runtime_config_output_path: str
    accepted_file_extensions: str = ".fcs"
    runtime_config_store_id: str = "runtime-config-store"
    upload_directory: Optional[Path] = None
    body_style_key: str = "body_scroll"


@dataclass(frozen=True)
class UploadState:
    """
    Result of resolving one upload action.
    """

    uploaded_fcs_path: Optional[str]
    uploaded_filename: Optional[str]
    runtime_config_data: dict[str, Any]


@dataclass(frozen=True)
class UploadCallbackResult:
    """
    Dash callback result for the reusable upload callback.

    Output order
    ------------
    1. page_state_payload
    2. runtime_config_data
    """

    page_state_payload: Any
    runtime_config_data: Any

    def to_tuple(self) -> tuple[Any, Any]:
        return (
            self.page_state_payload,
            self.runtime_config_data,
        )