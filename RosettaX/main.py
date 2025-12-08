import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State, MATCH
import os
from dash import ALL
from HTMLFrontend.styling import CONTENT_STYLE, SIDEBAR_STYLE
from HTMLFrontend.sidebar import sidebar as sbar
from HTMLFrontend.flourescent_calibration_layout import fluorescent_calibration_layout
from HTMLFrontend.other_calibration_layout import other_calibration_layout

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# the style arguments for the sidebar. We use position:fixed and a fixed width

# the styles for the main content position it to the right of the sidebar and
# add some padding.

sidebar = html.Div(
    sbar(),
    style=SIDEBAR_STYLE(),
)

content = html.Div(id="page-content", style=CONTENT_STYLE())

app.layout = html.Div([dcc.Location(id="url"), dcc.Store(id="start-calibration-store"), sidebar, content])


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return html.P("This is the content of the home page!")
    elif pathname == "/page-1":
        return fluorescent_calibration_layout()
    elif pathname == "/page-2":
        return other_calibration_layout()
    # If the user tries to reach a different page, return a 404 message
    else:
        return html.P("This is the content of the calibration start page.")

@app.callback(
    Output("collapse-card", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse-card", "is_open")],
    prevent_initial_call=True,
)
def toggle_collapse(n, is_open):
    if n:
        print(f"Toggle collapse to {not is_open}")
        return not is_open
    return is_open

@app.callback(
    Output("start-calibration-store", "data"),
    Input({"type": "start-calibration", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def start_calibration(n_clicks_list):
    # ctx = dash.callback_context
    # if not ctx.triggered:
    #     raise dash.exceptions.PreventUpdate
    # # triggered e.g. '{"type":"start-calibration","index":"folder/file"}.n_clicks'
    # triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    # id_dict = json.loads(triggered_id)
    # index = id_dict["index"]
    print(n_clicks_list)
    index = None
    print("Calibration started for:", index)
    return {"index": index, "n_clicks": n_clicks_list}

if __name__ == "__main__":
    app.run(port=8888)