"""Settings page for browser-saved workflow profiles."""

import dash
from . import sections
from .ids import Ids
from dash import html
from RosettaX.application.access import can_edit_settings
from RosettaX.utils import styling


class SettingsPage:
    """Assemble the settings page and its profile editor."""

    def __init__(self) -> None:
        self.ids = Ids()
        self.style = styling.PAGE
        self.sections = [sections.DefaultProfile(page=self)]

    def register_callbacks(self) -> "SettingsPage":
        """Register the profile editor callbacks."""
        for section in self.sections:
            section.register_callbacks()
        return self

    def layout(self) -> html.Div:
        """Render the settings workspace."""
        if not can_edit_settings():
            return html.Div(
                [html.H1("Settings"), html.P("Use the sidebar to load a curated profile."),
                 html.A("Administrator sign-in", href="/admin/login?next=/settings")],
                className="settings-page settings-heading",
            )
        return html.Div(
            [
                html.Header(
                    [
                        html.H1("Settings"),
                        html.P(
                            "Manage browser profiles and choose the defaults RosettaX uses for your workflows."
                        ),
                    ],
                    className="settings-heading",
                ),
                *[section.get_layout() for section in self.sections],
            ],
            className="settings-page",
        )


_page = SettingsPage().register_callbacks()
layout = _page.layout

dash.register_page(__name__, path="/settings", name="Settings", order=4, layout=layout)
