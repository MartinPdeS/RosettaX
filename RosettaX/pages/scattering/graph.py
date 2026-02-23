from dash import dcc, html
import dash_bootstrap_components as dbc

from RosettaX.pages.scattering.base import BaseSection

class GraphSection(BaseSection):
    def layout(self) -> dbc.Card:
        ids = self.context.ids

        return dbc.Card(
            [
                dbc.CardHeader("4. Graph Output"),
                dbc.CardBody(
                    html.Div(
                        [
                            html.Div(
                                dcc.Graph(id=ids.graph_1),
                                style={"display": "inline-block", "height": "90%", "width": "20%"},
                            ),
                            html.Div(
                                dcc.Graph(id=ids.graph_2),
                                style={"display": "inline-block", "height": "90%", "width": "80%"},
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [html.Div(["Calculated Slope:"]), html.Div("", id=ids.slope_out)],
                                        style={"display": "flex", "alignItems": "center", "gap": "5px"},
                                    ),
                                    html.Div(
                                        [html.Div(["Calculated Intercept:"]), html.Div("", id=ids.intercept_out)],
                                        style={"display": "flex", "alignItems": "center", "gap": "5px"},
                                    ),
                                ]
                            ),
                        ],
                        style={"width": "100%", "height": "100%", "display": "inline-block"},
                    ),
                    style={"height": "100%", "overflowY": "auto"},
                ),
            ],
            style={"height": "70vh", "overflowY": "auto"},
        )
