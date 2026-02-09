import dash
from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc
from RosettaX.pages import styling

class ScatterCalibrationIds:
    """
    Central registry of Dash component ids for the scatter calibration page.

    Use this to keep layout and callbacks consistent and to avoid typos or id collisions.

    Attributes
    ----------
    page_name
        Page identifier used to namespace some ids.
    upload
        Upload component id for the flow cytometry data file.
    flow_file_label
        Output div id showing the uploaded file name.
    flow_type_dropdown
        Dropdown id for selecting flow cytometry type.
    fsc_dropdown
        Dropdown id for selecting the forward scatter channel.
    fsc_wavelength
        Input id for forward scatter wavelength in nm.
    ssc_dropdown
        Dropdown id for selecting the side scatter channel.
    ssc_wavelength
        Input id for side scatter wavelength in nm.
    green_fluorescence_dropdown
        Dropdown id for selecting the green fluorescence channel.
    calibrate_flow_btn
        Button id for starting calibration using the uploaded flow data.

    mie_model
        RadioItems id for selecting Mie model.
    medium_index
        RadioItems id for selecting medium refractive index preset.
    custom_medium_index
        Input id for custom medium refractive index.
    core_index
        Input id for particle core refractive index.
    shell_index
        Input id for particle shell refractive index.
    shell_thickness
        Input id for shell thickness in nm.
    calibrate_example_btn
        Button id for running example parameter calibration.

    run_calibration_btn
        Button id for running scatter calibration.
    export_file_name
        Input id for export file name.
    save_export_btn
        Button id for saving exporting scatter calibration.

    interpolate_method
        Input id for interpolation method.
    interpolate_au
        Input id for AU value to interpolate.
    interpolate_area
        Input id for area value in nm^2 to interpolate.
    interpolate_btn
        Button id for interpolation action.

    graph_1
        Graph id for left plot.
    graph_2
        Graph id for right plot.
    slope_out
        Output div id showing computed slope.
    intercept_out
        Output div id showing computed intercept.

    result_out
        Output div id for status messages from run calibration callback.
    """

    page_name: str = "scatter_calibration"

    upload: str = "upload-data"
    flow_file_label: str = "flow-cytometry-data-file-output"

    flow_type_dropdown: str = "flow-cytometry-data-file-dropdown"

    fsc_dropdown: str = "forward-scatter-dropdown"
    fsc_wavelength: str = "forward-scatter-wavelength-nm"

    ssc_dropdown: str = "side-scatter-dropdown"
    ssc_wavelength: str = "side-scatter-wavelength-nm"

    green_fluorescence_dropdown: str = "green-fluorescence-dropdown"

    calibrate_flow_btn: str = "calibrate-flow-cytometry-button"

    mie_model: str = "mie-model-input"
    medium_index: str = "refractive-index-input"
    custom_medium_index: str = "custom-refractive-index-input"
    core_index: str = "particle-core-refractive-index-input"
    shell_index: str = "particle-shell-refractive-index-input"
    shell_thickness: str = "particle-shell-thickness-input"
    calibrate_example_btn: str = "calibrate-example-button"

    run_calibration_btn: str = "run-calibration-button"
    export_file_name: str = "file-name"
    save_export_btn: str = "save-export-calibration-button"

    interpolate_method: str = "interpolate-input"
    interpolate_au: str = "interpolate-au"
    interpolate_area: str = "interpolate-area"
    interpolate_btn: str = "interpolate-calibration-button"

    graph_1: str = f"graph-1-{page_name}"
    graph_2: str = f"graph-2-{page_name}"
    slope_out: str = "light-scattering-detector-output-slope"
    intercept_out: str = "light-scattering-detector-output-intercept"

    result_out: str = "calibration-result-output"


