# -*- coding: utf-8 -*-

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from RosettaX.workflow.file_selection.models import UploadedFileBatch
from RosettaX.workflow.page_session import FeedbackState


@dataclass(frozen=True)
class UploadConfig:
    """
    Static configuration for one reusable FCS upload section.
    """

    card_title: str
    upload_link_text: str
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
        """
        Return outputs as a tuple in Dash callback output order.

        Order
        -----
        1. page_state_payload
        2. runtime_config_data

        Returns
        -------
        tuple[Any, Any]
            Two-element tuple matching the Dash callback output order.
        """
        return (
            self.page_state_payload,
            self.runtime_config_data,
        )


@dataclass(frozen=True)
class FCSBatchOperationResult:
    """The standardized outcome of persisting and checking an FCS upload batch."""

    batch: UploadedFileBatch | None
    feedback: FeedbackState
    consistency_report: dict[str, Any]

    @property
    def is_compatible(self) -> bool:
        """Return whether this result contains a compatible batch."""
        return self.batch is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the operation result for a Dash store or page callback."""
        return {
            "batch": self.batch.to_dict() if self.batch is not None else None,
            "feedback": self.feedback.to_dict(),
            "consistency_report": deepcopy(self.consistency_report),
        }
