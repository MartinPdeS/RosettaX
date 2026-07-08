# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
    build_documentation_link_chip,
)


class InstallLocalDocumentationPage:
    """
    Documentation for installing RosettaX locally from GitHub releases.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-install-local"
        self.releases_url = "https://github.com/MartinPdeS/RosettaX/releases"
        self.latest_windows_url = (
            "https://github.com/MartinPdeS/RosettaX/releases/latest/download/"
            "RosettaX-windows-x86_64.zip"
        )
        self.latest_macos_url = (
            "https://github.com/MartinPdeS/RosettaX/releases/latest/download/"
            "RosettaX-macos.zip"
        )
        self.latest_linux_url = (
            "https://github.com/MartinPdeS/RosettaX/releases/latest/download/"
            "RosettaX-linux-x86_64.zip"
        )

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Install RosettaX Locally",
                    description=(
                        "This page explains how to download and run the prebuilt RosettaX bundles from GitHub Releases "
                        "without building from source."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use the documentation hub for workflow and model details after installation.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="Quick start",
                                    href="/documentation",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "10px",
                            },
                        ),
                    ],
                    min_height="unset",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._download_buttons_card(), lg=6),
                        dbc.Col(self._install_steps_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._validation_notes_card(),
            ]
        )

    def _download_buttons_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Download latest release bundle",
            subtitle="Choose the archive for your operating system.",
            body=[
                html.Div(
                    [
                        dbc.Button(
                            "Download Windows",
                            href=self.latest_windows_url,
                            color="primary",
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"fontWeight": "700"},
                        ),
                        dbc.Button(
                            "Download macOS",
                            href=self.latest_macos_url,
                            color="primary",
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"fontWeight": "700"},
                        ),
                        dbc.Button(
                            "Download Linux",
                            href=self.latest_linux_url,
                            color="primary",
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"fontWeight": "700"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "10px",
                        "marginBottom": "12px",
                    },
                ),
                html.Div(
                    [
                        "Need a different version? Use the full ",
                        html.A(
                            "Releases page",
                            href=self.releases_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"textDecoration": "none", "fontWeight": "600"},
                        ),
                        ".",
                    ],
                    style={"opacity": 0.85},
                ),
            ],
            min_height="unset",
        )

    def _install_steps_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Install and run",
            subtitle="Run directly from the extracted bundle.",
            body=[
                html.Ol(
                    [
                        html.Li("Download the ZIP archive for your OS."),
                        html.Li("Extract it to a folder where you have write permission."),
                        html.Li("Open the extracted rosettax folder."),
                        html.Li("Run rosettax (macOS/Linux) or rosettax.exe (Windows)."),
                    ],
                    style={
                        "marginBottom": "0px",
                        "paddingLeft": "20px",
                        "display": "grid",
                        "rowGap": "7px",
                    },
                ),
            ],
            min_height="unset",
        )

    def _validation_notes_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Validation and provenance",
            subtitle="Recommended checks before distributing binaries internally.",
            body=[
                html.Div("Confirm you downloaded the expected version tag from the release page."),
                html.Div("Verify release checksums and provenance metadata when required by your lab or organization."),
                html.Div("Keep exported reports together with calibrated files for traceability."),
            ],
            min_height="unset",
        )


_page = InstallLocalDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/install-local",
    name="Install Locally",
    layout=layout,
)