class ScatterCalibrationPage:
    """
    Dash page for creating and exporting a scatter calibration.

    Responsibilities
    ---------------
    1. Define layout for:
       - selecting uploaded flow cytometry data and channels
       - choosing example Mie calculation parameters
       - exporting and optional interpolation controls
       - graph output placeholders

    2. Register callbacks for page actions.

    Notes
    -----
    The calibration logic here is still placeholder, matching your current code.
    The main value of this refactor is:
    - unique component ids (your original code reused several ids, which will break Dash)
    - consistent layout helpers
    - single source of truth for ids and styles
    """

    def __init__(self) -> None:
        """
        Initialize page configuration, ids, and reusable styles.
        """
        self.ids = ScatterCalibrationIds()

        self.scroll_style = {"maxHeight": "60vh", "overflowY": "auto"}
        self.row_style = {"display": "flex", "alignItems": "center", "gap": "10px", "marginTop": "8px"}
        self.label_style = {"minWidth": "160px"}

    def register(self) -> None:
        """
        Register this file as a Dash page and register callbacks.
        """
        dash.register_page(__name__, path="/scatter_calibration", name="Scatter Calibration")
        self._register_callbacks()

    def layout(self) -> html.Div:
        """
        Build and return the layout for the scatter calibration page.

        Returns
        -------
        dash.html.Div
            Root container for the page.
        """
        ids = self.ids

        return html.Div(
            [
                html.H1("Create and Save A New Scatter Calibration"),
                dbc.Card(
                    [
                        dbc.CardHeader("1. Select Flow Cytometry Data and Parameters"),
                        dbc.Collapse(
                            dbc.CardBody(
                                html.Div(
                                    [
                                        dcc.Upload(
                                            id=ids.upload,
                                            children=html.Div(["Drag and Drop or ", html.A("Select File")]),
                                            style=styling.UPLOAD,
                                            multiple=False,
                                        ),
                                        self._inline_row(
                                            "Flow Cytometry Name:",
                                            html.Div(id=ids.flow_file_label, style={"flex": "1 1 200px"}),
                                            margin_top=False,
                                        ),
                                        self._inline_row(
                                            "Flow Cytometry Type:",
                                            dcc.Dropdown(id=ids.flow_type_dropdown, value=None, style={"width": "250px"}),
                                        ),
                                        self._inline_row(
                                            "Forward Scatter:",
                                            dcc.Dropdown(id=ids.fsc_dropdown, value=None, style={"width": "250px"}),
                                        ),
                                        self._inline_row(
                                            "Wavelength (nm):",
                                            dcc.Input(id=ids.fsc_wavelength, type="number", value="", style={"width": "120px"}),
                                        ),
                                        self._inline_row(
                                            "Side Scatter:",
                                            dcc.Dropdown(id=ids.ssc_dropdown, value=None, style={"width": "250px"}),
                                        ),
                                        self._inline_row(
                                            "Wavelength (nm):",
                                            dcc.Input(id=ids.ssc_wavelength, type="number", value="", style={"width": "120px"}),
                                        ),
                                        self._inline_row(
                                            "Green fluorescence:",
                                            dcc.Dropdown(
                                                id=ids.green_fluorescence_dropdown, value=None, style={"width": "250px"}
                                            ),
                                        ),
                                    ],
                                    style={"display": "flex", "flexDirection": "column", "gap": "6px", **self.scroll_style},
                                )
                            ),
                            id=f"collapse-{ids.page_name}-flow",
                            is_open=True,
                        ),
                    ]
                ),
                html.Br(),
                html.Button("Calibrate", id=ids.calibrate_flow_btn, n_clicks=0),
                html.Br(),
                dbc.Card(
                    [
                        dbc.CardHeader("2. Set Example Calculation Parameters"),
                        dbc.Collapse(
                            dbc.CardBody(
                                html.Div(
                                    [
                                        self._inline_row(
                                            "Mie Model:",
                                            dcc.RadioItems(
                                                ["Solid Sphere", "Core/Shell Sphere"],
                                                "Solid Sphere",
                                                id=ids.mie_model,
                                                inline=True,
                                                labelClassName="me-3",
                                            ),
                                            margin_top=False,
                                        ),
                                        self._inline_row(
                                            "Medium Refractive Index:",
                                            dcc.RadioItems(
                                                ["water", "PBS", "other"],
                                                "water",
                                                id=ids.medium_index,
                                                inline=True,
                                                labelClassName="me-3",
                                            ),
                                        ),
                                        self._inline_row(
                                            "Custom Refractive Index:",
                                            dcc.Input(
                                                id=ids.custom_medium_index,
                                                type="number",
                                                placeholder="Custom Refractive Index",
                                                style={"width": "160px"},
                                            ),
                                        ),
                                        self._inline_row(
                                            "Particle Core Refractive Index:",
                                            dcc.Input(
                                                id=ids.core_index,
                                                type="number",
                                                placeholder="Particle Core Refractive Index",
                                                value=1.38,
                                                min=1.0,
                                                max=2.5,
                                                step=0.001,
                                                style={"width": "160px"},
                                            ),
                                        ),
                                        self._inline_row(
                                            "Particle Shell Refractive Index:",
                                            dcc.Input(
                                                id=ids.shell_index,
                                                type="number",
                                                placeholder="Particle Shell Refractive Index",
                                                value=1.48,
                                                min=1.0,
                                                max=2.5,
                                                step=0.001,
                                                style={"width": "160px"},
                                            ),
                                        ),
                                        self._inline_row(
                                            "Particle Shell Thickness (nm):",
                                            dcc.Input(
                                                id=ids.shell_thickness,
                                                type="number",
                                                placeholder="Particle Shell Thickness (nm)",
                                                value=6,
                                                min=0,
                                                step=1,
                                                style={"width": "120px"},
                                            ),
                                        ),
                                        html.Button("Calibrate", id=ids.calibrate_example_btn, n_clicks=0, style={"marginTop": "8px"}),
                                    ]
                                ),
                                style=self.scroll_style,
                            ),
                            id=f"collapse-{ids.page_name}-example",
                            is_open=True,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Card(
                    [
                        dbc.CardHeader("3. Export Size Calibration"),
                        dbc.Collapse(
                            dbc.CardBody(
                                html.Div(
                                    [
                                        html.Button("Run Scatter Calibration", id=ids.run_calibration_btn, n_clicks=0),
                                        dcc.Input(id=ids.export_file_name, type="text", placeholder="Enter file name", style={"width": "200px"}),
                                        html.Button("Save/Export Scatter Calibration", id=ids.save_export_btn, n_clicks=0),
                                        html.Br(),
                                        html.Br(),
                                        html.Div("Interpolate (optional):"),
                                        dcc.Input(
                                            id=ids.interpolate_method,
                                            type="text",
                                            placeholder="Enter interpolation method",
                                            style={"width": "200px"},
                                        ),
                                        dcc.Input(id=ids.interpolate_au, type="number", placeholder="Enter AU value", style={"width": "200px"}),
                                        dcc.Input(
                                            id=ids.interpolate_area,
                                            type="number",
                                            placeholder="Enter area value nm^2",
                                            style={"width": "200px"},
                                        ),
                                        html.Button("Interpolate Calibration", id=ids.interpolate_btn, n_clicks=0),
                                        html.Br(),
                                        html.Br(),
                                        html.Div(id=ids.result_out),
                                    ],
                                    style={"display": "flex", "flexDirection": "column", "gap": "6px", **self.scroll_style},
                                )
                            ),
                            id=f"collapse-{ids.page_name}-export",
                            is_open=True,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Collapse(
                    dbc.Card(
                        [
                            dbc.CardHeader("4. Graph Output"),
                            dbc.CardBody(
                                html.Div(
                                    [
                                        html.Div(
                                            dcc.Graph(id=ids.graph_1),
                                            style={"display": "inline-block", "height": "90%", "width": "20%"},
                                        ),
                                        html.Div(
                                            dcc.Graph(id=ids.graph_2),
                                            style={"display": "inline-block", "height": "90%", "width": "80%"},
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [html.Div(["Calculated Slope:"]), html.Div("", id=ids.slope_out)],
                                                    style={"display": "flex", "alignItems": "center", "gap": "5px"},
                                                ),
                                                html.Div(
                                                    [html.Div(["Calculated Intercept:"]), html.Div("", id=ids.intercept_out)],
                                                    style={"display": "flex", "alignItems": "center", "gap": "5px"},
                                                ),
                                            ]
                                        ),
                                    ],
                                    style={"width": "100%", "height": "100%", "display": "inline-block"},
                                ),
                                style={"height": "100%", "overflowY": "auto"},
                            ),
                        ],
                        style={"height": "70vh", "overflowY": "auto"},
                    ),
                    id=f"collapse-{ids.page_name}-graphs",
                    is_open=True,
                ),
            ]
        )

    def _inline_row(self, label: str, control, *, margin_top: bool = True) -> html.Div:
        """
        Create a label control row with consistent spacing.

        Parameters
        ----------
        label
            Text label shown on the left side.
        control
            Dash component shown on the right side.
        margin_top
            If True, apply a top margin for vertical spacing.

        Returns
        -------
        dash.html.Div
            Row container with label and control.
        """
        style = dict(self.row_style)
        if not margin_top:
            style.pop("marginTop", None)

        return html.Div([html.Div([label], style=self.label_style), control], style=style)

    def _register_callbacks(self) -> None:
        """
        Register callbacks for this page.

        Current callbacks are placeholders that mirror your original file.
        """
        ids = self.ids

        @callback(
            Output(ids.result_out, "children"),
            Input(ids.run_calibration_btn, "n_clicks"),
            Input(ids.export_file_name, "value"),
            prevent_initial_call=False,
        )
        def run_scatter_calibration(n_clicks: int, file_name: str) -> str:
            """
            Placeholder callback to simulate running scatter calibration.

            Parameters
            ----------
            n_clicks
                Number of times the run calibration button was clicked.
            file_name
                Export file name entered by the user.

            Returns
            -------
            str
                Status message reflecting the triggered action.
            """
            if n_clicks and n_clicks > 0:
                name = (file_name or "").strip() or "<no file name>"
                return f"Scatter Calibration run {n_clicks} times with file name {name}."
            return ""


_page = ScatterCalibrationPage()
_page.register()
layout = _page.layout()