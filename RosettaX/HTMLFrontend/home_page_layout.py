from dash import Input, Output, dcc, html, State, MATCH
import dash_bootstrap_components as dbc

def home_page_layout():
    return html.Div(
        [
            html.H2("Home Page"),
            html.P("This is the Home page content."),
            # Add more components relevant to home page here
        ]
    )