# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.upload import services
from RosettaX.workflow.upload.models import UploadConfig


logger = logging.getLogger(__name__)


class UploadLayout:
    """
    Reusable layout builder for FCS upload sections.
    """

    def __init__(
        self,
        *,
        ids: Any,
        config: UploadConfig,
    ) -> None:
        self.ids = ids
        self.config = config

    def get_layout(self) -> html.Div:
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

        return html.Div(
            [
                self._build_hero_section(),
                html.Div(
                    style={
                        "height": "16px",
                    },
                ),
                self._build_upload_card(
                    initial_filename=initial_filename,
                ),
            ]
        )

    def _build_hero_section(self) -> dbc.Card:
        """
        Build the upload hero section.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title=self.config.section_title,
                        title_component="H2",
                        title_style_overrides={
                            "fontSize": "2rem",
                            "fontWeight": "600",
                            "lineHeight": "1.2",
                            "marginBottom": "8px",
                        },
                        description=self.config.description,
                        description_opacity=0.9,
                        description_margin_bottom_px=0,
                        description_style_overrides={
                            "fontSize": "1.02rem",
                            "maxWidth": "980px",
                            "marginBottom": "0px",
                        },
                    ),
                ]
            )
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
                                    "Drag and Drop or ",
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