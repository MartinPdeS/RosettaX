import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/scatter_calibration', name='Scatter Calibration')

layout = html.Div([
    html.H1('Create and Save A New Scatter Calibration'),
    dcc.Upload( id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False,
    ),
    html.Br(),
    dbc.Collapse(
        dbc.Card(
            dbc.CardBody(
                html.Div([
                    html.Div([
                        html.Div(["Flow Cytometry Name: "]),
                        html.Div(id='flow-cytometry-data-file-output')
                    ]),
                    html.Div([
                        html.Div(["Flow Cytometry Type: "]),
                        dcc.Dropdown(id='flow-cytometry-data-file-dropdown', value=None), 
                    ]),
                    html.Div([
                        html.Div(["Forward Scatter: "]),
                        dcc.Dropdown(id='bead-calibration-file-dropdown', value=None),
                    ]), 
                    html.Div([
                        html.Div(["Wavelength (nm): "]),
                        dcc.Input(id='sample-parameter-input', type='number', value=''),
                    ]), 
                    html.Div([
                        html.Div(["Side Scatter: "]),
                        dcc.Dropdown(id='bead-calibration-file-dropdown', value=None),
                    ]), 
                    html.Div([
                        html.Div(["Wavelength (nm): "]),
                        dcc.Input(id='sample-parameter-input', type='number', value=''),
                    ]), 
                    html.Div([
                        html.Div(["Green fluorescence: "]),
                        dcc.Dropdown(id='bead-calibration-file-dropdown', value=None),
                    ])
                ]),
                style={"maxHeight": "60vh", "overflowY": "auto"}
            )
        ),
        id="collapse-card",
        is_open=True,
    ),
    html.Br(),
    html.Button('Calibrate', id='calibrate-flow-cytometry-button', n_clicks=0),
    
    html.Div([
        html.Div("Set sample Calculation Parameters:"),
        dcc.RadioItems(
            options=['Solid Sphere', 'Core/Shell Sphere'],
            value='Solid Sphere',
            id='calculation-parameter-input'
        ), 
        dcc.RadioItems(
            options=['water', 'PBS', 'other'],
            value='water',
            id='refractive-index-input'
        ),
        dcc.Input(id='custom-refractive-index-input', type='number', value='', placeholder='Custom Refractive Index'),
        dcc.Input(id='particle-core-refractive-index-input', type='number', value='', placeholder='Particle Density (g/cm3)'),
        dcc.Input(id='particle-shell-refractive-index-input', type='number', value='', placeholder='Wavelength (nm)'),
        dcc.Input(id='particle-shell-thickness-input', type='number', value='', placeholder='Particle Shell Thickness (nm)'),
    ]),
    
    html.Label('File Name:'),
    dcc.Input(id='file-name', type='text', value='Calibration_1.csv'),
    html.Br(),
    html.Button('Run Scatter Calibration', id='run-calibration-button', n_clicks=0),
    html.Div(id='calibration-result-output'),
])

@callback(
    Output('calibration-result-output', 'children'),
    [Input('run-calibration-button', 'n_clicks'), 
    Input('file-name', 'value')]  # Assuming there's an input for file name
)
def run_scatter_calibration(n_clicks, file_name):
    if n_clicks > 0:
        # Placeholder for actual calibration logic
        return f'Scatter Calibration run {n_clicks} times with file name {file_name}.'
    return ''