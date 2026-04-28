# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.upload import services
from RosettaX.workflow.upload.models import UploadConfig


logger = logging.getLogger(__name__)


class UploadLayout:
    """
    Reusable layout builder for FCS upload sections.

    This component intentionally renders only the upload card. Page level
    explanation and workflow guidance should live in the page header section,
    for example ``s00_header.py``.
    """

    def __init__(
        self,
        *,
        ids: Any,
        config: UploadConfig,
    ) -> None:
        self.ids = ids
        self.config = config

    def get_layout(self) -> dbc.Card:
        """
        Build the upload section layout.
        """
        initial_fcs_path = self._get_initial_fcs_file_path()
        initial_filename = Path(initial_fcs_path).name if initial_fcs_path else ""

        logger.debug(
            "Building upload layout with initial_fcs_path=%r initial_filename=%r",
            initial_fcs_path,
            initial_filename,
        )

        return self._build_upload_card(
            initial_filename=initial_filename,
        )

    def _build_upload_card(
        self,
        *,
        initial_filename: str,
    ) -> dbc.Card:
        """
        Build the upload card.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    self.config.card_title,
                ),
                dbc.CardBody(
                    [
                        dcc.Upload(
                            id=self.ids.upload,
                            children=html.Div(
                                [
                                    "Drag and drop or ",
                                    html.A(
                                        self.config.upload_link_text,
                                    ),
                                ]
                            ),
                            style=styling.UPLOAD,
                            multiple=False,
                            accept=self.config.accepted_file_extensions,
                        ),
                        html.Div(
                            id=self.ids.upload_filename,
                            children=services.build_loaded_filename_text(
                                initial_filename,
                            ),
                        ),
                    ],
                    style=self._get_body_style(),
                ),
            ]
        )

    def _get_body_style(self) -> dict[str, Any]:
        """
        Return the configured body style.
        """
        page_styles = getattr(
            styling,
            "PAGE",
            {},
        )

        if isinstance(page_styles, dict):
            style = page_styles.get(
                self.config.body_style_key,
            )

            if isinstance(style, dict):
                return style

        return {}

    def _get_initial_fcs_file_path(self) -> Optional[str]:
        """
        Resolve the initial FCS file path from the default runtime config.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return runtime_config.get_path(
            self.config.initial_runtime_config_path,
            default=None,
        )