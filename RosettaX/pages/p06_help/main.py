import dash
import dash_bootstrap_components as dbc
from dash import html
from RosettaX.utils import ui_forms


class HelpPage:
    """Build workflow shortcuts, troubleshooting, and project resources."""

    def __init__(self) -> None:
        self.github_url = "https://github.com/MartinPdeS/RosettaX"
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"

    def layout(self, **_kwargs) -> dbc.Container:
        """Return the Help page layout."""
        return dbc.Container(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H1("Help", className="mb-2 fw-bold"),
                            html.P("Find a calibration workflow or troubleshoot a problem with your data.", className="mb-3"),
                            html.Div(
                                [
                                    dbc.Button("Sample files", href="/sample-files", color="primary"),
                                    dbc.Button("Tutorials", href="/tutorials", color="secondary", outline=True),
                                    dbc.Button("Technical docs", href="/documentation", color="secondary", outline=True),
                                ],
                                className="d-flex flex-wrap gap-2",
                            ),
                        ],
                        className="p-4",
                    ),
                    className="bg-body-tertiary",
                ),
                html.Section(
                    [
                        html.H2("Choose a workflow", className="h5 mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H3(html.A(title, href=path), className="h6"),
                                                html.P(description, className="mb-0 text-body-secondary"),
                                            ]
                                        ),
                                        className="h-100",
                                    ),
                                    md=4,
                                )
                                for title, path, description in (
                                    ("Fluorescence calibration", "/fluorescence", "Match bead peaks to reference fluorescence values and save a calibration."),
                                    ("Scattering calibration", "/scattering", "Match bead peaks to a scattering model using the detector geometry and bead properties."),
                                    ("Apply calibration", "/calibrate", "Use a saved calibration to convert measurements from one or more FCS files."),
                                )
                            ],
                            className="g-3",
                        ),
                    ]
                ),
                html.Section(
                    [
                        html.H2("Troubleshooting", className="h5 mb-3"),
                        dbc.Accordion(
                            [
                                dbc.AccordionItem(html.P(answer, className="mb-0"), title=symptom)
                                for symptom, answer in (
                                    ("I can’t upload a file or find my detector",
                                     "Try one FCS file first. Check the upload message and compare the detector dropdown with the channel names in that file. For batch apply, verify that the selected channel exists in every file."),
                                    ("My histogram is empty or peak detection misses a bead population",
                                     "Check the selected detector, axis scale, and event threshold. If the bead populations are visible, adjust the peak detection settings or select the peaks manually."),
                                    ("My calibration fit looks wrong",
                                     "Compare the peak plot with the calibration table. Check that each measured peak is paired with the intended reference bead. For scattering, also verify the detector geometry and bead properties."),
                                    ("I see a scattering inversion warning",
                                     "Inspect the target Mie relation and the selected monotonic branch. Check whether the signal range you are applying the calibration to is covered by that branch."),
                                    ("My saved calibration or export is missing something",
                                     "For a missing calibration, check the save location and refresh the sidebar. For an incomplete export, verify the selected calibration, target channel, and extra export columns before running it again."),
                                )
                            ],
                            start_collapsed=True,
                        ),
                    ]
                ),
                self._resources_card(),
            ],
            fluid=True,
            className="d-flex flex-column gap-4 px-0 pt-3 pb-4",
        )

    def _resources_card(self) -> dbc.Card:
        """Build the bug report checklist and project links."""
        card = dbc.Card(
            [
                dbc.CardHeader(html.H2("Report a problem", className="h5 mb-0")),
                dbc.CardBody(
                    [
                        html.P("Include enough detail to reproduce the issue."),
                        html.Ul(
                            [
                                html.Li("RosettaX version, workflow step, and exact error message."),
                                html.Li("FCS file names, selected detectors, and relevant settings."),
                                html.Li("A screenshot of the affected plot or table, and the saved calibration JSON for apply or export issues."),
                            ],
                            className="mb-3",
                        ),
                        html.Div(
                            [
                                dbc.Button("GitHub issues", href=f"{self.github_url}/issues", color="primary", outline=True),
                                dbc.Button("Email the developer", href=f"mailto:{self.contact_email}", color="secondary", outline=True),
                            ],
                            className="d-flex flex-wrap gap-2",
                        ),
                    ]
                ),
                dbc.CardFooter(
                    [
                        html.Span("Project resources", className="fw-semibold"),
                        html.A("GitHub", href=self.github_url),
                        html.A("PyPI", href="https://pypi.org/project/RosettaX/"),
                        html.A("Anaconda", href="https://anaconda.org/channels/MartinPdeS/packages/Rosettax/overview"),
                    ],
                    className="d-flex flex-wrap gap-3",
                ),
            ]
        )
        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )


_page = HelpPage()
layout = _page.layout

dash.register_page(
    __name__,
    path="/help",
    name="Help",
    order=3,
    layout=layout,
)
