import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/fluorescent_calibration', name='Fluorescent Calibration')

layout = html.Div([
    html.H1('Create and Save A New Fluorescent Calibration'),
    html.H3('Please select a rosetta beads calibration file to proceed. Select detectors and click "Find peak" to find the fluorescent peaks.'),

    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('1. Upload Bead File'),
            dbc.CardBody(
                dcc.Upload( id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select FluorescentFile')
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
                style={"maxHeight": "60vh", "overflowY": "auto"}
            )
        ]),
        id="collapse-card-2",
        is_open=True,
    ),
    html.Br(), 
    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('2. Find Peaks'),
            dbc.CardBody(
                html.Div([
                    html.Div([
                        html.Div(["Light Scattering Detector:"]),
                        dcc.Dropdown(id='fluorescence-detector-dropdown', value=None), 
                    ]),
                    html.Br(),
                    html.Div([
                        html.Div(["Fluorescence Detector:"]),
                        dcc.Dropdown(id='fluorescence-detector-dropdown', value=None), 
                    ]),
                    html.Br(),
                    html.Button('Find Peaks', id='find-peak-button-fluorescent_calibration', n_clicks=0),
                ]),
                style={"maxHeight": "60vh", "overflowY": "auto"}
            )
        ]),
        id="collapse-card-2",
        is_open=True,
    ),
    html.Br(), 
    dbc.Card([
        dbc.CardHeader('3. Bead Specifications'),
        dbc.Collapse(
            dbc.CardBody(
                html.Div([
                    html.Div("Add the bead specifications (Intensity in MESF and corresponding Intensity in a.u.) from the bottle/specification in the table below:"),
                    html.Br(),
                    html.Div([
                        dash_table.DataTable(
                            id='bead-spec-table',
                            columns=[
                                {"name": "Intensity (MESF)", "id": "col1", "editable": True},
                                {"name": "Intensity (a.u.)", "id": "col2", "editable": True},
                            ],
                            data=[{"col1": "", "col2": ""}, {"col1": "", "col2": ""}, {"col1": "", "col2": ""}],  # initial single empty row
                            editable=True,
                            row_deletable=True,
                            style_table={"overflowX": "auto"},
                        ),
                        html.Div([
                            html.Button("Add Row", id="add-row-button-fluorescent_calibration", n_clicks=0),
                        ], style={"marginTop": "10px"}),
                    ]),
                    html.Br(),
                    html.Button('Calibrate', id='calibrate-button-fluorescent_calibration', n_clicks=0),
                ]),
                style={"maxHeight": "60vh", "overflowY": "auto"}
            ), 
            id="collapse-card-2", is_open=True,
        )
    ]),
    html.Br(),
    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('4. Calibration Parameters'),
            dbc.CardBody(
                html.Div([
                    html.Div("Add the bead specifications (Intensity in MESF and corresponding Intensity in a.u.) from the bottle/specification in the table below:"),
                    html.Br(),
                    html.Div([
                        html.Div([
                            html.Div(["Calculated Slope:"]),
                            html.Div("", id='light-scattering-detector-output-slope')
                        ], style={"display": "flex", "alignItems": "center", "gap": "5px"}),
                        html.Div([
                            html.Div(["Calculated Intercept:"]),
                            html.Div("", id='light-scattering-detector-output-intercept')
                        ], style={"display": "flex", "alignItems": "center", "gap": "5px"}),
                        html.Label('Calibrated MESF Channel Name:'),
                        dcc.Input(id='channel-name-fluorescent_calibration', type='text', value='Calibration_1.csv'),
                    ]),
                ]),
                style={"maxHeight": "60vh", "overflowY": "auto"}
            )
        ]),
        id="collapse-card-2",
        is_open=True,
    ),
    html.Br(), 
    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('5. Graph Output'),
            dbc.CardBody(
                html.Div([
                    html.Div(dcc.Graph(), style={'display': 'inline-block'}),
                    html.Div(dcc.Graph(), style={'display': 'inline-block'})
                ], style={'width': '100%', 'display': 'inline-block'}),
                style={"maxHeight": "60vh", "overflowY": "auto"}
            )
        ]),
        id="collapse-card-2",
        is_open=True,
    ),
    html.Br(),
    dbc.Card([
        dbc.CardHeader('6. Save/Export Calibration'),
        dbc.Collapse(
            dbc.CardBody([
                html.Label('Save Calibration Setup As:'),
                dcc.Input(id='file-name-fluorescent_calibration', type='text', value='Calibration_1.csv'),
                html.Br(),
                html.Button('Save Fluorescent Calibration', id='run-calibration-button-fluorescent_calibration', n_clicks=0),
                html.Div(id='calibration-result-output-fluorescent_calibration'),
                # style={"maxHeight": "60vh", "overflowY": "auto"}
            ]), 
            id="collapse-card-2", is_open=True,
        )
    ]),
])

@callback(
    Output('calibration-result-output-fluorescent_calibration', 'children'),
    [Input('run-calibration-button-fluorescent_calibration', 'n_clicks'), 
    Input('file-name-fluorescent_calibration', 'value')]  # Assuming there's an input for file name
)
def run_fluorescent_calibration(n_clicks, file_name):
    if n_clicks > 0:
        # Placeholder for actual calibration logic
        return f'Fluorescent Calibration run {n_clicks} times with file name {file_name}.'
    return ''

@callback(
    Output('bead-spec-table', 'data'),
    Input('add-row-button-fluorescent_calibration', 'n_clicks'),
    State('bead-spec-table', 'data'),
    State('bead-spec-table', 'columns')
)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows