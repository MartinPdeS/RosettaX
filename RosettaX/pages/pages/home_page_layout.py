import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/', name='Home Page')
layout = html.Div([
    html.H1('This is our Home Page'),
    
])