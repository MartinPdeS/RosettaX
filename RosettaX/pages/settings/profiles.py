from dash import html

class ProfilesPage():
    def __init__(self) -> None:
        pass

    def layout(self):
        """
        Layout for the Profiles page. This page allows users to manage their profiles, including creating, editing, and deleting profiles
        """
        return html.Div(
            [
                html.H1("Profiles"),
                html.P("Manage your profiles here. You can create, edit, and delete profiles to customize your experience."),
            ]
        )