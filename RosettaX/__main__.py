import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State
import webbrowser
from threading import Timer
import json
from RosettaX.pages.styling import CONTENT_STYLE, SIDEBAR_STYLE
from RosettaX.pages.sidebar import sidebar_html

def create_table_from_dict():
    # {"col1": "", "col2": ""}
    try:
        with open('RosettaX/data/settings/saved_mesf_values.json', 'r') as file:
            data = json.load(file)
            table_data = []
            for key, value in data.items():
                if value.get('default', True):
                    mesf_values = value['mesf_values'].split(',')
                    for mesf in mesf_values:
                        table_data.append({"col1": mesf, "col2": ""})
    except Exception as e:
        table_data = [{"col1": "", "col2": ""}]
    return table_data

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
    style=CONTENT_STYLE()
)
sidebar_content = html.Div(
    id="sidebar-content",
    style=SIDEBAR_STYLE()
)

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Store(data={'Fluorescent':[], 'Scatter':[]}, id="apply-calibration-store", storage_type='session'),
        dcc.Store(data=create_table_from_dict(), id="MESF-default_table-store", storage_type='session'), 
        sidebar_content,
        main_content
    ]
)

def open_browser():
	webbrowser.open_new("http://localhost:{}".format(8050))

if __name__ == "__main__":
    Timer(1, open_browser).start()

    app.run(debug=True, port=8050)