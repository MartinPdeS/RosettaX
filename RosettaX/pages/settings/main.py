import dash
from dash import dcc, html
from RosettaX.pages.settings.default_settings_values import DefaultSettingValues
from RosettaX.pages.settings.profiles import ProfilesPage
from RosettaX.pages.settings.new_profile import NewProfilePage
from RosettaX.pages.settings.delete_profile import DeleteProfilePage
from RosettaX.pages.settings.ids import Ids

class SettingsPage(ProfilesPage, DefaultSettingValues, NewProfilePage, DeleteProfilePage):
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
        self._new_profile_register_callbacks()
        self._delete_profile_register_callbacks()
        return self

    def layout(self) -> html.Div:
        """
        The layout is defined here in the main page file since it composes sections that are defined across multiple files.

        Returns
        -------
        html.Div
            The layout of the fluorescent calibration page, composed of multiple sections.
        """
        return html.Div(
            [
                html.H1("Settings"),
                html.P("Configure your RosettaX instance here. You can change the backend, manage your data, and adjust other settings."),
                self._edit_settings_get_layout(),
                self._new_profile_get_layout(),
                self._delete_profile_get_layout(),
            ]
        )
        return self

layout = SettingsPage().register().layout()