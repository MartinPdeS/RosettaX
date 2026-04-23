import dash

from RosettaX.pages.settings import sections
from RosettaX.pages.settings.ids import Ids
from RosettaX.utils import styling

class SettingsPage:
    def __init__(self) -> None:
        self.ids = Ids()

        self.style = styling.PAGE

        self.sections = [
            sections.DefaultProfile(page=self),
            sections.CreateProfile(page=self),
            sections.DeleteProfile(page=self),
        ]

        self.backend = None

    def register_callbacks(self) -> "SettingsPage":
        for section in self.sections:
            section.register_callbacks()
        return self

    def layout(self) -> dash.html.Div:
        return dash.html.Div(
            [
                *[section._get_layout() for section in self.sections],
            ]
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