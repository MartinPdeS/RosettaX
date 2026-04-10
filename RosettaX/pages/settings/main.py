import dash

from RosettaX.pages.settings import sections

from RosettaX.pages.settings.ids import Ids

class SettingsPage():
    def __init__(self) -> None:
        self.ids = Ids()

        self.style = {
            "card_body_scroll": {"maxHeight": "60vh", "overflowY": "auto"},
            "graph": {"width": "100%", "height": "45vh"},
        }

        self.sections = [
            sections.DefaultSection(page=self),
            sections.CreateSection(page=self),
            sections.DeleteSection(page=self),
        ]

        self.backend = None

    def register(self) -> None:
        """
        Register the page with Dash and all callbacks. The page must be registered before the layout can be accessed.

        Returns
        -------
        SettingsPage
            The page instance, returned for chaining purposes.
        """
        dash.register_page(__name__, path="/settings", name="Settings", order=4)
        for section in self.sections:
            section._register_callbacks()
        return self

    def layout(self) -> dash.html.Div:
        """
        The layout is defined here in the main page file since it composes sections that are defined across multiple files.

        Returns
        -------
        dash.html.Div
            The layout of the settings page, composed of multiple sections.
        """
        return dash.html.Div(
            [
                dash.html.H1("Settings"),
                dash.html.P("Configure your RosettaX instance here. You can change the backend, manage your data, and adjust other settings."),
                *[section._get_layout() for section in self.sections]
            ]
        )

layout = SettingsPage().register().layout()