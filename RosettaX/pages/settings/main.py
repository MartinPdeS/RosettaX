import dash

from RosettaX.pages.settings import sections

from RosettaX.pages.settings.ids import Ids

class SettingsPage(
    sections.DefaultSettingValues,
    sections.CreateProfilePage,
    sections.DeleteProfilePage
):
    def __init__(self) -> None:
        self.ids = Ids()

        self.card_body_scroll = {"maxHeight": "60vh", "overflowY": "auto"}
        self.graph_style = {"width": "100%", "height": "45vh"}

        self.backend = None

    def register(self) -> None:
        """
        Register the page with Dash and all callbacks. The page must be registered before the layout can be accessed.

        Returns
        -------
        FluorescentCalibrationPage
            The page instance, returned for chaining purposes.
        """
        dash.register_page(__name__, path="/settings", name="Settings", order=1)
        self._edit_settings_register_callbacks()
        self._create_profile_register_callbacks()
        self._delete_profile_register_callbacks()
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
                self._edit_settings_get_layout(),
                self._create_profile_get_layout(),
                self._delete_profile_get_layout(),
            ]
        )

layout = SettingsPage().register().layout()