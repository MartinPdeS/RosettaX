
import dash_bootstrap_components as dbc
import logging
from . import callbacks, layout
from RosettaX.ui import WorkflowStep
from RosettaX.workflow.upload.adapters import FluorescenceUploadAdapter
from RosettaX.workflow.upload.layout import UploadLayout
from RosettaX.workflow.upload.models import UploadConfig
from typing import Any

logger = logging.getLogger(__name__)


class Upload:
    """
    Fluorescence FCS upload section.

    Responsibilities
    ----------------
    - Provide the fluorescence FCS upload card.
    - Register the reusable upload workflow callbacks.

    Notes
    -----
    The page level explanation is handled by ``s00_header.Header``.
    Upload persistence, runtime config synchronization, filename display, and
    page state reset behavior are delegated to ``RosettaX.workflow.upload``.
    """

    workflow_step = WorkflowStep(
        title="Upload bead FCS file",
        description=(
            "Load the FCS file of fluorescent reference beads. This FCS file becomes "
            "the source for parameter selection and detection of fluorescence peaks."
        ),
        hover_description=(
            "Upload an FCS file measured from fluorescence calibration beads with known "
            "MESF values. RosettaX uses the bead peak positions and the known MESF "
            "references to build the fluorescence calibration."
        ),
    )

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str,
    ) -> None:
        self.page = page
        self.ids = page.ids.Upload
        self.section_number = section_number
        self.card_color = card_color

        self.upload_tooltip_target_id = f"{self.ids.upload}-calibration-file-info-target"
        self.upload_tooltip_id = f"{self.ids.upload}-calibration-file-info-tooltip"

        self.config = UploadConfig(
            card_title=layout.build_card_title(self),
            upload_link_text="Select bead FCS file",
            initial_runtime_config_path="files.fluorescence_fcs_file_path",
            runtime_config_output_path="files.fluorescence_fcs_file_path",
            accepted_file_extensions=".fcs",
            runtime_config_store_id="runtime-config-store",
            body_style_key="body_scroll",
        )

        self.adapter = FluorescenceUploadAdapter()

        self.layout_builder = UploadLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Fluorescence Upload section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the upload section layout.
        """
        return layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Register callbacks for the fluorescence upload section.
        """
        callbacks.register_callbacks(self)
