import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State
import webbrowser
from threading import Timer


from RosettaX.pages import styling
from RosettaX.pages.sidebar import sidebar_html

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True
)

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

main_content = html.Div(
    dash.page_container,
    id="page-content",
    style=styling.CONTENT
)
sidebar_content = html.Div(
    id="sidebar-content",
    style=styling.SIDEBAR
)

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Store(data={'Fluorescent':[], 'Scatter':[]}, id="apply-calibration-store", storage_type='session'),
        sidebar_content,
        main_content
    ]
)

def open_browser():
	webbrowser.open_new("http://localhost:{}".format(8050))

if __name__ == "__main__":
    Timer(1, open_browser).start()

    app.run(debug=True, port=8050)