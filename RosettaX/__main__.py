import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State
import webbrowser
from threading import Timer
import json

from RosettaX.pages import styling
from RosettaX.pages.sidebar import sidebar_html

def create_table_from_dict():
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
    Output("sidebar-content", "children"),
    Input("url", "pathname"),
    Input("apply-calibration-store", "data"),
)
def update_sidebar(_url, sidebar_data):
    return sidebar_html(sidebar_data)

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