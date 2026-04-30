# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReferenceTableConfig:
    """
    Static configuration for one reusable reference table section.
    """

    card_title: Any
    description: Optional[Any]
    table_title: Optional[str] = None
    add_row_button_label: str = "Add row"
    add_row_button_color: str = "secondary"
    add_row_button_outline: bool = True
    body_style_key: str = "body_scroll"
    show_table_title: bool = False


@dataclass(frozen=True)
class ReferenceTableActionConfig:
    """
    Optional action block displayed below the reference table.
    """

    button_id: Any
    button_label: str
    description: Optional[Any]
    button_color: str = "primary"
    button_style: Optional[dict[str, Any]] = None


class ReferenceTableLayout:
    """
    Reusable layout builder for calibration reference table sections.

    Responsibilities
    ----------------
    - Render the section card.
    - Render the card header.
    - Render the table description.
    - Render the Dash DataTable.
    - Render the add row button.
    - Optionally render an action block below the table.
    """

    def __init__(
        self,
        *,
        ids: Any,
        config: ReferenceTableConfig,
        table_columns: list[dict[str, Any]],
        table_data: list[dict[str, Any]],
        action_config: Optional[ReferenceTableActionConfig] = None,
    ) -> None:
        self.ids = ids
        self.config = config
        self.table_columns = table_columns
        self.table_data = table_data
        self.action_config = action_config

    def get_layout(self) -> dbc.Card:
        """
        Build the complete reference table section layout.
        """
        logger.debug(
            "Building ReferenceTableLayout with card_title=%r row_count=%r column_count=%r",
            self.config.card_title,
            len(self.table_data),
            len(self.table_columns),
        )

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return dbc.CardHeader(
            self.config.card_title,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        children: list[Any] = [
            self._build_reference_table_block(),
        ]

        if self.action_config is not None:
            children.extend(
                [
                    dash.html.Div(
                        style={
                            "height": "12px",
                        },
                    ),
                    self._build_action_block(),
                ]
            )

        return dbc.CardBody(
            children,
            style=self._get_body_style(),
        )

    def _build_reference_table_block(self) -> dash.html.Div:
        """
        Build the table block.
        """
        children: list[Any] = []

        if self.config.show_table_title and self.config.table_title:
            children.append(
                dash.html.H5(
                    self.config.table_title,
                )
            )

        if self.config.description is not None:
            children.append(
                dash.html.Div(
                    self.config.description,
                    style={
                        "marginBottom": "10px",
                        "opacity": 0.8,
                    },
                )
            )

        children.extend(
            [
                dash.dash_table.DataTable(
                    id=self.ids.bead_table,
                    columns=self.table_columns,
                    data=self.table_data,
                    **self._build_table_options(),
                ),
                self._build_add_row_button_row(),
            ]
        )

        return dash.html.Div(
            children,
        )

    def _build_add_row_button_row(self) -> dash.html.Div:
        """
        Build the add row button row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    self.config.add_row_button_label,
                    id=self.ids.add_row_btn,
                    n_clicks=0,
                    color=self.config.add_row_button_color,
                    outline=self.config.add_row_button_outline,
                    size="sm",
                )
            ],
            style={
                "marginTop": "10px",
                "display": "flex",
                "gap": "8px",
                "alignItems": "center",
            },
        )

    def _build_action_block(self) -> dash.html.Div:
        """
        Build the optional action block.
        """
        if self.action_config is None:
            raise RuntimeError("Cannot build action block without action_config.")

        button_style = (
            self.action_config.button_style
            if isinstance(self.action_config.button_style, dict)
            else {
                "marginTop": "12px",
            }
        )

        children: list[Any] = [
            dbc.Button(
                self.action_config.button_label,
                id=self.action_config.button_id,
                n_clicks=0,
                color=self.action_config.button_color,
                style=button_style,
            ),
        ]

        if self.action_config.description is not None:
            info_target_id = f"{self.action_config.button_id}-info-target"
            info_tooltip_id = f"{self.action_config.button_id}-info-tooltip"

            children.extend(
                [
                    self._build_info_badge(
                        info_target_id,
                    ),
                    dbc.Tooltip(
                        self.action_config.description,
                        id=info_tooltip_id,
                        target=info_target_id,
                        placement="right",
                    ),
                ]
            )

        return dash.html.Div(
            children,
            style={
                "display": "flex",
                "alignItems": "center",
            },
        )

    def _build_info_badge(
        self,
        tooltip_target_id: str,
    ) -> dash.html.Span:
        """
        Build a compact reusable info badge.
        """
        return dash.html.Span(
            "i",
            id=tooltip_target_id,
            style={
                "width": "19px",
                "height": "19px",
                "borderRadius": "50%",
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "center",
                "fontSize": "0.72rem",
                "fontWeight": "800",
                "marginLeft": "8px",
                "cursor": "help",
                "opacity": 0.72,
                "border": "1px solid currentColor",
                "lineHeight": "1",
                "flex": "0 0 auto",
            },
        )

    def _build_table_options(self) -> dict[str, Any]:
        """
        Build DataTable options.
        """
        return {
            **styling.DATATABLE,
        }

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