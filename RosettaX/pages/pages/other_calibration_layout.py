import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/other_calibration', name='Other Calibration')

layout = html.Div([
    html.H1('Create and Save A New Other Calibration'),
    html.Div([
        "Select a city: ",
        dcc.RadioItems(
            options=['New York City', 'Montreal', 'San Francisco'],
            value='Montreal',
            id='analytics-input-other_calibration'
        )
    ]),
    html.Br(),
    html.Div(id='analytics-output-other_calibration'),
    html.Br(),
    html.Label('File Name:'),
    dcc.Input(id='file-name-other_calibration', type='text', value='Calibration_1.csv'),
    html.Br(),
    html.Button('Run Other Calibration', id='run-calibration-button-other_calibration', n_clicks=0),
    html.Div(id='calibration-result-output-other_calibration'),
])


@callback(
    Output('analytics-output-other_calibration', 'children'),
    Input('analytics-input-other_calibration', 'value')
)
def update_city_selected(input_value):
    return f'You selected: {input_value}'

@callback(
    Output('calibration-result-output-other_calibration', 'children'),
    [Input('run-calibration-button-other_calibration', 'n_clicks'), 
    Input('file-name-other_calibration', 'value')]  # Assuming there's an input for file name
)
def run_other_calibration(n_clicks, file_name):
    if n_clicks > 0:
        # Placeholder for actual calibration logic
        return f'Other Calibration run {n_clicks} times with file name {file_name}.'
    return ''