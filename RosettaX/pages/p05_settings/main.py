import dash
import dash_bootstrap_components as dbc
from . import sections
from .ids import Ids
from .state import SettingsPageState
from RosettaX.ui import WorkflowHeader
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
        self.workflow_header = WorkflowHeader(
            title="Settings",
            description=(
                "Configure reusable defaults for fluorescence, scattering, "
                "apply-calibration, and visualization behavior. Save everything as "
                "browser profiles for rapid workflow switching."
            ),
            steps=[step for section in self.sections for step in section.workflow_steps],
        )

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
                *[section.get_layout() for section in self.sections],
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": styling.get_spacing_token("md"),
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return self.workflow_header.build_header()



_page = SettingsPage().register_callbacks()
layout = _page.layout


dash.register_page(
    __name__,
    path="/settings",
    name="Settings",
    order=4,
    layout=layout,
)
