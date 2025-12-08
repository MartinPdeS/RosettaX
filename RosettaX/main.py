import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State, MATCH
import os
from dash import ALL
from pages.styling import CONTENT_STYLE, SIDEBAR_STYLE
from pages.sidebar import sidebar as sbar
import json

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)
sidebar = html.Div(sbar(), id="sidebar", style=SIDEBAR_STYLE())
content = html.Div(dash.page_container, id="page-content", style=CONTENT_STYLE())
app.layout = html.Div([dcc.Location(id="url"), dcc.Store(id="apply-calibration-store"), sidebar, content])

@app.callback(
    Output("collapse-card", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse-card", "is_open")],
    prevent_initial_call=True,
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("apply-calibration-store", "data"),
    Input({"type": "apply-calibration", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def apply_calibration(n_clicks_list):
    print(n_clicks_list)
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # ctx.triggered[0]['prop_id'] looks like '{"type":"apply-calibration","index":1}.n_clicks'
    prop_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        button_id = json.loads(prop_id)
    except Exception:
        button_id = prop_id

    print(button_id)  # prints the id dict of the button clicked
    return {"last_clicked": button_id}

if __name__ == "__main__":
    app.run(debug=True)