import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from root import ROOT_DIR
from pages.sidebar import sidebar_html

dash.register_page(__name__, path='/fluorescent_calibration', name='Fluorescent Calibration')

layout = html.Div([
    html.H1('Create and Save A New Fluorescent Calibration'),
    html.H3('Please select a rosetta beads calibration file to proceed. Select detectors and click "Find peak" to find the fluorescent peaks.'),

    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('1. Upload Bead File'),
            dbc.CardBody([
                dcc.Upload(id='upload-data',
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
                html.Div(id='upload-file-name')
            ], style={"maxHeight": "60vh", "overflowY": "auto"}, )
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
                        dcc.Dropdown(id='light-scattering-detector-dropdown', value=None), 
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
    
    html.Br(), 
    dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('4. Graph Output'),
            dbc.CardBody(
                html.Div([
                    html.Div(dcc.Graph(id='graph-1-fluorescent_calibration'), style={'display': 'inline-block', 'height': '100%', 'width': '20%'}),
                    html.Div(dcc.Graph(id='graph-2-fluorescent_calibration'), style={'display': 'inline-block', 'height': '100%', 'width': '80%'}),
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
    ),
    html.Br(),
    dbc.Card([
        dbc.CardHeader('5. Save/Export Calibration'),
        dbc.Collapse(
            dbc.CardBody([
                html.Label('Calibrated MESF Channel Name:'),
                dcc.Input(id='channel-name-fluorescent_calibration', type='text', value=''),
                html.Br(),
                html.Label('Save Calibration Setup As:'),
                dcc.Input(id='file-name-fluorescent_calibration', type='text', value=''),
                html.Br(),
                html.Button('Save Fluorescent Calibration', id='save-calibration-button-fluorescent_calibration', n_clicks=0),
                html.Div(id='calibration-result-output-fluorescent_calibration'),
                # style={"maxHeight": "60vh", "overflowY": "auto"}
            ]), 
            id="collapse-card-2", is_open=True,
        )
    ]),
])

@callback(
    Output('light-scattering-detector-dropdown', 'options'),
    Output('fluorescence-detector-dropdown', 'options'),
    Output('light-scattering-detector-dropdown', 'value'),
    Output('fluorescence-detector-dropdown', 'value'),
    Output('upload-file-name', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'), 
    prevent_initial_call=True,
)
def update_detector_dropdown(contents, filename):
    if contents is not None:
        # Placeholder for actual logic to extract detector names from the uploaded file
        detectors = ['Detector 1', 'Detector 2', 'Detector 3']
        detectors2 = ['Detector 4', 'Detector 5', 'Detector 6']
        return [{'label': det, 'value': det} for det in detectors], [{'label': det, 'value': det} for det in detectors2], detectors[0], detectors2[0], f'Selected file: {filename}'
    return [], [], None, None

@callback(
    Output('graph-1-fluorescent_calibration', 'figure'),
    Output('bead-spec-table', 'data', allow_duplicate=True),
    Input('find-peak-button-fluorescent_calibration', 'n_clicks'),
    State('light-scattering-detector-dropdown', 'value'),
    State('fluorescence-detector-dropdown', 'value'),
    prevent_initial_call=True,
)
def find_peaks(n_clicks, ls_detector, fl_detector):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    # create simple example bead-specs (MESF vs a.u.)
    mesf_vals = [1e3, 1e4, 1e5, 1e6, 1e7]
    au_vals = [10, 50, 200, 800, 3000]
    table_data = [{"col1": str(int(m)), "col2": str(a)} for m, a in zip(mesf_vals, au_vals)]

    # create simple Plotly figures and store them in a module-level variable so other callbacks can use them
    fig1 = go.Figure(go.Scatter(x=au_vals, y=mesf_vals, mode='lines'))
    fig1.update_layout(title='MESF vs Intensity (a.u.)', xaxis_title='Intensity (a.u.)', yaxis_title='Fluorescence Intensity (a.u.)')
    fig1.update_yaxes(type='log')

    table_data = [{"col1": str(int(m)), "col2": str(a)} for m, a in zip(mesf_vals, au_vals)]

    return fig1, table_data

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

@callback(
    Output('light-scattering-detector-output-slope', 'children'),
    Output('light-scattering-detector-output-intercept', 'children'),
    Output('channel-name-fluorescent_calibration', 'value', allow_duplicate=True),
    Output('graph-2-fluorescent_calibration', 'figure'),
    Input('calibrate-button-fluorescent_calibration', 'n_clicks'),
    State('bead-spec-table', 'data'),
    State('fluorescence-detector-dropdown', 'value'),
    prevent_initial_call=True,
)
def calibrate_fluorescence(n_clicks, table_data, fl_detector):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    # create simple example bead-specs (MESF vs a.u.)
    print(table_data)
    mesf_vals = []
    au_vals = []
    for row in table_data:
        mesf = float(row['col1'])
        au = float(row['col2'])
        mesf_vals.append(mesf)
        au_vals.append(au)

    # create simple Plotly figures and store them in a module-level variable so other callbacks can use them
    fig1 = go.Figure(go.Scatter(x=mesf_vals, y=au_vals, mode='markers'))
    x = np.array(mesf_vals, dtype=float)
    y = np.array(au_vals, dtype=float)
    mask = (x > 0) & (y > 0)

    if mask.sum() >= 2:
        logx = np.log10(x[mask])
        logy = np.log10(y[mask])
        p = np.polyfit(logx, logy, 1)
        slope, intercept = p[0], p[1]
        x_fit = np.logspace(np.log10(x[mask].min()), np.log10(x[mask].max()), 200)
        y_fit = 10 ** (slope * np.log10(x_fit) + intercept)
    else:
        # keep previous slope/intercept if not enough points
        x_fit = x
        y_fit = y
        slope = 0
        intercept = 0

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=mesf_vals, y=au_vals, mode='markers', name='beads'))
    fig1.add_trace(go.Scatter(x=x_fit, y=y_fit, mode='lines', name='log-log fit'))
    fig1.update_layout(title='MESF vs Intensity (a.u.)', xaxis_title='Intensity (a.u.)', yaxis_title='Fluorescence Intensity (a.u.)')
    fig1.update_yaxes(type='log')
    fig1.update_xaxes(type='log')

    return f'{slope:.3f}', f'{intercept:.3f}', fl_detector, fig1

@callback(
    Output('calibration-result-output-fluorescent_calibration', 'children'),
    Output('apply-calibration-store', 'data'),
    Output('sidebar-content', 'children'),
    Input('save-calibration-button-fluorescent_calibration', 'n_clicks'),
    State('file-name-fluorescent_calibration', 'value'),
    State('apply-calibration-store', 'data'),
    prevent_initial_call=True
)
def save_calibration(n_clicks, file_name, sidebar_data):
    if n_clicks and n_clicks > 0:
        # downloads_dir = os.path.join(ROOT_DIR, 'SavedCalibrations', 'FluorescentCalibrations')
        # os.makedirs(downloads_dir, exist_ok=True)
        # filename = (file_name or "fluorescent_calibration.csv").strip()
        # path = os.path.join(downloads_dir, filename)

        # with open(path, "w", encoding="utf-8") as f:
        #     f.write("Calibration saved\n")
        #     f.write(f"Timestamp,{datetime.datetime.now().isoformat()}\n")
        # print(f"Calibration saved to {path}")
        # return f'Calibration saved to {path}'
        print(sidebar_data)
        sidebar_data['Fluorescent'].append(file_name)
        print(sidebar_data)
        return f'Calibration "{file_name}" saved successfully.', sidebar_data, sidebar_html(sidebar_data)
    return dash.no_update