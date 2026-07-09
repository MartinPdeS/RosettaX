# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from . import sections
from .ids import Ids
from .state import SettingsPageState
from RosettaX.utils import styling, ui_forms


class SettingsPage:
    """
    Settings page.

    This page owns one SettingsPageState store shared by all settings sections.
    """

    def __init__(self) -> None:
        self.ids = Ids()
        self.style = styling.PAGE

        self.sections = [
            sections.DefaultProfile(page=self),
        ]

        self.backend = None

    def register_callbacks(self) -> "SettingsPage":
        for section in self.sections:
            section.register_callbacks()

        return self

    def layout(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.dcc.Store(
                    id=self.ids.State.page_state_store,
                    storage_type="session",
                    data=SettingsPageState.empty().to_dict(),
                ),
                self._build_header_card(),
                *[
                    section.get_layout()
                    for section in self.sections
                ],
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": styling.get_spacing_token("md"),
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Settings",
                        title_component="H2",
                        description=(
                            "Configure reusable defaults for fluorescence, scattering, "
                            "apply-calibration, and visualization behavior. Save everything as "
                            "browser profiles for rapid workflow switching."
                        ),
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                self._build_step_card(
                                    number=step["number"],
                                    title=step["title"],
                                    description=step["description"],
                                    color_name=step["color_name"],
                                ),
                                xs=12,
                                md=6,
                                lg=4,
                                style={
                                    "marginBottom": "10px",
                                },
                            )
                            for step in self._build_steps()
                        ],
                        className="g-2",
                    ),
                ],
                style=ui_forms.build_workflow_section_body_style(),
            ),
            style={
                **ui_forms.build_workflow_section_card_style(
                    color_name=styling.get_workflow_page_header_color(),
                ),
                "marginBottom": "16px",
            },
        )

    def _build_steps(self) -> list[dict[str, str]]:
        return [
            {
                "number": "1",
                "title": "Edit defaults",
                "description": (
                    "Adjust startup defaults for calibration pages, chart behavior, and "
                    "runtime options in one centralized form."
                ),
                "color_name": styling.get_workflow_section_color(1),
            },
            {
                "number": "2",
                "title": "Create profile",
                "description": (
                    "Save the current defaults as a named browser profile for quick context "
                    "switching across experiments and instruments."
                ),
                "color_name": styling.get_workflow_section_color(2),
            },
            {
                "number": "3",
                "title": "Clean up profiles",
                "description": (
                    "Remove stale profiles and keep only actively used defaults to reduce "
                    "configuration drift."
                ),
                "color_name": styling.get_workflow_section_color(3),
            },
        ]

    def _build_step_card(
        self,
        *,
        number: str,
        title: str,
        description: str,
        color_name: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        number,
                        style={
                            "width": "28px",
                            "height": "28px",
                            "borderRadius": "50%",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "fontWeight": "700",
                            "fontSize": "0.9rem",
                            "backgroundColor": styling.build_rgba(
                                color_name,
                                0.12,
                            ),
                            "border": f"1px solid {styling.build_rgba(color_name, 0.35)}",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H6(
                        title,
                        style={
                            "marginBottom": "6px",
                        },
                    ),
                    html.P(
                        description,
                        style={
                            "marginBottom": "0px",
                            "fontSize": "0.86rem",
                            "opacity": 0.78,
                        },
                    ),
                ],
                style={
                    "height": "100%",
                    "padding": "14px",
                },
            ),
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=color_name,
                style_overrides={
                    "height": "100%",
                },
            ),
        )


_page = SettingsPage().register_callbacks()
layout = _page.layout


dash.register_page(
    __name__,
    path="/settings",
    name="Settings",
    order=4,
    layout=layout,
)
