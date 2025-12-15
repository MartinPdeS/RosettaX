import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/help', name='Help Page')
layout = html.Div([
    html.H1('This is our Help Page'),

])