import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State, MATCH
import os
from dash import ALL
from pages.styling import CONTENT_STYLE, SIDEBAR_STYLE
from pages.sidebar import sidebar as sbar

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

# @app.callback(
#     Output("apply-calibration-store", "data"),
#     Input({"type": "apply-calibration", "index": ALL}, "n_clicks"),
#     prevent_initial_call=True,
# )
# def apply_calibration(n_clicks_list):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate
#     # triggered e.g. '{"type":"apply-calibration","index":"folder/file"}.n_clicks'
#     triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
#     id_dict = json.loads(triggered_id)
#     index = id_dict["index"]
#     print(n_clicks_list)
#     index = None
#     print("Calibration started for:", index)
#     return {"index": index, "n_clicks": n_clicks_list}

if __name__ == "__main__":
    app.run(debug=True)