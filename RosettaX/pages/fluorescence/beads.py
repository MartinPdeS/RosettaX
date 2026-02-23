from typing import List

from dash import Input, Output, State, callback, dash_table, html
import dash_bootstrap_components as dbc

from RosettaX.pages.fluorescence import BaseSection, SectionContext


class BeadsSection(BaseSection):
    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)

    def layout(self) -> dbc.Card:
        ids = self.context.ids

        return dbc.Card(
            [
                dbc.CardHeader("4. Bead specifications"),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.Br(),
                            dash_table.DataTable(
                                id=ids.bead_table,
                                columns=self.context.bead_table_columns,
                                data=self.context.default_bead_rows,
                                editable=True,
                                row_deletable=True,
                                style_table={"overflowX": "auto"},
                            ),
                            html.Div(
                                [html.Button("Add Row", id=ids.add_row_btn, n_clicks=0)],
                                style={"marginTop": "10px"},
                            ),
                            html.Br(),
                            html.Button("Calibrate", id=ids.calibrate_btn, n_clicks=0),
                        ],
                        style=self.context.card_body_scroll,
                    ),
                    id=f"collapse-{ids.page_name}-beadspec",
                    is_open=True,
                ),
            ]
        )

    def register_callbacks(self) -> None:
        ids = self.context.ids

        @callback(
            Output(ids.bead_table, "data"),
            Input(ids.add_row_btn, "n_clicks"),
            State(ids.bead_table, "data"),
            State(ids.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, rows: List[dict], columns: List[dict]) -> List[dict]:
            next_rows = list(rows or [])
            next_rows.append({c["id"]: "" for c in columns})
            return next_rows
