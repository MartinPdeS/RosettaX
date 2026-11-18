"""Tutorial landing page for visual RosettaX workflow guides."""

import dash
import dash_bootstrap_components as dbc
from dash import html
from RosettaX.utils import styling, ui_forms


def build_layout() -> dbc.Container:
    """Build the tutorials page while its visual guides are being prepared.

    Returns
    -------
    dash_bootstrap_components.Container
        The tutorials page layout.
    """
    return dbc.Container(
        [
            dbc.Card(
                dbc.CardBody(
                    ui_forms.build_section_intro(
                        title="Tutorials",
                        title_component="H2",
                        description=(
                            "Follow short visual guides to learn common RosettaX "
                            "workflows, from loading FCS files to applying a calibration."
                        ),
                    ),
                ),
                style=ui_forms.build_workflow_section_card_style(
                    color_name=styling.get_workflow_page_header_color(),
                ),
            ),
            dbc.Alert(
                [
                    html.H4("Tutorials are under construction", className="alert-heading"),
                    html.P(
                        "Step-by-step GIF guides are being prepared and will be added here."
                    ),
                    html.P(
                        [
                            "In the meantime, visit ",
                            html.A("Sample files", href="/sample-files"),
                            " to find data for practicing the RosettaX workflows.",
                        ],
                        className="mb-0",
                    ),
                ],
                color="info",
                className="mt-3",
            ),
        ],
        fluid=True,
        style={
            **styling.PAGE,
            "paddingLeft": "0px",
            "paddingRight": "0px",
        },
    )


layout = build_layout()

dash.register_page(
    __name__,
    path="/tutorials",
    name="Tutorials",
    order=25,
    layout=layout,
)
