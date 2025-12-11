import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/flourescent_calibration', name='Flourescent Calibration')

layout = html.Div([
    html.H1('Create and Save A New Flourescent Calibration'),
    html.Div([
        "Select a city: ",
        dcc.RadioItems(
            options=['New York City', 'Montreal', 'San Francisco'],
            value='Montreal',
            id='analytics-input'
        )
    ]),
    html.Br(),
    html.Div(id='analytics-output'),
    html.Br(),
    html.Label('File Name:'),
    dcc.Input(id='file-name', type='text', value='Calibration_1.csv'),
    html.Br(),
    html.Button('Run Flourescent Calibration', id='run-calibration-button', n_clicks=0),
    html.Div(id='calibration-result-output'),
])

@callback(
    Output('analytics-output', 'children'),
    Input('analytics-input', 'value')
)
def update_city_selected(input_value):
    return f'You selected: {input_value}'

@callback(
    Output('calibration-result-output', 'children'),
    [Input('run-calibration-button', 'n_clicks'), 
    Input('file-name', 'value')]  # Assuming there's an input for file name
)
def run_flourescent_calibration(n_clicks, file_name):
    if n_clicks > 0:
        # Placeholder for actual calibration logic
        return f'Flourescent Calibration run {n_clicks} times with file name {file_name}.'
    return ''