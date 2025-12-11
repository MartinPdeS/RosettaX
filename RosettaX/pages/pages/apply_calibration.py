import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path_template='/apply-calibration/<calibration_type>/<file_name>', name='Apply Calibration')

def layout(calibration_type=None, file_name=None, **kwargs):
    return html.Div([
        html.H1(f'Calibrate using this saved calibration: {file_name}'),
        html.H1(f'Calibration for the Following type: {calibration_type}'),
        html.Div([
            "Select a calibration type: ",
            dcc.RadioItems(
                options=['Fluroescent Calibration', 'Other Calibration'],
                value='Fluroescent Calibration',
                id='apply-calibration-input'
            ), 
            dcc.Upload( id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
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
                multiple=True
            ),
        ]),
        html.Br(),
        html.Div(id='apply-calibration-output'),
        html.Br(),
    ])

@callback(
    Output('apply-calibration-output', 'children'),
    Input('apply-calibration-input', 'value')
)
def update_city_selected(input_value):
    return f'You selected: {input_value}'