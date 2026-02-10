import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


SIDEBAR_PREFIX = "sidebar"
COLLAPSE_BUTTON_ID = f"{SIDEBAR_PREFIX}-collapse-button"
COLLAPSE_CARD_ID = f"{SIDEBAR_PREFIX}-collapse-card"


def sidebar_html(sidebar: dict[str, list[str]]):
    """
    Build sidebar navigation and saved calibration list.

    Parameters
    ----------
    sidebar
        Mapping of folder name to a list of calibration filenames.

    Returns
    -------
    list
        Dash components that can be placed in a container, typically a Div children list.
    """
    page_links = [
        dbc.NavLink(page["name"], href=page["relative_path"], active="exact")
        for page in dash.page_registry.values()
        if page.get("name") != "Apply Calibration"
    ]

    saved_items = []
    for folder, files in (sidebar or {}).items():
        saved_items.append(
            html.Div(
                [
                    html.H5(folder),
                    html.Ul(
                        [
                            html.Li(
                                dcc.Link(
                                    file,
                                    href=f"/apply-calibration/{folder}/{file}",
                                    id={"type": "apply-calibration", "index": f"{folder}/{file}"},
                                )
                            )
                            for file in files
                        ]
                    ),
                ]
            )
        )

    return [
        dbc.Col(
            html.Img(
                src="/assets/logo.png",
                style={"height": "156px", "width": "auto"},
            ),
            width="auto",
        ),
        html.Hr(),
        html.P("Navigation bar", className="lead"),
        dbc.Nav(page_links, vertical=True, pills=True),
        html.Hr(),
        dbc.Button(
            "Apply Saved Calibrations",
            id=COLLAPSE_BUTTON_ID,
            className="mb-3",
            color="primary",
            n_clicks=0,
            style={"width": "100%"},
        ),
        dbc.Collapse(
            dbc.Card(
                [
                    dbc.CardHeader("Saved Calibrations"),
                    dbc.CardBody(saved_items, style={"maxHeight": "60vh", "overflowY": "auto"}),
                ]
            ),
            id=COLLAPSE_CARD_ID,
            is_open=True,
        ),
    ]
