import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State, MATCH
from pages.styling import CONTENT_STYLE, SIDEBAR_STYLE
from pages.sidebar import sidebar_html

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)

# @app.callback(
#     Output("collapse-card", "is_open"),
#     [Input("collapse-button", "n_clicks")],
#     [State("collapse-card", "is_open")],
#     prevent_initial_call=True,
# )
# def toggle_collapse(n, is_open):
#     if n:
#         return not is_open
#     return is_open

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    return dash.page_container

@app.callback(
    Output("sidebar-content", "children", allow_duplicate=True),
    Input("url", "pathname"),
    State("apply-calibration-store", "data"),
    prevent_initial_call=True, 
)
def update_sidebar(url, sidebar):
    return sidebar_html(sidebar)

main_content = html.Div(dash.page_container, id="page-content", style=CONTENT_STYLE())
sidebar_content = html.Div(id="sidebar-content", style=SIDEBAR_STYLE())
app.layout = html.Div([dcc.Location(id="url"), dcc.Store(data={'Fluorescent':[], 'Scatter':[]}, id="apply-calibration-store", storage_type='session'), sidebar_content, main_content])

if __name__ == "__main__":
    app.run(debug=True)