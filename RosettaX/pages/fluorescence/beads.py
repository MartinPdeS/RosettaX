from typing import List, Optional
import numpy as np

from dash import Input, Output, State, callback, dash_table, html
import dash_bootstrap_components as dbc


class BeadsSection():
    def _bead_get_layout(self) -> dbc.Card:
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

    def _bead_register_callbacks(self) -> None:
        @callback(
            Output(self.ids.bead_table, "data", allow_duplicate=True),
            Input(self.ids.add_row_btn, "n_clicks"),
            State(self.ids.bead_table, "data"),
            State(self.ids.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(n_clicks: int, rows: List[dict], columns: List[dict]) -> List[dict]:
            next_rows = list(rows or [])
            next_rows.append({c["id"]: "" for c in columns})
            return next_rows
