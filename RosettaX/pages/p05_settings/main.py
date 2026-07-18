# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc

from . import sections
from .ids import Ids
from .state import SettingsPageState
from RosettaX.ui import WorkflowStep, build_workflow_page_header
from RosettaX.utils import styling


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
        return build_workflow_page_header(
            title="Settings",
            description=(
                "Configure reusable defaults for fluorescence, scattering, "
                "apply-calibration, and visualization behavior. Save everything as "
                "browser profiles for rapid workflow switching."
            ),
            steps=self._build_steps(),
        )

    def _build_steps(self) -> list[WorkflowStep]:
        return [
            WorkflowStep(
                number="1",
                title="Edit defaults",
                description=(
                    "Adjust startup defaults for calibration pages, chart behavior, and "
                    "runtime options in one centralized form."
                ),
                color_name=styling.get_workflow_section_color(1),
            ),
            WorkflowStep(
                number="2",
                title="Create profile",
                description=(
                    "Save the current defaults as a named browser profile for quick context "
                    "switching across experiments and instruments."
                ),
                color_name=styling.get_workflow_section_color(2),
            ),
            WorkflowStep(
                number="3",
                title="Clean up profiles",
                description=(
                    "Remove stale profiles and keep only actively used defaults to reduce "
                    "configuration drift."
                ),
                color_name=styling.get_workflow_section_color(3),
            ),
        ]


_page = SettingsPage().register_callbacks()
layout = _page.layout


dash.register_page(
    __name__,
    path="/settings",
    name="Settings",
    order=4,
    layout=layout,
)
