import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/scatter_calibration', name='Scatter Calibration')

layout = html.Div([
    html.H1('Create and Save A New Scatter Calibration'),
    dbc.Card([
        dbc.CardHeader('1. Select Flow Cytometry Data and Parameters'),
        dbc.Collapse(
            dbc.CardBody(
                html.Div([
                    html.Div([
                    dcc.Input(style={'marginRight': '10px', 'width':'100%'}, id='bead-file-location-input', type='text', placeholder='Location of Rosetta Bead Files:'),
                ]),
                html.Div(id='bead-file-location-output'),
                    # Use flex layout so each label+control is inline and wraps if needed
                    html.Div([
                        html.Div(["Flow Cytometry Name: "], style={'minWidth': '160px'}),
                        html.Div(id='flow-cytometry-data-file-output', style={'flex': '1 1 200px'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
                    html.Div([
                        html.Div(["Flow Cytometry Type: "], style={'minWidth': '160px'}),
                        dcc.Dropdown(id='flow-cytometry-data-file-dropdown', value=None, style={'width': '250px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div(["Forward Scatter: "], style={'minWidth': '160px'}),
                        dcc.Dropdown(id='bead-calibration-file-dropdown', value=None, style={'width': '250px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div(["Wavelength (nm): "], style={'minWidth': '160px'}),
                        dcc.Input(id='sample-parameter-input', type='number', value='', style={'width': '120px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div(["Side Scatter: "], style={'minWidth': '160px'}),
                        dcc.Dropdown(id='bead-calibration-file-dropdown', value=None, style={'width': '250px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div(["Wavelength (nm): "], style={'minWidth': '160px'}),
                        dcc.Input(id='sample-parameter-input', type='number', value='', style={'width': '120px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div(["Green fluorescence: "], style={'minWidth': '160px'}),
                        dcc.Dropdown(id='bead-calibration-file-dropdown', value=None, style={'width': '250px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                ], style={"display": "flex", "flexDirection": "column", "gap": "6px", "maxHeight": "60vh", "overflowY": "auto"}),
            ),
            id="collapse-card",
            is_open=True
        ),
    ]),
    html.Br(),
    html.Button('Calibrate', id='calibrate-flow-cytometry-button', n_clicks=0),
    
    dbc.Card([
        dbc.CardHeader('2. Set Example Calculation Parameters'),
        dbc.Collapse(
            dbc.CardBody(
                html.Div([
                    html.Div([
                        html.Div("Mie Model:", style={'minWidth': '160px'}),
                        dcc.RadioItems(['Solid Sphere', 'Core/Shell Sphere'], 'Solid Sphere', id='calculation-parameter-input', inline=True, labelClassName='me-3'),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
                    html.Div([
                        html.Div("Medium Refractive Index:", style={'minWidth': '160px'}),
                        dcc.RadioItems(['water', 'PBS', 'other'], 'water', id='refractive-index-input', inline=True, labelClassName='me-3'),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div("Custom Refractive Index:", style={'minWidth': '160px'}),
                        dcc.Input(id='custom-refractive-index-input', type='number', placeholder='Custom Refractive Index', style={'width': '160px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div("Particle Core Refractive Index:", style={'minWidth': '160px'}),
                        dcc.Input(id='particle-core-refractive-index-input', type='number', placeholder='Particle Core Refractive Index', value=1.38, min=1.0, max=2.5, step=0.001, style={'width': '160px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div("Particle Shell Refractive Index:", style={'minWidth': '160px'}),
                        dcc.Input(id='particle-shell-refractive-index-input', type='number', placeholder='Particle Shell Refractive Index', value=1.48, min=1.0, max=2.5, step=0.001, style={'width': '160px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Div([
                        html.Div("Particle Shell Thickness (nm):", style={'minWidth': '160px'}),
                        dcc.Input(id='particle-shell-thickness-input', type='number', placeholder='Particle Shell Thickness (nm)', value=6, min=0, step=1, style={'width': '120px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'marginTop': '8px'}),
                    html.Button('Calibrate', id='calibrate-button-fluorescent_calibration', n_clicks=0, style={'marginTop': '8px'}),
                ]),
                style={"maxHeight": "60vh", "overflowY": "auto"}
            ), 
            id="collapse-card-2", is_open=True,
        )
    ]),

    dbc.Card([
        dbc.CardHeader('3. Export Size Calibration'),
        dbc.Collapse(
            dbc.CardBody(
                html.Div([
                    html.Button('Run Scatter Calibration', id='run-calibration-button', n_clicks=0),
                    dcc.Input(id='file-name', type='text', placeholder='Enter file name', style={'width': '200px'}),
                    html.Button('Save/Export Scatter Calibration', id='save-export-calibration-button', n_clicks=0),
                    html.Br(),html.Br(),

                    html.Div("Interpolate (optional):"), 
                    dcc.Input(id='interpolate-input', type='text', placeholder='Enter interpolation method', style={'width': '200px'}), 
                    dcc.Input(id='interpolate-au', type='number', placeholder='Enter AU value', style={'width': '200px'}),
                    dcc.Input(id='interplate-area', type='number', placeholder='Enter area value nm^2', style={'width': '200px'}),
                    html.Button('Interpolate Calibration', id='interpolate-calibration-button', n_clicks=0),
                    html.Br(),html.Br(),
                ], style={"display": "flex", "flexDirection": "column", "gap": "6px", "maxHeight": "60vh", "overflowY": "auto"}),
            ),
            id="collapse-card",
            is_open=True
        ),
    ]),
    html.Br(), 
    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('4. Graph Output'),
            dbc.CardBody(
                html.Div([
                    html.Div(dcc.Graph(id='graph-1-scatter_calibration'), style={'display': 'inline-block', 'height': '90%', 'width': '20%'}),
                    html.Div(dcc.Graph(id='graph-2-scatter_calibration'), style={'display': 'inline-block', 'height': '90%', 'width': '80%'}),
                    html.Div([
                        html.Div([
                            html.Div(["Calculated Slope:"]),
                            html.Div("", id='light-scattering-detector-output-slope')
                        ], style={"display": "flex", "alignItems": "center", "gap": "5px"}),
                        html.Div([
                            html.Div(["Calculated Intercept:"]),
                            html.Div("", id='light-scattering-detector-output-intercept')
                        ], style={"display": "flex", "alignItems": "center", "gap": "5px"}),
                    ]),
                ], style={'width': '100%', 'height':'100%', 'display': 'inline-block'}),
                style={"height": "100%", "overflowY": "auto"}
            )
        ], style={"height": "70vh", "overflowY": "auto"}),
        id="collapse-card-2",
        is_open=True,
    )
])

@callback(
    Output('graph-1-scatter_calibration', 'figure'),
    [Input('run-calibration-button', 'n_clicks'), 
    Input('file-name', 'value')], 
    prevent_initial_call=True
)
def run_scatter_calibration(n_clicks, file_name):
    if n_clicks > 0:
        # Placeholder for actual calibration logic
        return f'Scatter Calibration run {n_clicks} times with file name {file_name}.'
    return ''