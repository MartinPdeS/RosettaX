import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import time
import json

dash.register_page(__name__, path_template='/settings', name='Settings')

def load_mesf_values():
    filename = 'RosettaX/data/settings/saved_mesf_values.json'
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return {}
    
def layout(**kwargs):
    return html.Div([
        dbc.Collapse(
        dbc.Card([
            dbc.CardHeader('Rosetta Bead Fluorescent MESF File Settings'),
            dbc.CardBody([
                html.Div([
                    html.Div("Enter MESF Values from Manufacturer:"),
                    dcc.Input(style={'marginRight': '10px', 'width':'100%'}, id='mesf-bead-values-input', type='text', placeholder='MESF Values from Manufacturer'),
                    html.Br(),
                    html.Br(),
                    html.A(html.Button('Save MESF Values', id='save-mesf-values-button', n_clicks=0), href='/settings'),
                    html.Div(id='save-mesf-values-output')
                ]), 
                html.Br(), 
                html.Div([
                    html.Div("Change Default MESF Settings:"),
                    dcc.Dropdown(
                        id='change-default-mesf-values-dropdown',
                        options=[{'label': f"{value['mesf_values']}", 'value': key} for key, value in load_mesf_values().items()],
                        placeholder='Enter MESF Values to Set as Default',
                        value='' if not any(value.get('default', False) for value in load_mesf_values().values()) else next(key for key, value in load_mesf_values().items() if value.get('default', False)),
                        style={'width':'100%'},
                    ),
                    html.Br(),
                    html.Button('Save MESF Values', id='save-default-mesf-values-button', n_clicks=0),
                    html.Div(id='save-default-mesf-values-output')
                ]), 
                html.Br(), 
                html.Div([
                    html.Div("Delete MESF Entry:"),
                    dcc.Dropdown(
                        id='delete-mesf-values-dropdown',
                        options=[{'label': f"{value['mesf_values']}", 'value': key} for key, value in load_mesf_values().items()],
                        placeholder='Select MESF Values to Delete',
                        # value='' if not any(value.get('default', False) for value in load_mesf_values().values()) else next(key for key, value in load_mesf_values().items() if value.get('default', False)),
                        style={'width':'100%'}, 
                        multi=True
                    ),
                    html.Br(),
                    html.Button('Delete MESF Values', id='delete-mesf-values-button', n_clicks=0),
                    html.Div(id='delete-mesf-values-output')
                ])
            ])
        ]),
        id="collapse-card-1",
        is_open=True,
    ),
])
@callback(
    Output('mesf-bead-values-input', 'value'),
    Output('save-mesf-values-output', 'children'),
    Input('save-mesf-values-button', 'n_clicks'),
    State('mesf-bead-values-input', 'value'),
    prevent_initial_call=True
)
def save_mesf_values(n_clicks, mesf_values):
    filename = 'RosettaX/data/settings/saved_mesf_values.json'
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            new_entry = dict(mesf_values=mesf_values, default=True if data == {} else False)
            unique_key = str(int(time.time() * 1000))  # Millisecond precision

            # Add an entry with the unique key
            data[unique_key] = new_entry
        with open(filename, 'w') as file:
            json.dump(data, file)
        return '', f'MESF values "{mesf_values}" saved successfully.'
    except FileNotFoundError:
        # Handle cases where the file doesn't exist yet
        data = {}
        with open(filename, 'w') as file:
            json.dump(data, file)
        return '', 'Error, no file found to update. Recreating file. Try again.'

@callback(
    Output('save-default-mesf-values-output', 'children'),
    Input('save-default-mesf-values-button', 'n_clicks'),
    State('change-default-mesf-values-dropdown', 'value'),
    prevent_initial_call=True
)
def change_default_mesf_values(n_clicks, mesf_values):
    filename = 'RosettaX/data/settings/saved_mesf_values.json'
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            for key in data:
                data[key]['default'] = (key == mesf_values)
            dcc.Store(data=data, id="MESF-default_table-store", storage_type='session')
        with open(filename, 'w') as file:
            json.dump(data, file)
        return f'Default MESF values updated.'
    except FileNotFoundError:
        # Handle cases where the file doesn't exist yet
        data = {}
        with open(filename, 'w') as file:
            json.dump(data, file)
        return 'Error, no file found to update. Recreating file. Try again.'


@callback(
    Output('delete-mesf-values-output', 'children'),
    Input('delete-mesf-values-button', 'n_clicks'),
    State('delete-mesf-values-dropdown', 'value'),
    prevent_initial_call=True
)
def delete_mesf_values(n_clicks, mesf_values):
    filename = 'RosettaX/data/settings/saved_mesf_values.json'
    try:
        deleted_list = []
        with open(filename, 'r') as file:
            data = json.load(file)
            for key in list(data.keys()):
                if key in mesf_values:
                    deleted_list.append(data[key]['mesf_values'])
                    del data[key]
        with open(filename, 'w') as file:
            json.dump(data, file)
        return f'Deleted the following MESF entries: \'{"\', \'".join(deleted_list)}\''
    except FileNotFoundError:
        # Handle cases where the file doesn't exist yet
        data = {}
        with open(filename, 'w') as file:
            json.dump(data, file)
        return 'Error, no file found to update. Recreating file. Try again.'