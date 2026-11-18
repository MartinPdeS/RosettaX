
import dash_bootstrap_components as dbc
import logging
from . import callbacks as _callbacks
from . import layout as _layout
from RosettaX.ui import WorkflowStep
from typing import Any

logger = logging.getLogger(__name__)


class Header:
    """
    Fluorescence calibration page header.

    Responsibilities
    ----------------
    - Explain the purpose of the fluorescence calibration page.
    - Show the calibration workflow before the user starts.
    - Clarify what each step produces.
    - Keep explanatory UX content separate from upload and processing logic.
    """

    def __init__(
        self,
        page: Any,
        card_color: str,
        *,
        workflow_steps: list[WorkflowStep] | None = None,
    ) -> None:
        self.page = page
        self.card_color = card_color
        if workflow_steps is None:
            from ..services import SECTION_TYPES

            workflow_steps = [section_type.workflow_step for section_type in SECTION_TYPES]
        self.workflow_header = _layout.build_workflow(workflow_steps=workflow_steps)

        logger.debug(
            "Initialized Fluorescence Header section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence calibration header layout.
        """
        return _layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Header section has no callbacks.
        """
        return _callbacks.register_callbacks(self)
