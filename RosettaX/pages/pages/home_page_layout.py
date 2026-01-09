import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/', name='Home Page')
layout = html.Div([
    html.H1('Welcome to RosettaX'),
    html.P('This is the home page of the RosettaX application. Use the sidebar to navigate through different features.'),
    dcc.Link('Go to Help Page for more information on how to use this tool', href='/help'),
    html.Br(),
    html.P("Have you never used this tool before and saved a calibration before? If so, you can start a new calibration."),
    html.Div("Go to the Fluorescent Calibration page to start a new calibration on fluorescent."),
    dcc.Link('Fluorescent Calibration', href='/fluorescent_calibration'),
    html.Br(),html.Br(),
    html.Div("Go to the Scatter Calibration page to start a new calibration on scatter."),
    dcc.Link('Scatter Calibration', href='/scatter_calibration'),

    html.Div("Have you already created a calibration? If so, you can select it from the sidebar."),
])